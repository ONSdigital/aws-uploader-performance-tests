import os
from dataclasses import dataclass


@dataclass
class Config:
    env: str
    cloudfront_base_url: str
    api_gateway_base_url: str
    test_lad_code: str
    council_name: str
    submission_date: str
    homepage_path: str
    presign_path: str
    extract_file_size_bytes: int
    mani_file_size_bytes: int
    upload_timeout_s: int
    threshold_p50_ms: float
    threshold_p95_ms: float
    threshold_p99_ms: float
    threshold_5xx_rate: float
    threshold_cold_start_rate: float
    threshold_throughput_mbs: float


    @classmethod
    def from_env(cls) -> "Config":
        env = os.getenv("ENV", "dev")
        test_lad_code = os.getenv("TEST_LAD_CODE", "P00000000")

        return cls(
            env=env,
            cloudfront_base_url=os.getenv("CLOUDFRONT_BASE_URL", f"https://uploader.ingest-{env}.aws.onsdigital.uk"),
            api_gateway_base_url=os.getenv("API_GATEWAY_BASE_URL", ""),
            test_lad_code=test_lad_code,
            council_name=os.getenv("COUNCIL_NAME", "Performance-Test"),
            submission_date=os.getenv("SUBMISSION_DATE", "20261231"),
            homepage_path=os.getenv("HOMEPAGE_PATH", f"/council-tax/{test_lad_code}-Performance-Test.html"),
            presign_path=os.getenv("PRESIGN_PATH", "/pre-signed-url"),
            extract_file_size_bytes=int(os.getenv("EXTRACT_FILE_SIZE_BYTES", str(20 * 1024 * 1024))),  # 20 MB
            mani_file_size_bytes=int(os.getenv("MANI_FILE_SIZE_BYTES", str(1 * 1024))),  # 1 KB
            upload_timeout_s=int(os.getenv("UPLOAD_TIMEOUT_S", "120")),
            threshold_p50_ms = float(os.getenv("THRESHOLD_P50_MS", "150")),
            threshold_p95_ms = float(os.getenv("THRESHOLD_P95_MS", "400")),
            threshold_p99_ms = float(os.getenv("THRESHOLD_P99_MS", "800")),
            threshold_5xx_rate = float(os.getenv("THRESHOLD_5XX_RATE", "0.001")),  # 0.1%
            threshold_cold_start_rate = float(os.getenv("THRESHOLD_COLD_START_RATE", "0.05")),  # 5%
            threshold_throughput_mbs = float(os.getenv("THRESHOLD_THROUGHPUT_MBS", "10.0")),  # 10 MB/s minimum
        )