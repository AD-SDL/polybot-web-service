"""Interface to the robot controller"""
from typing import Callable
import logging

import requests

from .config import settings
from .models import Sample

logger = logging.getLogger(__name__)


def _check_if_robot_defined(function: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        if settings.robot_url is None:
            raise ConnectionError('Robot URL is not defined')
        return function(*args, **kwargs)
    return wrapper


@_check_if_robot_defined
def send_new_sample(sample: Sample):
    """Send a new sample to be run by the PolyBot system

    Args:
        sample: Sample to be created on the Robot
    """
    # Send the request
    logger.info(f'Sending sample {sample.id} to robot controller')
    res = requests.post(
        url=settings.robot_url + "upload/inputs.json",
        files={"file": [f'{sample.id}.json', sample.json(), 'application/json']}
    )

    # Check if the result was
    if res.status_code != 200:
        raise ValueError(f'Failure to send new sample: Error: {res.text}')
    out = res.json()
    if out['status'] != 'success':
        raise ValueError(f'Failure to send new sample. Error: {out.get("error")}')
