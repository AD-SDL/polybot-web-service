"""Make sure the service launches correctly"""

import platform

from flask import url_for


def test_launch(client):
    res = client.get(url_for('home'))
    assert res.status_code == 200
    assert platform.node() in res.data.decode()
