"""
Observability (Point 15): structured logging with latency + token usage.
"""
import logging
import time
import functools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("resume_extractor")


def log_call(fn):
    """Decorator: logs latency for any agent/tool call."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.info(f"START {fn.__name__}")
        try:
            result = fn(*args, **kwargs)
            latency = time.time() - start
            logger.info(f"END {fn.__name__} | latency={latency:.2f}s")
            return result
        except Exception as e:
            latency = time.time() - start
            logger.error(f"FAILED {fn.__name__} | latency={latency:.2f}s | error={e}")
            raise
    return wrapper


def log_token_usage(response, label: str = "call"):
    usage = getattr(response, "usage", None)
    if usage:
        logger.info(f"TOKENS[{label}] input={usage.input_tokens} output={usage.output_tokens}")
