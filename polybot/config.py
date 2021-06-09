"""Settings for the service"""
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, HttpUrl

_run_folder = Path.cwd()


class Settings(BaseSettings):
    """Settings for the web service"""

    # Sample handling
    sample_folder: Path = Field(_run_folder / "samples", description="Path in which to store the samples")

    # Logging
    log_name: Optional[str] = Field(None, description="Name of the log file. If not provided, logs will not be stored")
    log_size: int = Field(1, description="Maximum log size in MB")

    # Interface with the controller
    robot_url: Optional[HttpUrl] = Field(None, description="Address of the robotic controller system")


settings = Settings()
