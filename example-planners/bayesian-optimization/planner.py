from typing import Tuple

import numpy as np
from colmena.models import Result
from colmena.thinker import result_processor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.gaussian_process import GaussianProcessRegressor, kernels

from polybot.robot import send_new_sample
from polybot.sample import load_samples
from polybot.planning import BasePlanner


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

    @result_processor(topic='robot')
    def robot_result_handler(self, _: Result):
        # Get the training data
        train_x, train_y = self.generate_training_set()
        self.logger.info(f'Loaded a training set of {len(train_x)} entries')

        # Train a GPR model
        model = Pipeline([
            ('scale', MinMaxScaler()),
            ('gpr', GaussianProcessRegressor(kernels.ConstantKernel() * kernels.RBF() + kernels.ConstantKernel()))
        ])
        model.fit(train_x, train_y)
        self.logger.info(f'Finished fitting the model on {len(train_x)} data points')

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
            self.logger.info(f'Recorded inference task {i}/{n_chunks}. Starting point: {chunk_start}')

        # Get the largest UCB
        assert self.opt_spec.maximize, "The optimization requests minimization"
        ucb = search_y + self.opt_spec.planner_options.get('beta', 1) * search_std
        best_ind = np.argmax(ucb)
        best_point = search_x.iloc[best_ind][self.opt_spec.search_template.input_columns]

        # Make the sample and send it out
        output = self.opt_spec.search_template.create_new_sample()
        for p, x in zip(self.opt_spec.search_template.input_columns, best_point):
            output.inputs[p] = x
        self.logger.info(f'Sending a new sample to the robot')
        send_new_sample(output)

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
