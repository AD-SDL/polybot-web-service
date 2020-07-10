"""Routes related to ingesting data from the robot"""

import os
from pathlib import Path

from flask import Blueprint, request, current_app
from pydantic import ValidationError
from werkzeug.utils import secure_filename

from polybot.models import UVVisExperiment

bp = Blueprint('ingest', __name__, url_prefix='/ingest')


@bp.route('/', methods=('POST',))
def upload_data():
    """Intake a file from the robot and save it to disk"""

    # Check the format of the request
    if 'file' not in request.files:
        return {
            'success': False,
            'error': 'File not included in the message'
        }
    try:
        metadata = UVVisExperiment.parse_obj(request.form)
    except ValidationError as exc:
        return {
            'success': False,
            'error': str(exc)
        }

    # Save the file somewhere accessible
    filename = secure_filename(f'{metadata.name}.csv')
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    output_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
    file = request.files['file']
    file.save(output_path)
    return {'success': True, 'filename': output_path.name}
