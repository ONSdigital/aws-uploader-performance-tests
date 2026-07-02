import logging

from metrics.custom_metrics import record_cold_start, record_upload_throughput

from config.env_config import Config
from utils.helpers import fire_request_event

config = Config.from_env()

logger = logging.getLogger("uploader-locust")

def _handle_homepage_response(resp, elapsed_ms: float):
    if resp.status_code == 200:
        resp.success()
        logger.debug("homepage OK %.1f ms", elapsed_ms)
        return
    if resp.status_code in (301, 302):
        resp.success()
        return
    resp.failure(f"Unexpected status {resp.status_code}")


def _build_presign_params() -> dict:
    return {
        "fileOneName": f"CTAX_EXTRACT_{config.test_lad_code}_{config.submission_date}.csv",
        "fileOneType": "text/csv",
        "fileOneSize": config.extract_file_size_bytes,
        "fileTwoName": f"CTAX_MANI_{config.test_lad_code}_{config.submission_date}.csv",
        "fileTwoType": "text/csv",
        "fileTwoSize": config.mani_file_size_bytes,
        "councilName": config.council_name,
    }


def _handle_presign_response(resp, latency_ms: float) -> dict | None:
    if resp.headers.get("x-cold-start") == "true":
        record_cold_start(latency_ms)
        logger.debug("Cold start detected %.1f ms", latency_ms)

    if resp.status_code == 200:
        resp.success()
        try:
            return resp.json()
        except Exception as err:
            resp.failure(f"Non-JSON 200 response from presign endpoint: {err}")
            return None

    if resp.status_code == 429:
        resp.failure("API GW throttle (HTTP Status: 429)")
        return None

    resp.failure(f"Presign failed with HTTP Status: {resp.status_code}")
    return None


def _handle_put_response(environment, resp, size_bytes: int, label: str, elapsed_s: float):
    if resp.status_code in (200, 204):
        mb_transferred = size_bytes / (1024 * 1024)
        throughput = mb_transferred / elapsed_s if elapsed_s > 0 else 0
        fire_request_event(environment, "PUT", label, elapsed_s, size_bytes)
        record_upload_throughput(throughput)
        logger.debug("%s OK %.2f MB in %.2fs = %.1f MB/s", label, mb_transferred, elapsed_s, throughput)
        return
    fire_request_event(
        environment, "PUT", label, elapsed_s, 0,
        exception=Exception(f"S3 upload failed with HTTP Status: {resp.status_code}"),
    )


def _handle_part_response(environment, resp, part_number: int, chunk_size: int, label: str, elapsed_s: float) -> dict | None:
    if resp.status_code in (200, 204):
        etag = resp.headers.get("ETag", "").strip('"')
        fire_request_event(environment, "PUT", label, elapsed_s, chunk_size)
        logger.debug("Part %d OK ETag=%s", part_number, etag)
        return {"PartNumber": part_number, "ETag": etag}

    fire_request_event(
        environment, "PUT", label, elapsed_s, 0,
        exception=Exception(f"Part upload failed with HTTP Status: {resp.status_code}"),
    )
    logger.error("Part %d failed with HTTP Status: %d — aborting", part_number, resp.status_code)
    return None


def _handle_complete_response(environment, resp, size_bytes: int, label: str, elapsed_s: float):
    if resp.status_code == 200:
        mb_transferred = size_bytes / (1024 * 1024)
        throughput = mb_transferred / elapsed_s if elapsed_s > 0 else 0
        fire_request_event(environment, "POST", f"{label} complete", elapsed_s, size_bytes)
        record_upload_throughput(throughput)
        logger.debug("%s multipart complete OK", label)
        return
    fire_request_event(
        environment, "POST", f"{label} complete", elapsed_s, 0,
        exception=Exception(f"Complete multipart failed with HTTP Status: {resp.status_code}"),
    )


def _fire_timeout(environment, request_type: str, label: str, timeout_s: int):
    fire_request_event(
        environment, request_type, label, timeout_s, 0,
        exception=Exception(f"{label} timed out"),
    )