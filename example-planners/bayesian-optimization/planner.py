from datetime import datetime
from pathlib import Path
from typing import Tuple
import pickle as pkl
import logging
import sys

import numpy as np
from colmena.models import Result
from colmena.redis.queue import ClientQueues
from colmena.thinker import result_processor
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process import GaussianProcessRegressor, kernels
from sklearn.model_selection import RepeatedKFold, cross_validate
from modAL.acquisition import EI

from polybot.robot import send_new_sample
from polybot.sample import load_samples
from polybot.planning import BasePlanner, OptimizationProblem


def run_inference(gpr: GaussianProcessRegressor, search_x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Run inference on a machine learning model

    Args:
        gpr: Gaussian process regression model
        search_x: Search space to be evalauted
    Returns:
        - Mean of the predictions
        - Standard deviation of the predictions
    """
    return gpr.predict(search_x, return_std=True)


class BOPlanner(BasePlanner):
    """Use Bayesian optimization to select the next experiment"""

    def __init__(self, queues: ClientQueues, opt_spec: OptimizationProblem, daemon: bool = False):
        super().__init__(queues, opt_spec, daemon=daemon)

        # Make a storage directory
        self.output_dir = Path.cwd() / 'runs' / f'{datetime.now().strftime("%d%b%y-%H%M%S")}'
        self.output_dir.mkdir(parents=True, exist_ok=False)

        # Keep track of the iteration number
        self.iteration = 0

        # Save the optimization specification
        with self.output_dir.joinpath('opt_spec.json').open('w') as fp:
            print(opt_spec.json(indent=2), file=fp)

        # Set up the logging
        handlers = [logging.FileHandler(self.output_dir / 'runtime.log'),
                    logging.StreamHandler(sys.stdout)]

        class ParslFilter(logging.Filter):
            """Filter out Parsl debug logs"""

            def filter(self, record):
                return not (record.levelno == logging.DEBUG and '/parsl/' in record.pathname)

        for h in handlers:
            h.addFilter(ParslFilter())

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG, handlers=handlers)

    @result_processor(topic='robot')
    def robot_result_handler(self, _: Result):
        # Make the output directory for results
        out_dir = self.output_dir / f'iteration-{self.iteration}'
        out_dir.mkdir()

        # Increment the iteration number
        self.iteration += 1

        # Get the training data
        train_x, train_y = self.generate_training_set()
        self.logger.info(f'Loaded a training set of {len(train_x)} entries')

        # Log-normalize conductivity
        train_y = np.log(train_y)

        # Fit a model and save the training records
        model = self._fit_model(train_x, train_y, out_dir)

        # Create the search space
        possible_options = self.opt_spec.search_template.generate_search_space_dataframe()
        search_x = possible_options[self.opt_spec.search_template.input_columns]
        self.logger.info(f'Created {len(search_x)} samples to be evaluated')

        # Send it to be evaluated remotely
        chunk_size = self.opt_spec.planner_options.get('chunk_size')
        chunk_start = 0
        n_chunks = 0
        for i, chunk in enumerate(np.array_split(search_x, len(search_x) // chunk_size)):
            self.queues.send_inputs(model, chunk,
                                    method='run_inference', topic='compute',  # Define what to run
                                    task_info={'chunk_start': chunk_start},  # Maintain how to map to search space
                                    keep_inputs=False)  # Optimization: Do not send search space or model back
            chunk_start += len(chunk)
            n_chunks += 1
        self.logger.info(f'Sent all {n_chunks} inference tasks')

        # Prepare to be able to store the data
        search_y = np.empty((len(search_x),))
        search_std = np.empty((len(search_y),))
        for i in range(n_chunks):
            result = self.queues.get_result(topic='compute')  # Get the result
            if not result.success:
                raise ValueError(f'Inference task failed.\n{result.task_info["exception"]}')

            # Store the result
            chunk_start = result.task_info['chunk_start']
            chunk_y, chunk_std = result.value
            search_y[chunk_start:(chunk_start + len(chunk_y))] = chunk_y
            search_std[chunk_start:(chunk_start + len(chunk_y))] = chunk_std
            self.logger.info(f'Recorded inference task {i+1}/{n_chunks}. Starting point: {chunk_start}')

        # Get the largest UCB
        assert self.opt_spec.maximize, "The optimization requests minimization"
        ei = EI(search_y, search_std, max_val=np.max(train_y), tradeoff=0.1)
        best_ind = np.argmax(ei)
        best_point = search_x.iloc[best_ind][self.opt_spec.search_template.input_columns]

        # Make the sample and send it out
        output = self.opt_spec.search_template.create_new_sample()
        for p, x in zip(self.opt_spec.search_template.input_columns, best_point):
            output.inputs[p] = x
        self.logger.info('Sending a new sample to the robot')
        send_new_sample(output)
        with out_dir.joinpath('selected_sample.json').open('w') as fp:
            print(output.json(indent=2), file=fp)

    def _fit_model(self, train_x: np.ndarray, train_y: np.ndarray, out_dir: Path) -> Pipeline:
        """Fit and test a model using the latest data

        Args:
            train_x: Input columns
            train_y: Output column
            out_dir: Location to store the data
        """
        # Create an initial RBF kernel, using the training set mean as a scaling parameter
        kernel = train_y.mean() ** 2 * kernels.RBF(length_scale=1)

        # TODO (wardlt): Make it clear where featurization would appear, as we are soon to introduce additives
        #  This will yield chemical degrees of freedom better captured using features of the additives rather
        #  than a new variable per additive
        #  Notes for now: Mol. Weight, Side Chain Length, and ... are the likely candidates

        # Add a noise parameter based on user settings
        noise = self.opt_spec.planner_options.get('noise_level', 0)
        self.logger.debug(f'Using a noise level of {noise}')
        if noise < 0:
            # Use standard deviation of the distribution of train_y will be the estimation of initial noise
            # TODO (wardlt): Document where 3, 4, and 11 come from
            noise_estimated = np.std(train_y) / 3
            noise_lb = noise_estimated / 4
            noise_ub = noise_estimated * 11

            kernel_noise = kernels.WhiteKernel(noise_level=noise_estimated ** 2,
                                               noise_level_bounds=(noise_lb ** 2, noise_ub ** 2))
            kernel = kernel + kernel_noise
        elif noise > 0:
            kernel = kernel + kernels.WhiteKernel(noise ** 2, noise_level_bounds=(noise ** 2,) * 2)

        # Train a GPR model
        self.logger.debug('Starting kernel')
        model = Pipeline([
            ('variance', VarianceThreshold()),
            ('scale', StandardScaler()),
            ('gpr', GaussianProcessRegressor(kernel))
        ])

        # Perform k-Fold cross-validation to estimate model performance
        if len(train_x) > 5:
            cv_results = cross_validate(model, train_x, train_y, cv=RepeatedKFold(), return_train_score=True,
                                        scoring='neg_mean_squared_error')
            with out_dir.joinpath('cross-val-results.pkl').open('wb') as fp:
                pkl.dump(cv_results, fp)
            self.logger.info('Performed cross-validation.'
                             f' RMSE: {np.sqrt(-1 * np.mean(cv_results["train_score"])):.2e}')
        else:
            self.logger.info('Insufficient data for cross-validation')

        # Train and save the model
        model.fit(train_x, train_y)
        self.logger.info(f'Finished fitting the model on {len(train_x)} data points')
        self.logger.info(f'Optimized model: {model["gpr"].kernel_}')
        with out_dir.joinpath('model.pkl').open('wb') as fp:
            pkl.dump(model, fp)
        return model

    def generate_training_set(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load in all of the previous samples to build a training set

        Uses the inputs and outputs defined in the optimization specification

        Returns:
            - Input features
            - Output variable
        """

        # Get the name of the input columns
        input_columns = self.opt_spec.search_template.input_columns

        train_x = []
        train_y = []
        # Loop over samples in the training data
        for sample in load_samples():
            train_x.append([sample.inputs[i] for i in input_columns])  # Get only the needed input columns
            train_y.append(sample.processed_output[self.opt_spec.output])  # Get the target output column

        # Convert them to numpy and return
        return np.array(train_x), np.array(train_y)
