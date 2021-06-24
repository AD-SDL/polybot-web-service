from itertools import product

import numpy as np
from colmena.models import Result
from colmena.thinker import result_processor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.gaussian_process import GaussianProcessRegressor, kernels

from polybot.robot import send_new_sample
from polybot.sample import load_samples
from polybot.planning import BasePlanner


class BOPlanner(BasePlanner):
    """Use Bayesian optimization to select the next experiment"""

    @result_processor(topic='robot')
    def robot_result_handler(self, _: Result):
        # Load in all of the previous samples to build a training set
        #  Use the inputs and outputs defined in the optimization specification
        train_x = []
        train_y = []
        for sample in load_samples():
            train_x.append([sample.inputs[i] for i in self.opt_spec.inputs])
            train_y.append(sample.processed_output[self.opt_spec.output])

        # Train a GPR model
        model = Pipeline([
            ('scale', MinMaxScaler()),
            ('gpr', GaussianProcessRegressor(kernels.ConstantKernel() * kernels.RBF() + kernels.ConstantKernel()))
        ])
        model.fit(train_x, train_y)

        # Evaluate over the search space
        levels = [
            np.linspace(lower, upper, self.opt_spec.points_per_axis)
            for lower, upper in self.opt_spec.search_space
        ]
        search_x = np.array(list(product(levels)))
        search_y, search_std = model.predict(search_x, return_std=True)

        # Get the largest EI
        assert self.opt_spec.maximize, "The optimization requests minimization"
        ei = search_y + self.opt_spec.planner_options.get('beta', 1) * search_std
        best_ind = np.argmax(ei)
        best_point = search_x[best_ind, :]

        # Make the sample and send it out
        output = self.opt_spec.get_sample_template()
        for p, x in zip(self.opt_spec.inputs, best_point):
            output.inputs[p] = x
        send_new_sample(output)
