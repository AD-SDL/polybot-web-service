from pathlib import Path

from pytest import fixture, raises

from polybot.sample import save_sample, load_samples
from polybot.config import settings


@fixture(autouse=True)
def sample_dir(tmpdir):
    settings.sample_folder = Path(tmpdir)


def test_save(example_sample):
    save_sample(example_sample)
    assert settings.sample_folder.joinpath(f'{example_sample.id}.json').is_file()
    with raises(ValueError):
        save_sample(example_sample, overwrite=False)


def test_load(example_sample):
    test_save(example_sample)
    samples = list(load_samples())
    assert len(samples) == 1
    assert samples[0].id == example_sample.id
