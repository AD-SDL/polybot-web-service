from pathlib import Path

from pytest import raises
from pytest_mock import MockerFixture

from polybot.cli import main
from polybot.version import __version__

_test_sample = str(Path(__file__).parent / 'files' / 'example-sample.json')


def test_version(capsys):
    main(['version'])
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_upload(mocker: MockerFixture):
    mock = mocker.patch('requests.post')
    main(['upload', '--dry-run', _test_sample])
    assert mock.call_count == 0
    main(['upload', _test_sample])
    assert mock.call_count == 1


def test_planner():
    main(['--verbose', 'planner', '--timeout', '1', str(Path(__file__).parent / 'files' / 'opt_spec.json')])
    main(['--verbose', 'planner', '--timeout', '1', str(Path(__file__).parent / 'files' / 'opt_spec.yaml')])


def test_planner_error():
    with raises(ValueError):
        main(['--verbose', 'planner', '-p', 'notARealPath', str(Path(__file__).parent / 'files' / 'opt_spec.json')])
