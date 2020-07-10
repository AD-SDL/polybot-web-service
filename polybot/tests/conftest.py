import shutil
import os

import pytest

from polybot import create_app

test_config = {
    'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), 'files')
}


@pytest.fixture
def app():
    shutil.rmtree(test_config['UPLOAD_FOLDER'], ignore_errors=True)
    return create_app(test_config)
