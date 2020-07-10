import pytest

from polybot import create_app


@pytest.fixture
def app():
    return create_app()
