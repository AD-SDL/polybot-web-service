# Polybot

[![Python package](https://github.com/AD-SDL/polybot-web-service/actions/workflows/python-package.yml/badge.svg)](https://github.com/AD-SDL/polybot-web-service/actions/workflows/python-package.yml)
[![Coverage Status](https://coveralls.io/repos/github/AD-SDL/polybot-web-service/badge.svg?branch=master)](https://coveralls.io/github/AD-SDL/polybot-web-service?branch=master)

A server for controlling the robot synthesis of thin-film polymeric materials.

## Installation

We describe our full environment using an Anaconda environment file,
[`environment.yml`](./environment.yml).
Install it by calling:

`conda env create --file environment.yml`

The package requirements are also listed in [`requirements.txt`](./requirements.txt),
which you can use to build the environment using `pip`:

`pip install -e .`

## Running Polybot

The web service is built from three smaller services.

- Redis: Launch Redis as normal: `redis-server`
- AI planner: Launch using the CLI: `polybot planner opt_spec.json`

### Configuring PolyBot

Configure the web service and planner using environment variables, which can be stored in the `.env` file in the run directory.
Key variables include:

- `ROBOT_URL`: URL of the Robot Scheduler
- `REDIS_URL`: URL of the Redis queue
- `LOG_NAME`: Name of the log file

Full options are in [`polybot/config.py`](./polybot/config.py).

An "optimization specification" JSON file (note `opt_spec.json` above) provides additional details to the AI planning algorithm.
The specification includes the names of input variables and a path to a template workflow.
The `OptimizationProblem` specification in [`polybot/planning.py`](./polybot/planning.py) includes the full details.

## Example Planning Agents

The [example-planners](./example-planners) directory includes a few different planning algorithms used by the PolyBot project.+

## Designing Planning Algorithms

The default AI planning algorithm randomly selects a new experiment from the search space once a previous experiment completes,
but there is significant flexibility to write more complex algorithms.
Define a new planning algorithm by implementing a new `BasePlanner` and supplying a path to that file when launching polybot.
For example, use a planning class named `BOPlanner` stored in a python file named `planner.py` by calling

```bash
polybot planner --planning-class planner:BOPlanner
```

Polybot uses [Colmena](http://colmena.rtfd.org/) to express planning algorithms.
Follow our guide to creating a ["Thinker"](https://colmena.readthedocs.io/en/latest/how-to.html#creating-a-thinker-application)
to defines the logic for controlling the robot.
`BasePlanner` is a subclass of the Colmena `BaseThinker` class.
We briefly describe a few common tasks and how to implement them.

#### Responding to Data from Robot

We access results from the robot by subscribing "study events" from the Argonne Data Cloud (ADC).
The ADC provides a service where one can be sent messages about when a sample is created via web sockets.
Use this feature by first setting the ID for your study as the `ADC_STUDY_ID` environment variable and
then using the `subscribe_to_study` function provided with this library.

A template "Thinker" application that uses these functions would be

```python
from colmena.thinker import agent

from polybot.planning import BasePlanner
from polybot.sample import subscribe_to_study
from polybot.robot import send_new_sample

class RobotPlanner(BasePlanner):

    @agent()
    def make_tasks(self):
        """This function will run as a thread when you start the planner"""
        for sample in subscribe_to_study():
            new_sample = ...  # Logic to be defined by you!
            send_new_sample(new_sample)
```

Note how we receive a new sample from the [`subscribe_to_study`](./polybot/sample.py) function
and then send a new task to the robot using the 
[`polybot.robot.send_new_sample`](./polybot/robot.py) function.

#### Performing Computations on Remote Resources

The event-driven system for defining how to respond to robot commands handles executing computations on remote resources.

The first step is to create a ["task server"](https://colmena.readthedocs.io/en/latest/how-to.html#configuring-a-task-server)
that defines a list of methods which can be run remotely and the resources on which they can execute.
Create a function that takes a queue object as inputs and then returns a fully defined task server.
For example, a task server that runs `f(x) = x + 1` on LCRC Bebop would be:

```python
from parsl.config import Config
from parsl.providers import SlurmProvider
from parsl.executors import HighThroughputExecutor
from colmena.redis.queue import TaskServerQueues
from colmena.task_server import ParslTaskServer

# Define the workflow configuration
config = Config(
    executors=[
        HighThroughputExecutor(
            label='compute',
            prefetch_capacity=0,
            provider=SlurmProvider(
                partition='bdwall',
                init_blocks=0,
                max_blocks=1,
                nodes_per_block=1,
                walltime='48:00:00',
                scheduler_options="#SBATCH --account=sdl"
            )
        )
    ]
)


def f(x: float) -> float:
    return x

def make_task_server(queues: TaskServerQueues) -> ParslTaskServer:
    """Make a task server that serves "f"
    
    Args:
        queues: Queues defining how to communicate tasks with Redis
    """
    
    return ParslTaskServer(
        queues=queues,  # Gives access to the Redis server 
        methods=[(f, {'executors': ['compute']})],  # Defines the methods and where they would run
        config=config  # Provides the compute layout
    )


```

By default, the Redis queues have a "compute" topic used for compute tasks. 
You can add more by setting the "TASK_QUEUES" environment variable with a list of names.

Use the "compute" topic for sending asynchronous task requests.
For example, a simple "send then receive" pattern would look like:

```python

@agent
def sim_worker()
    self.queues.send_inputs(1., topic='compute', method='f')
    result = self.queues.get_result(topic='compute')
    do_something_with_that_knowledge(result.value)
```
