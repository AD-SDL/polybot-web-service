"""Data models for objects used by this service"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class UVVisExperiment(BaseModel):
    """Description for a UVVis experiment"""

    # Metadata about the experiment
    name: str = Field(..., description='Name for the experiment')
    date_created: datetime = Field(datetime.utcnow(), description='Date this result was created')
    sample_description: dict = Field({}, description='Description of the sample')

    # Key data about the experiment
    wavelength: Optional[List[float]] = Field(None, description='Wavelength of incident radiation')
    absorption: Optional[List[float]] = Field(None, description='Absorption of the sample')
