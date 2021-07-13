"""Tests for the REST API"""


def test_home(fastapi_client):
    res = fastapi_client.get("/")
    assert res.status_code == 200


def test_upload(fastapi_client):
    res = fastapi_client.post('/ingest', json={'ID': '1'*10}, allow_redirects=True)
    assert res.status_code == 200
    reply = res.json()
    assert reply['success']
    assert reply['sample'] == '1' * 10
