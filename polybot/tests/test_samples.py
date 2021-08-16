from polybot.sample import load_samples
from polybot.config import settings


def test_load(example_sample):
    with open(settings.sample_folder / "test.json", 'w') as fp:
        fp.write('Junk')
    samples = list(load_samples())
    assert len(samples) == 1
    assert samples[0].ID == example_sample.ID
