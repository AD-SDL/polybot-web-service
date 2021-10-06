from datetime import datetime
from pathlib import Path
from typing import Tuple
import logging
import sys

import numpy as np
from colmena.redis.queue import ClientQueues
from colmena.thinker import agent
from sklearn.gaussian_process import GaussianProcessRegressor

from polybot.config import settings
from polybot.robot import send_new_sample
from polybot.sample import load_samples, subscribe_to_study
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

    @agent(critical=False)
    def startup(self):
        """A thread that just performs a standard"""
        if self.opt_spec.planner_options.get('cold_start', True):
            self.logger.info('Performing a cold-start')
            self.launch_flow()

    @agent()
    def robot_result_handler(self):
        """Launches a new planning task whenever the robot finishes a simulation"""
        for sample in subscribe_to_study():
            self.launch_flow()

    def launch_flow(self):
        """Launch a Globus flow that will generate the next task"""

        # Get the inputs needed for the low
        training_set = [x.json() for x in load_samples()]  # The training set for the algorithm, stored as JSON strings
        self.logger.info(f'Gathered {len(training_set)} training examples')
        run_configuration = self.opt_spec.planner_options.copy()  # Any configuration options for the task

        # Create a new job
        client = settings.generate_adc_client()
        # TODO (wardlt): Not sure what to use for sample and investigation IDs.
        #  - Do we need a sample to start a Job?
        #  - I can make an investigation and add it to the "settings" for the run
        job_id = client.create_job('invest_id', 'sample_id', datetime.now())
        self.logger.info(f'Created a job in the ADC: {job_id}')

        # Call flow
        #  flow_client.run_flow(inputs={'training_set': training_set, 'settings': run_configuration}) ...
        self.logger.info('Submitted job to Globus Flows: {flow_id}')

        # Wait until the job finishes
        for event in client.subscribe_to_job(job_id):
            # Not sure what these events are
            break

        send_new_sample(None)  # TODO (wardlt): Unpack the sample from the output of the job
