import io
import logging
import requests
import time

from config.env_config import Config
from utils.helpers import generate_dummy_file_bytes, split_into_parts
from metrics.response_handlers import _handle_homepage_response, _build_presign_params, \
    _handle_presign_response, _handle_put_response, _fire_timeout, _handle_part_response, _handle_complete_response

logger = logging.getLogger("uploader-locust")
config = Config.from_env()

class UploaderBehaviour:
    def task_upload_session(self):
        self.task_homepage()
        self.task_upload_both_files()

    def task_homepage(self):
        start = time.perf_counter()
        with self.client.get(
                config.homepage_path,
                name=f"[CloudFront] GET {config.homepage_path}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                catch_response=True,
        ) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000
            _handle_homepage_response(resp, elapsed_ms)

    def task_upload_both_files(self):
        result = self.task_get_presigned_urls()
        if not result:
            return
        self._put_multipart(
            file_one_upload=result["fileOneUpload"],
            size_bytes=config.extract_file_size_bytes,
            label="[S3] PUT EXTRACT (20 MB)")

        self._put_single(
            upload_url=result["fileTwoUpload"]["uploadURL"],
            size_bytes=config.mani_file_size_bytes,
            label="[S3] PUT MANI (1 KB)")

    def task_get_presigned_urls(self) -> dict | None:
        params = _build_presign_params()
        start = time.perf_counter()
        with self.client.get(
            f"{config.api_gateway_base_url}{config.presign_path}",
            params=params,
            name=f"[API GW -> Lambda] GET {config.presign_path}",
            catch_response=True,
        ) as resp:
            latency_ms = (time.perf_counter() - start) * 1000
            return _handle_presign_response(resp, latency_ms)

    def _put_single(self, upload_url: str, size_bytes: int, label: str):
        payload = generate_dummy_file_bytes(size_bytes)
        start = time.perf_counter()
        try:
            resp = requests.put(
                upload_url,
                data=io.BytesIO(payload),
                headers={"Content-Type": "text/csv"},
                timeout=config.upload_timeout_s,
            )
            _handle_put_response(self.environment, resp, size_bytes, label, time.perf_counter() - start)
        except requests.Timeout:
            _fire_timeout(self.environment, "PUT", label, config.upload_timeout_s)

    def _put_multipart_parts(self, parts_meta: list, chunks: list) -> list | None:
        completed_parts = []
        for part, chunk in zip(parts_meta, chunks):
            result = self._put_part(part, chunk, len(parts_meta))
            if result is None:
                return None
            completed_parts.append(result)
        return completed_parts

    def _put_part(self, part: dict, chunk: bytes, total_parts: int) -> dict | None:
        part_number = part["PartNumber"]
        label = f"[S3] PUT EXTRACT (20 MB) part {part_number}/{total_parts}"
        start = time.perf_counter()
        try:
            resp = requests.put(
                part["uploadURL"],
                data=io.BytesIO(chunk),
                headers={"Content-Type": "text/csv"},
                timeout=config.upload_timeout_s,
            )
            elapsed_s = time.perf_counter() - start
            return _handle_part_response(self.environment, resp, part_number, len(chunk), label, elapsed_s)
        except requests.Timeout:
            _fire_timeout(self.environment, "PUT", label, config.upload_timeout_s)
            return None

    def _complete_multipart(self, complete_url: str, completed_parts: list, size_bytes: int, label: str):
        start = time.perf_counter()
        try:
            resp = requests.post(
                complete_url,
                json={"parts": completed_parts},
                timeout=30,
            )
            elapsed_s = time.perf_counter() - start
            _handle_complete_response(self.environment, resp, size_bytes, label, elapsed_s)
        except requests.Timeout:
            _fire_timeout(self.environment, "POST", f"{label} complete", 30)

    def _put_multipart(self, file_one_upload: dict, size_bytes: int, label: str):
        parts_meta = file_one_upload.get("parts", [])
        complete_url = file_one_upload.get("completeURL")

        if not parts_meta or not complete_url:
            logger.error("Multipart upload missing parts or completeURL")
            return

        payload = generate_dummy_file_bytes(size_bytes)
        chunks = split_into_parts(payload, len(parts_meta))
        completed_parts = self._put_multipart_parts(parts_meta, chunks)

        if completed_parts is None:
            return

        self._complete_multipart(complete_url, completed_parts, size_bytes, label)