import logging

from locust import LoadTestShape

logger = logging.getLogger("locust.runners")

class StressShape(LoadTestShape):
    """
    Escalating stress: VUs increase every 3 minutes until a ceiling
    or until the test is stopped manually when errors appear.

    Monitor in real time — stop when:
      - p95 > 600 ms
      - 4xx rate > 1%
      - 5xx rate > 0.1%
    """

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 5},
        {"duration": 180, "users": 25, "spawn_rate": 5},
        {"duration": 360, "users": 50, "spawn_rate": 10},
        {"duration": 540, "users": 75, "spawn_rate": 10},
        {"duration": 720, "users": 100, "spawn_rate": 10},
        {"duration": 900, "users": 150, "spawn_rate": 15},
        {"duration": 1080, "users": 200, "spawn_rate": 20},
        {"duration": 1260, "users": 300, "spawn_rate": 25},
        {"duration": 1440, "users": 350, "spawn_rate": 25},  # ~Max council load
    ]

    def tick(self):
        logger.info("Applying StressShape to stress test")
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None