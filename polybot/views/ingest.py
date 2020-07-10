"""Routes related to ingesting data from the robot"""

import os
import logging
from pathlib import Path

from flask import Blueprint, request, current_app
from pydantic import ValidationError
from werkzeug.utils import secure_filename

from polybot.models import UVVisExperiment


logger = logging.getLogger(__name__)
bp = Blueprint('ingest', __name__, url_prefix='/ingest')


@bp.route('/', methods=('POST',))
def upload_data():
    """Intake a file from the robot and save it to disk"""

    # Check the format of the request
    if 'file' not in request.files:
        logger.info('Bad request, missing the file')
        return {
            'success': False,
            'error': 'File not included in the message'
        }
    try:
        metadata = UVVisExperiment.parse_obj(request.form)
    except ValidationError as exc:
        logger.info('Bad request, failed validation')
        return {
            'success': False,
            'error': str(exc)
        }

    # Save the file somewhere accessible
    filename = secure_filename(f'{metadata.name}.csv')
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    output_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
    logger.info(f'Saving file to: {output_path}')
    file = request.files['file']
    file.save(output_path)
    return {'success': True, 'filename': output_path.name}
