"""Routes related to ingesting data from the robot"""
import logging

from fastapi import APIRouter
from colmena.models import Result

from polybot.models import Sample
from polybot.config import settings
from polybot.sample import save_sample

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/ingest')


@router.post("/")
def upload_data(sample: Sample):
    """Intake a file from the robot and save it to disk"""
    logger.info(f'Received sample {sample.id}')

    # Save it to disk
    save_sample(sample)

    # Send the result to the planning service
    #  We use Colmena-formatted messages in a Redis queue
    if settings.redis_address is not None:
        queue = settings.make_server_queue()
        result = Result(((None,), {}))
        result.set_result(sample, 0)
        queue.send_result(
            result, topic='robot'
        )
        logger.info('Sent result to the planning service')

    return {'success': True, 'sample': sample.id}
