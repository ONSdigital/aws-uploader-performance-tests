from locust import HttpUser, between, task

from config.env_config import Config
from behaviours.uploader_behaviour import UploaderBehaviour

config = Config.from_env()

class LoadTestUser(UploaderBehaviour, HttpUser):
    host = config.cloudfront_base_url
    wait_time = between(1, 3)
    weight = 1

    @task
    def upload_session(self):
        self.task_upload_session()
