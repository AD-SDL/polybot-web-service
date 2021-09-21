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


def subscribe_to_study() -> Iterator[Sample]:
    """Subscribe to the "new sample" created event feed

    Yields:
        Latest samples as they are created
    """

    # Query to get the list of samples in the study
    adc_client = settings.generate_adc_client()
    if settings.adc_study_id is None:
        raise ValueError('The ADC study id is not set. Set your ADC_STUDY_ID environment variable.')

    for event in adc_client.subscribe_to_study(settings.adc_study_id):
        # Check that we have the right type of event
        if "newSample" not in event:
            logger.debug('Event type was not "newSample"')
            continue

        # Get the sample information
        sample = event["newSample"]["sample"]
        yield _parse_sample(sample)


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
        yield _parse_sample(sample)


def _parse_sample(sample_record: dict) -> Sample:
    """Create a Sample object given a sample record from ADC

    Args:
        sample_record: Sample information record from ADC
    Returns:
        Sample object in the format used by `pol
    """
    # Pull down the JSON associated with each sample
    json_url = sample_record['url']
    sample_data = get(json_url, verify=False).json()

    # Parse as a sample object
    return Sample.parse_obj(sample_data)
