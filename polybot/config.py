"""Settings for the service"""
from pathlib import Path
from typing import Optional, Tuple, List
from urllib.parse import urlparse

from adc_sdk.client import ADCClient
from colmena.redis.queue import ClientQueues, TaskServerQueues
from pydantic import BaseSettings, Field, HttpUrl, RedisDsn

_run_folder = Path.cwd()


class Settings(BaseSettings):
    """Settings for the web service"""

    # Configuration related to data storage on the Argonne Data Cloud
    adc_access_token: Optional[str] = Field(None, description='Token for accessing the Argonne Data Cloud')
    adc_study_id: Optional[str] = Field(None, description='Study ID associated with this experiment')

    # Logging
    log_name: Optional[str] = Field(None, description="Name of the log file. If not provided, logs will not be stored")
    log_size: int = Field(1, description="Maximum log size in MB")

    # Interface between the thinker and any remote compute processes
    redis_url: Optional[RedisDsn] = Field(None, description="URL of the redis service. Used to send messages "
                                                            "between web and planning services")

    # Interface with the controller
    robot_url: Optional[HttpUrl] = Field(None, description="Address of the robotic controller system")

    # Settings for the Colmena task server
    task_queues: Optional[List[str]] = Field(['compute'],
                                             description='Additional task queues to create for the Colmena service')

    @property
    def redis_info(self) -> Tuple[str, int]:
        """The redis connection information

        Returns:
            - Redis hostname
            - Redis port
        """
        if self.redis_url is None:
            raise AttributeError('Redis URL is not defined!')
        res = urlparse(settings.redis_url)
        port = 6379 if res.port is None else res.port
        return res.hostname, port

    class Config:
        env_file: str = ".env"

    def make_client_queue(self) -> ClientQueues:
        """Make the client side of the event queue

        Returns:
            Client side of queues with the proper defaults
        """
        hostname, port = self.redis_info
        return ClientQueues(hostname, port, name='polybot', topics=['robot'] + self.task_queues,
                            serialization_method='pickle')

    def make_server_queue(self) -> TaskServerQueues:
        """Make the server side of the event queue

        Returns:
            Server side of the queue with the proper defaults
        """
        hostname, port = self.redis_info
        return TaskServerQueues(hostname, port, name='polybot', topics=['robot'] + self.task_queues)

    def generate_adc_client(self) -> ADCClient:
        """Create an authenticated ADC client

        Returns:
            A client to the ADC that is ready to make queries
        """
        return ADCClient(self.adc_access_token)


settings = Settings()
