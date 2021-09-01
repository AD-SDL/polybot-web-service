from pathlib import Path
import json

from pytest import fixture
from pytest_mock import MockerFixture

from polybot.config import settings
from polybot.models import Sample
from polybot.sample import load_samples, subscribe_to_study

_my_path = Path(__file__).parent


@fixture
def example_sample() -> dict:
    """Get an example sample response from ADC with a fresh token to access S3"""
    client = settings.generate_adc_client()
    assert settings.adc_study_id is not None, "Missing ADC_STUDY_ID environmental variable"
    study_response = client.get_study(settings.adc_study_id)
    return study_response['study']['samples'][0]


@fixture()
def mock_subscribe(example_sample, mocker: MockerFixture):
    # Make a fake subscription response
    ex_record = json.loads(_my_path.joinpath('files', 'example-adc-subscription-event.json').read_text())
    ex_record['newSample']['sample'] = example_sample  # Gives a sample with an active data URL

    # Mock the event generator
    def _fake_subscribe(*args, **kwargs):
        yield ex_record
    mocker.patch('polybot.config.ADCClient.subscribe_to_study', new=_fake_subscribe)


def test_subscribe(mock_subscribe):
    sample = next(subscribe_to_study())
    assert isinstance(sample, Sample)


def test_load(example_sample):
    samples = list(load_samples())
    assert len(samples) >= 1
