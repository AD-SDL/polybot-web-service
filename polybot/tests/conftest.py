from pathlib import Path
from shutil import rmtree

from pytest import fixture

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
