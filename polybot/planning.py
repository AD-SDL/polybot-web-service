"""Definition for the class that runs the optimization routine.

We describe the policy for starting new runs by implementing a
`Colmena <http://colmena.rtfd.org/>`_ Thinker class.
"""
from pathlib import Path
from typing import List, Tuple

from colmena.redis.queue import ClientQueues
from colmena.thinker import BaseThinker, result_processor
from colmena.models import Result
from pydantic import BaseModel, Field
import numpy as np

from polybot.models import Sample
from polybot.robot import send_new_sample


class OptimizationProblem(BaseModel):
    """Define the optimization problem"""

    # Define the search space
    example_sample: Path = Field(..., description="Path to an example sample")
    # TODO (wardlt): Make inputs a List of Lists to specify nested dictionaries?
    inputs: List[str] = Field(..., description="List of input fields that are resolved against sample documents. "
                                               "Names of values in the `inputs` dictionary of a sample.")
    search_space: List[Tuple[float, float]] = Field(..., description="Ranges of the variables to be optimized. "
                                                                     "In the same order as inputs")
    points_per_axis: int = Field(32, description="Number of levels per input variable. Used during optimization", ge=2)

    # Define the optimization metric
    output: str = Field(..., description="Output variable. Name of values within the `processed_outputs` dictionary")
    maximize: bool = Field(True, description="Whether to maximize (or minimize) the target function")

    def get_sample_template(self) -> Sample:
        """Get an template for a new sample

        Returns:
            A new sample instance
        """
        new = Sample.parse_file(self.example_sample)
        new.reset_id()
        return new


class Planner(BaseThinker):
    """Class that manages the experiments and computations performed by the PolyBot System"""

    def __init__(self, queues: ClientQueues, opt_spec: OptimizationProblem):
        super().__init__(queues)
        self.opt_spec = opt_spec

    @result_processor(topic='robot')
    def robot_result_handler(self, _: Result):
        """Generate a new task to be run on the robot after one completes

        Args:
            _: Result that is not actually used for now.
        """

        # Make a choice for each variable
        output = self.opt_spec.get_sample_template()
        for path, (low, high) in zip(self.opt_spec.inputs, self.opt_spec.search_space):
            choices = np.linspace(low, high, self.opt_spec.points_per_axis)
            choice = np.random.choice(choices)
            output.inputs[path] = choice

        # Send it to the robot
        send_new_sample(output)
        return
