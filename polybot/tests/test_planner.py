"""Make sure the planning system works"""
import logging
from time import sleep
from typing import Tuple

from colmena.models import Result
from colmena.redis.queue import ClientQueues, MethodServerQueues, make_queue_pairs
from pytest import fixture

from polybot.planning import OptimizationProblem, Planner

from conftest import sample_path


@fixture
def opt_config() -> OptimizationProblem:
    """Sample configuration for the optimization problem"""
    return OptimizationProblem(
        example_sample=sample_path,
        inputs=['inputs.1'],
        search_space=[(25, 45)],
        output='processed_outputs.conductivity'
    )


@fixture
def queues() -> Tuple[ClientQueues, MethodServerQueues]:
    """Queues used to communicate results to Colmena"""
    return make_queue_pairs('localhost', topics=['robot'])


def test_generate(fake_robot, opt_config, queues, caplog):
    # Make the planner
    client_q, server_q = queues
    planner = Planner(client_q, opt_config)

    # Launch it as a Thread
    planner.start()
    try:
        # Test sending in a new result
        with caplog.at_level(logging.INFO):
            server_q.send_result(Result(((0,), {})), topic='robot')
            sleep(1)  # For the other thread to catch up

        # Make sure the server responded by sending a record to the "robot"
        assert any("Sending" in i.message for i in caplog.records[-5:])
    finally:
        # Kill the planning service
        planner.done.set()