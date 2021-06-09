"""Tests for the REST API"""
from fastapi.testclient import TestClient

from polybot.fastapi import app

client = TestClient(app)


def test_home():
    res = client.get("/")
    assert res.status_code == 200


def test_upload():
    res = client.post('/ingest', json={'id': '1'*10}, allow_redirects=True)
    assert res.status_code == 200
    reply = res.json()
    assert reply['success']
    assert reply['sample'] == '1' * 10
