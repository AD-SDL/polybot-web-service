from pathlib import Path

from requests import exceptions
from pytest import raises

from polybot.cli import main
from polybot.version import __version__

_test_sample = str(Path(__file__).parent / 'files' / 'example-sample.json')


def test_version(capsys):
    main(['--version'])
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_upload():
    main(['upload', '--dry-run', _test_sample])
    with raises(exceptions.ConnectionError):
        main(['upload', _test_sample])
