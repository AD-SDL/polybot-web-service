from pathlib import Path

from pytest import fixture

from polybot.models import Sample

_test_sample = str(Path(__file__).parent / 'files' / 'example-sample.json')


@fixture()
def example_sample() -> Sample:
    return Sample.parse_file(_test_sample)
