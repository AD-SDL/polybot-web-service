"""Make sure the service launches correctly"""

import platform
from io import BytesIO
from pathlib import Path

from flask import url_for
from flask.testing import FlaskClient


def test_launch(client):
    res = client.get(url_for('home'))
    assert res.status_code == 200
    assert platform.node() in res.data.decode()


def test_upload(client: FlaskClient):
    data = {'name': 'test_experiment',
            'file': (BytesIO(b"Content!"), 'test.csv')}
    res = client.post(url_for('ingest.upload_data'), data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    assert res.json['success']
    assert res.json['filename'] == 'test_experiment.csv'
    assert (Path(client.application.config['UPLOAD_FOLDER'])
            .joinpath('test_experiment.csv').is_file())
