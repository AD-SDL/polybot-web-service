"""Use local compute for the Parsl executor"""
from colmena.redis.queue import TaskServerQueues
from colmena.task_server import ParslTaskServer
from parsl import Config, ThreadPoolExecutor

from planner import run_inference

config = Config(
    executors=[ThreadPoolExecutor(max_threads=1)]
)


def make_task_server(queues: TaskServerQueues) -> ParslTaskServer:
    """Make the task server

    Has a single method: run_inference

    Args:
        queues: Queues to be used. Expects a single compute queue, named "compute"
    Returns:
        Initialized task server
    """
    return ParslTaskServer(
        queues=queues,
        methods=[run_inference],
        config=config
    )
