"""Routes related to ingesting data from the robot"""
from urllib.parse import urlparse
import logging

from fastapi import APIRouter
from colmena.models import Result
from colmena.redis.queue import MethodServerQueues

from polybot.models import Sample
from polybot.config import settings
from polybot.sample import save_sample

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/ingest')


# Make a Redis result queue if settings
def _make_colmena_queue() -> MethodServerQueues:
    """Make queues needed to interact with planning service"""
    res = urlparse(settings.redis_address)
    port = 6379 if res.port is None else res.port
    return MethodServerQueues(hostname=res.hostname, port=port, topics=['robot'], clean_slate=False, name='method')


@router.post("/")
def upload_data(sample: Sample):
    """Intake a file from the robot and save it to disk"""
    logger.info(f'Received sample {sample.id}')

    # Save it to disk
    save_sample(sample)

    # Send the result to the planning service
    #  We use Colmena-formatted messages in a Redis queue
    if settings.redis_address is not None:
        queue = _make_colmena_queue()
        result = Result(((None,), {}))
        result.set_result(sample, 0)
        queue.send_result(
            result, topic='robot'
        )
        logger.info(f'Sent result to the planning service')

    return {'success': True, 'sample': sample.id}
