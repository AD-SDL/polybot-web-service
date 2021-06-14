"""Utilities for manipulating samples

Note: We currently just save things to disk as JSON files.
We will work with the "data infrastructure" team to figure out something better.
"""

import logging
from typing import Iterator

from .config import settings
from .models import Sample


logger = logging.getLogger(__name__)


def save_sample(sample: Sample, overwrite: bool = True):
    """Save a sample

    Args:
        sample: Sample to be saved
        overwrite: Whether overwriting existing files
    """

    path = settings.sample_folder / f"{sample.id}.json"
    if path.exists():
        if overwrite:
            logger.warning(f'Overwriting file at {sample.id}')
        else:
            raise ValueError(f"File already exists. Set overwrite=True, if you want to remove it. Path: {path}")
    with open(path, 'w') as fp:
        fp.write(sample.json(indent=2))
    logger.info(f'Wrote {sample.id} to {path}')


def load_samples() -> Iterator[Sample]:
    """Load all of the known samples from disk

    Yields:
        Samples in no prescribed order
    """

    for path in settings.sample_folder.glob("*.json"):
        try:
            yield Sample.parse_file(path)
        except BaseException:
            continue
