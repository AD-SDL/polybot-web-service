"""Routines for creating the REST interface"""

from fastapi import FastAPI

from .views import ingest

# Build the application
app = FastAPI()
app.include_router(ingest.router)


@app.get("/")
def home():
    return {"hello": "world"}
