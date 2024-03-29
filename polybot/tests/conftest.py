from pathlib import Path
import json

from adc_sdk.models import StudySubscriptionEvent
from pytest import fixture
from pytest_mock import MockerFixture

from polybot.models import Sample, SampleTemplate
from polybot.config import settings

file_path = Path(__file__).parent / 'files'
sample_path = str(file_path / 'example-sample.json')
_test_dir = Path(__file__).parent


@fixture(autouse=True)
def test_settings():
    # Set up the test Redis service
    settings.redis_url = "rediss://localhost"


@fixture()
def example_sample() -> Sample:
    return Sample.parse_file(sample_path)


@fixture()
def example_template() -> SampleTemplate:
    return SampleTemplate.parse_file(file_path / 'example-template.json')


@fixture
def example_sample() -> dict:
    """Get an example sample response from ADC with a fresh token to access S3"""
    client = settings.generate_adc_client()
    assert settings.adc_study_id is not None, "Missing ADC_STUDY_ID environmental variable"
    study_response = client.get_study(settings.adc_study_id)
    return study_response.samples[0]


@fixture()
def mock_subscribe(example_sample, mocker: MockerFixture):
    # Make a fake subscription response with a real sample
    ex_record = json.loads(file_path.joinpath('example-adc-subscription-event.json').read_text())['study']
    ex_record['sample'] = example_sample.dict()  # Gives a sample with an active data URL
    event = StudySubscriptionEvent.parse_event(ex_record)

    # Mock the event generator
    mocker.patch('polybot.config.ADCClient.subscribe_to_study', return_value=iter([event]))
