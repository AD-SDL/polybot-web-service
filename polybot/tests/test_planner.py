"""Make sure the planning system works"""
import json
import logging
from time import sleep

from colmena.models import Result
from pytest import fixture
from pytest_mock import MockerFixture

from polybot.models import SampleTemplate
from polybot.planning import OptimizationProblem, RandomPlanner
from polybot.config import settings

from conftest import file_path


@fixture
def opt_config() -> OptimizationProblem:
    """Sample configuration for the optimization problem"""
    return OptimizationProblem(
        search_template_path=file_path / "example-template.json",
        output='processed_outputs.conductivity'
    )


def test_get_sample_from_url(mocker: MockerFixture):
    class _FakeResult:
        def json(self):
            with open(file_path / "example-template.json") as fp:
                return json.load(fp)

    mocker.patch('polybot.planning.requests.get', new=lambda x: _FakeResult())
    opt = OptimizationProblem(search_template_path='http://fake.com/path', output='fake')
    assert isinstance(opt.search_template, SampleTemplate)


def test_generate(mocker: MockerFixture, opt_config, example_sample, caplog):
    # Mock the send_new_sample in the planning library
    fake_robot = mocker.patch('polybot.planning.send_new_sample')

    # Make the planner
    client_q = settings.make_client_queue()
    server_q = settings.make_server_queue()
    planner = RandomPlanner(client_q, opt_config, daemon=True)

    # Launch it as a Thread
    planner.start()
    try:
        # Test sending in a new result directly via Redis
        server_q.send_result(Result(((0,), {})), topic='robot')
        sleep(1)  # For the other thread to catch up

        # Make sure the server responded by sending a record to the "robot"
        assert fake_robot.call_count == 1, planner.is_alive()
    finally:
        # Kill the planning service
        planner.done.set()
