import logging
import threading

logger = logging.getLogger("uploader-locust.metrics")

_lock = threading.Lock()

_cold_starts: list[float] = []
_total_requests: int = 0
_throughput_samples: list[float] = []

def record_cold_start(latency_ms: float) -> None:
    with _lock:
        _cold_starts.append(latency_ms)

def record_upload_throughput(mb_per_s: float) -> None:
    with _lock:
        _throughput_samples.append(mb_per_s)