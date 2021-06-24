"""Make sure the planning system works"""
import logging
from time import sleep

from colmena.models import Result
from pytest import fixture

from polybot.planning import OptimizationProblem, RandomPlanner
from polybot.config import settings

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


def test_generate(fake_robot, opt_config, fastapi_client, example_sample, caplog):
    # Make the planner
    client_q = settings.make_client_queue()
    server_q = settings.make_server_queue()
    planner = RandomPlanner(client_q, opt_config)

    # Launch it as a Thread
    planner.start()
    try:
        # Test sending in a new result
        with caplog.at_level(logging.INFO):
            server_q.send_result(Result(((0,), {})), topic='robot')
            sleep(1)  # For the other thread to catch up

        # Make sure the server responded by sending a record to the "robot"
        assert any("Sending" in i.message for i in caplog.records[-5:])

        # Test sending via the REST API
        caplog.clear()
        with caplog.at_level(logging.INFO):
            res = fastapi_client.post("/ingest", json=example_sample.dict(), allow_redirects=True)
            assert res.status_code == 200
            sleep(2)  # Multiple threads have to complete

        # Make sure the server responded by sending a record to the "robot"
        assert any("Sending" in i.message for i in caplog.records[-5:])
    finally:
        # Kill the planning service
        planner.done.set()
