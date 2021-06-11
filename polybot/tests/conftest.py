from pathlib import Path
from subprocess import Popen
from time import sleep

from pytest import fixture

from polybot.models import Sample
from polybot.config import settings

_test_sample = str(Path(__file__).parent / 'files' / 'example-sample.json')
_test_dir = Path(__file__).parent


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
    return Sample.parse_file(_test_sample)
