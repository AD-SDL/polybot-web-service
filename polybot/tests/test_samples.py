from pathlib import Path

from polybot.models import Sample
from polybot.sample import load_samples, subscribe_to_study

_my_path = Path(__file__).parent


def test_subscribe(mock_subscribe):
    sample = next(subscribe_to_study())
    assert isinstance(sample, Sample)


def test_load(example_sample):
    samples = list(load_samples())
    assert len(samples) >= 1
