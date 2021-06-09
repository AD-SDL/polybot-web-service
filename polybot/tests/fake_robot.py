"""Fake robot service with FastAPI.

Emulates the main endpoints"""
import json

from fastapi import FastAPI, UploadFile, File


app = FastAPI()


@app.post('/upload/inputs.json')
async def accept_inputs(file: UploadFile = File(...)):
    data = json.load(file.file)
    return {
        'status': 'success',
        'sample_ID': data['id']
    }
