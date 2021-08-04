"""Definition for the class that runs the optimization routine.

We describe the policy for starting new runs by implementing a
`Colmena <http://colmena.rtfd.org/>`_ Thinker class.
"""
import random
from pathlib import Path
from typing import Dict, Callable, Union

import requests
from colmena.redis.queue import ClientQueues, TaskServerQueues
from colmena.task_server import ParslTaskServer
from colmena.thinker import BaseThinker, result_processor
from colmena.models import Result
from parsl import Config, ThreadPoolExecutor
from pydantic import BaseModel, Field, AnyHttpUrl

from polybot.models import SampleTemplate
from polybot.robot import send_new_sample


class OptimizationProblem(BaseModel):
    """Define the optimization problem and any settings for the planning algorithm."""

    # Define the search space
    search_template_path: Union[AnyHttpUrl, Path] = Field(
        ..., description="Path to the sample template. Defines the input variables and the search space"
                         " for the optimization. Can be either a path on the local filesystem or a HTTP URL")

    # Options the planning algorithm
    planner_options: Dict = Field(default_factory=dict, description='Any options for the planning algorithm')

    # Define the optimization metric
    # TODO (wardlt): Should we dare cross into multi-objective optimization in this document or leave it up to
    #    the implementation of the Planner?
    output: str = Field(..., description="Output variable. Name of values within the `processed_outputs` dictionary")
    maximize: bool = Field(True, description="Whether to maximize (or minimize) the target function")

    @property
    def search_template(self) -> SampleTemplate:
        """Template that defines the sample search space"""
        if isinstance(self.search_template_path, str):
            # Download it to disk
            reply = requests.get(self.search_template_path)
            return SampleTemplate.parse_obj(reply.json())
        else:
            return SampleTemplate.parse_file(self.search_template_path)

    class Config:
        extras = 'forbid'


class BasePlanner(BaseThinker):
    """Base class for planning algorithms based on the `Colmena BaseThinker
    <https://colmena.readthedocs.io/en/latest/how-to.html#creating-a-thinker-application>`_ class.

    Subclasses should provide the optimization specification to the initializer of this class
    so that it is available as the `opt_spec` attribute. Additional options to the planner
    should be set using keyword arguments to the initializer, so that we can define them in the
    :class:`OptimizationProblem` JSON document.

    There are no requirements on how you implement the planning algorithm, but you may at least want an agent
    waiting for results with the "robot" topic. For example,

    .. code: python

        @result_processor(topic='robot')
        def robot_result_handler(self, _: Result):
            output = self.opt_spec.get_sample_template()
            send_send_new_sample(output)

    """

    def __init__(self, queues: ClientQueues, opt_spec: OptimizationProblem, daemon: bool = False):
        super().__init__(queues, daemon=daemon)
        self.opt_spec = opt_spec


class RandomPlanner(BasePlanner):
    """Submit a randomly-selected point from the search space each time a new result is completed"""

    @result_processor(topic='robot')
    def robot_result_handler(self, _: Result):
        """Generate a new task to be run on the robot after one completes

        Args:
            _: Result that is not actually used for now.
        """
        # Make a choice for each variable
        output = self.opt_spec.search_template.create_new_sample()
        for key, acceptable_values in self.opt_spec.search_template.list_acceptable_input_values().items():
            output.inputs[key] = random.choice(acceptable_values)

        # Send it to the robot
        send_new_sample(output)
        return


def _execute(f: Callable):
    """Debug function"""
    return f()


def build_thread_pool_executor(queues: TaskServerQueues) -> ParslTaskServer:
    """Builds a task server that runs a single task on a local thread.

    This server is primarily meant for testing, and has a single task,
    "execute," that receives a Callable and executes it remotely.

    Args:
        queues: Queues to use to communicate
    Returns:
        A configured task server
    """

    config = Config(executors=[ThreadPoolExecutor(max_threads=1)])
    return ParslTaskServer(
        queues=queues,
        methods=[_execute],
        config=config
    )
