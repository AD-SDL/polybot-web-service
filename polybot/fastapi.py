"""Routines for creating the REST interface"""
from logging.handlers import RotatingFileHandler
from datetime import datetime
import logging

from fastapi import FastAPI

from .views import ingest
from .config import settings

logger = logging.getLogger(__name__)
_start_time = datetime.now()

# Build the application
app = FastAPI()
app.include_router(ingest.router)

# Define the logging, if desired
if settings.log_name is not None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[RotatingFileHandler(settings.log_name, mode='a',
                                      maxBytes=1024 * 1024 * settings.log_size, backupCount=1)])


@app.get("/")
def home():
    return {"msg": f"System has been online since {_start_time.isoformat()}"}
