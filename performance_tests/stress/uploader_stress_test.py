import gevent
import logging

from locust import HttpUser, between, events, task

from config.env_config import Config
from behaviours.uploader_behaviour import UploaderBehaviour
from shapes import StressShape  # yes, this import is being used. Locust is picking it up automatically, otherwise the default shape is used.

logger = logging.getLogger("uploader-locust.stress")
config = Config.from_env()

MIN_REQUESTS_BEFORE_CHECK = 50

class StressTestUser(UploaderBehaviour, HttpUser):
    host = config.cloudfront_base_url
    wait_time = between(0.5, 1.5)
    weight = 1

    @task
    def upload_session(self):
        self.task_upload_session()


@events.init.add_listener
def on_init(environment, **kwargs):
    gevent.spawn(_monitor_thresholds, environment)


def _monitor_thresholds(environment):
    while not environment.runner is None:
        gevent.sleep(10)  # Check every 10 seconds
        _check_thresholds(environment)


def _check_thresholds(environment):
    for name, entry in environment.runner.stats.entries.items():
        if entry.num_requests < MIN_REQUESTS_BEFORE_CHECK:
            continue

        p95 = entry.get_response_time_percentile(0.95)
        error_rate = entry.num_failures / entry.num_requests if entry.num_requests > 0 else 0

        if p95 and p95 > config.threshold_p95_ms:
            logger.warning(
                "STRESS BREACH — %s: p95=%.0fms exceeds threshold of %.0fms — stopping test",
                name, p95, config.threshold_p95_ms,
            )
            environment.runner.quit()
            return

        if error_rate > config.threshold_5xx_rate:
            logger.warning(
                "STRESS BREACH — %s: error rate=%.2f%% exceeds threshold of %.2f%% — stopping test",
                name, error_rate * 100, config.threshold_5xx_rate * 100,
            )
            environment.runner.quit()
            return