import math
import random

def generate_dummy_file_bytes(size_bytes: int) -> bytes:
    rng = random.Random(42)
    chunk = bytes(rng.randint(0, 255) for _ in range(min(size_bytes, 65_536)))
    repeats, remainder = divmod(size_bytes, len(chunk))
    return chunk * repeats + chunk[:remainder]


def split_into_parts(data: bytes, part_count: int) -> list[bytes]:
    part_size = math.ceil(len(data) / part_count)
    return [data[i:i + part_size] for i in range(0, len(data), part_size)]


def fire_request_event(environment, request_type, name, elapsed_s, response_length, exception=None):
    environment.events.request.fire(
        request_type=request_type,
        name=name,
        response_time=elapsed_s * 1000,
        response_length=response_length,
        exception=exception,
        context={},
    )