from pathlib import Path

from pytest import raises

from polybot.cli import main
from polybot.version import __version__

_test_sample = str(Path(__file__).parent / 'files' / 'example-sample.json')


def test_version(fake_robot, capsys):
    main(['version'])
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_upload(fake_robot):
    main(['upload', '--dry-run', _test_sample])
    main(['upload', _test_sample])


def test_planner():
    main(['--verbose', 'planner', '--timeout', '5', str(Path(__file__).parent / 'files' / 'opt_spec.json')])


def test_planner_error():
    with raises(ValueError):
        main(['--verbose', 'planner', '-p', 'notARealPath', str(Path(__file__).parent / 'files' / 'opt_spec.json')])
