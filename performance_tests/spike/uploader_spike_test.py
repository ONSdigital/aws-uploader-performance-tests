from locust import HttpUser, between, task

from behaviour import UploaderBehaviour
from config.env_config import Config
from shapes import SpikeShape # yes, this import is being used. Locust is picking it up automatically, otherwise the default shape is used.

config = Config.from_env()

class SpikeTestUser(UploaderBehaviour, HttpUser):
    host = config.cloudfront_base_url
    wait_time = between(0.1, 0.5)
    weight = 1

    @task
    def upload_session(self):
        self.task_upload_session()