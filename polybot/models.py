"""Data models for objects used by this service"""
from typing import List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Sample(BaseModel):
    """Description for a UVVis experiment"""

    # Sample identifiers
    id: str = Field(..., description="Unique identifier for this sample used across robotic systems",
                    regex=r'[0-9a-f]{10}')

    # State information
    status: str = Field(None, description="Status of the sample")
    timestamp: List[str] = Field(default_factory=list, description='List of times sample object was modified')

    # Workflow information
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs to the system workflow")

    # Output data
    raw_output: Dict[str, Any] = Field(default_factory=dict, description="Data as recorded on an instrument")
    processed_output: Dict[str, Any] = Field(default_factory=dict,
                                             description="Summarized or post-processed versions of raw data")

    def reset_id(self):
        """Generate a new sample ID"""
        uuid = uuid4()
        self.id = uuid.hex[-10:]

    class Config:
        extra = 'allow'
