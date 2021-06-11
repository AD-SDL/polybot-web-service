"""Data models for objects used by this service"""
from typing import List, Dict, Any

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

    class Config:
        extra = 'allow'
