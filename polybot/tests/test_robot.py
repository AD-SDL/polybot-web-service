from time import sleep
from pathlib import Path
from subprocess import Popen, STDOUT

from pytest import fixture

from polybot.config import settings
from polybot.models import Sample
from polybot.robot import send_new_sample

_test_dir = Path(__file__).parent
_test_sample = str(Path(__file__).parent / 'files' / 'example-sample.json')


@fixture(autouse=True)
def fake_robot():
    settings.robot_url = "http://localhost:8152/"
    with open('fake-robot.log', 'w') as fp:
        proc = Popen(['uvicorn', '--port', '8152', '--app-dir', _test_dir, 'fake_robot:app'],
                     stdout=fp, stderr=STDOUT)
        sleep(1)
        yield proc
    proc.kill()


def test_submit():
    sample = Sample.parse_file(_test_sample)
    send_new_sample(sample)