"""Utilities for manipulating samples

Note: We currently just save things to disk as JSON files.
We will work with the "data infrastructure" team to figure out something better.
"""

import logging
from typing import Iterator

from adc_sdk.models import Sample as ADCSample

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
        yield _parse_sample(event.sample)


def load_samples() -> Iterator[Sample]:
    """Load all of the known samples from disk

    Yields:
        Samples in no prescribed order
    """

    # Query to get the list of samples in the study
    adc_client = settings.generate_adc_client()
    if settings.adc_study_id is None:
        raise ValueError('The ADC study id is not set. Set your ADC_STUDY_ID environment variable.')
    study = adc_client.get_study(settings.adc_study_id)

    for sample in study.samples:
        yield _parse_sample(sample)


def _parse_sample(sample: ADCSample) -> Sample:
    """Create a Sample object given a sample record from ADC

    Args:
        sample: Sample information record from ADC
    Returns:
        Sample object in the format created by polybot
    """
    # Pull down the JSON associated with each sample
    sample_data = sample.get_file(verify=False)

    # Parse as a sample object
    return Sample.parse_raw(sample_data)
