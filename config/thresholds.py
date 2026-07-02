import csv
import logging
import sys
from pathlib import Path

from env_config import Config

logger = logging.getLogger("uploader-locust.thresholds")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def check(stats_csv_path: str) -> bool:
    config = Config.from_env()

    path = Path(stats_csv_path)
    if not path.exists():
        logger.error("Stats CSV not found: %s", path)
        return False

    failures: list[str] = []

    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "")
            if name in ("Aggregated", ""):
                continue

            try:
                p50 = float(row.get("50%", 0) or 0)
                p95 = float(row.get("95%", 0) or 0)
                p99 = float(row.get("99%", 0) or 0)
                total = float(row.get("Request Count", 0) or 0)
                failures_4xx = float(row.get("Failure Count", 0) or 0)
            except ValueError:
                continue

            if total == 0:
                continue

            error_rate = failures_4xx / total if total else 0

            logger.info(
                "%-50s  p50=%5.0fms  p95=%5.0fms  p99=%5.0fms  err=%.2f%%",
                name[:50], p50, p95, p99, error_rate * 100,
            )

            if p50 > config.threshold_p50_ms:
                failures.append(f"[BREACH] {name}: p50 {p50:.0f}ms > {config.threshold_p50_ms}ms")
            if p95 > config.threshold_p95_ms:
                failures.append(f"[BREACH] {name}: p95 {p95:.0f}ms > {config.threshold_p95_ms}ms")
            if p99 > config.threshold_p99_ms:
                failures.append(f"[BREACH] {name}: p99 {p99:.0f}ms > {config.threshold_p99_ms}ms")
            if error_rate > config.threshold_5xx_rate:
                failures.append(
                    f"[BREACH] {name}: error rate {error_rate:.2%} > {config.threshold_5xx_rate:.2%}"
                )

            if failures:
                logger.error("\n%s\n", "\n".join(failures))
                logger.error("Threshold check FAILED — %d breach(es) detected.", len(failures))
                return False

            logger.info("All threshold checks PASSED.")
            return True


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "results/run_stats.csv"
    ok = check(csv_path)
    sys.exit(0 if ok else 1)