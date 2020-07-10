from flask.testing import FlaskClient
from requests import exceptions
from pytest import raises

from polybot.cli import main
from polybot.version import __version__


def test_version(capsys):
    main(['--version'])
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_upload(client: FlaskClient):
    with raises(exceptions.ConnectionError):
        main(['upload', 'cli_test', __file__])
