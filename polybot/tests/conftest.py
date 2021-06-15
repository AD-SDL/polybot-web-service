from pathlib import Path
from shutil import rmtree
from subprocess import Popen
from time import sleep

from pytest import fixture
from fastapi.testclient import TestClient

from polybot.fastapi import app
from polybot.models import Sample
from polybot.config import settings

sample_path = str(Path(__file__).parent / 'files' / 'example-sample.json')
_test_dir = Path(__file__).parent


@fixture(autouse=True)
def test_settings():
    # Redirect the sample folder
    sample_dir = _test_dir / "test-samples"
    if sample_dir.is_dir():
        rmtree(sample_dir)
    sample_dir.mkdir()
    settings.sample_folder = sample_dir

    # Set up the test Redis service
    settings.redis_url = "rediss://localhost"


@fixture()
def fake_robot():
    settings.robot_url = "http://localhost:8152/"
    proc = Popen(['uvicorn', '--port', '8152', '--app-dir', _test_dir, 'fake_robot:app'])
    sleep(1)
    assert proc.poll() is None, "Uvicorn process died"
    yield proc
    proc.kill()


@fixture()
def example_sample() -> Sample:
    return Sample.parse_file(sample_path)


@fixture()
def fastapi_client() -> TestClient:
    return TestClient(app)
