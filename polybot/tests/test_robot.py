from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from pytest import raises, fixture

from polybot.robot import send_new_sample
from polybot.config import settings


@fixture()
def mock_post(mocker: MockerFixture) -> MagicMock:
    class FakeReply:
        status_code = 200

        def json(self):
            return {'status': 'success'}

    mock = mocker.patch('requests.post', return_value=FakeReply())
    return mock


def test_submit(example_sample, mock_post):
    # Try without the robot URL defined
    with raises(ConnectionError):
        send_new_sample(example_sample)

    # Try with the robot URL defind
    settings.robot_url = "http://doesntmatter.com/"
    send_new_sample(example_sample)
    assert mock_post.call_count == 1


def test_mock(example_sample):
    settings.robot_url = 'http://mock.com'
    send_new_sample(example_sample)
