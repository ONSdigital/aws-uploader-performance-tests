import logging

from locust import LoadTestShape

logger = logging.getLogger("uploader-locust.spike")

class SpikeShape(LoadTestShape):
    """
    Spike: instant jump from 1 → 100 VUs, held briefly, then drop back.
    Reveals cold-start frequency, burst-error rate, and recovery time.

    Timeline (seconds):
      0-10:   baseline (1 VU)
      10-11:  instant spike to 100
      11-130: hold spike
      130-140: instant drop to 5
      140-240: recovery observation
      240+:   done
    """

    stages = [
        {"duration": 10, "users": 1, "spawn_rate": 1},
        {"duration": 11, "users": 100, "spawn_rate": 100},  # Instant spike
        {"duration": 130, "users": 100, "spawn_rate": 1},  # Hold
        {"duration": 140, "users": 5, "spawn_rate": 100},  # Drop
        {"duration": 240, "users": 5, "spawn_rate": 1},  # Recovery
    ]

    def tick(self):
        logger.info("Applying SpikeShape to spike test")
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None