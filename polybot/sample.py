"""Utilities for manipulating samples

Note: We currently just save things to disk as JSON files.
We will work with the "data infrastructure" team to figure out something better.
"""

import logging
from typing import Iterator

from .config import settings
from .models import Sample
from adc import sample


logger = logging.getLogger(__name__)


def load_samples() -> Iterator[Sample]:
    """Load all of the known samples from disk

    Yields:
        Samples in no prescribed order
    """

    sample()
    for path in settings.sample_folder.glob("*.json"):
        try:
            yield Sample.parse_file(path)
        except BaseException:
            continue
