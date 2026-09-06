"""
Error handling / retries / malformed JSON recovery (Point 14).
No external dependency needed - simple manual retry with backoff.
"""
import time
import functools
from utils.logging_config import logger


def retry_on_failure(max_attempts: int = 3, backoff_seconds: float = 1.5):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"{fn.__name__} failed on attempt {attempt}/{max_attempts}: {e}"
                    )
                    if attempt < max_attempts:
                        time.sleep(backoff_seconds * attempt)
            raise RuntimeError(
                f"{fn.__name__} failed after {max_attempts} attempts: {last_error}"
            )
        return wrapper
    return decorator


def clean_json_text(raw_output: str) -> str:
    """Strip markdown code fences etc. that models sometimes add."""
    raw_output = raw_output.strip()
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`")
        if raw_output.lower().startswith("json"):
            raw_output = raw_output[4:].strip()
    return raw_output
