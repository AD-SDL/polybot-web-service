"""Routes related to ingesting data from the robot"""
import logging

from fastapi import APIRouter

from polybot.models import Sample

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/ingest')


@router.post("/")
def upload_data(sample: Sample):
    """Intake a file from the robot and save it to disk"""
    logger.info(f'Received sample {sample.id}')
    return {'success': True, 'sample': sample.id}
