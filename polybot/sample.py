"""Utilities for manipulating samples

Note: We currently just save things to disk as JSON files.
We will work with the "data infrastructure" team to figure out something better.
"""

import logging
from typing import Iterator
from requests import get

from .config import settings
from .models import Sample


logger = logging.getLogger(__name__)


def load_samples() -> Iterator[Sample]:
    """Load all of the known samples from disk

    Yields:
        Samples in no prescribed order
    """

    # Query to get the list of samples in the study
    adc_client = settings.generate_adc_client()
    if settings.adc_study_id is None:
        raise ValueError('The ADC study id is not set. Set your ADC_STUDY_ID environment variable.')
    study_info = adc_client.get_study(settings.adc_study_id)

    for sample in study_info['study']['samples']:
        # Pull down the JSON associated with each sample
        json_url = sample['url']
        sample_data = get(json_url, verify=False).json()

        # Yield the result a Sample object
        try:
            yield Sample.parse_obj(sample_data)
        except Exception:
            logger.warning(f'Failed to parse Sample ID {sample["id"]}')
