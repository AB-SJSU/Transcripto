import time
import functools
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

RETRYABLE_CODES = [
    "ProvisionedThroughputExceededException",
    "ThrottlingException",
    "ServiceUnavailable",
    "InternalServerError",
    "RequestExpired",
    "RequestThrottled",
]


def with_retries(max_attempts: int = 3, base_delay: float = 0.5, retryable_codes: list = None):
    """
    Decorator for exponential backoff retry on transient AWS ClientErrors.
    Non-retryable errors (ConditionalCheckFailedException, ValidationException, etc.) raise immediately.
    """
    codes = retryable_codes if retryable_codes is not None else RETRYABLE_CODES

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    code = e.response["Error"]["Code"]
                    if code not in codes:
                        raise
                    last_exception = e
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))  # 0.5s, 1s, 2s
                        logger.warning(
                            "%s attempt %d/%d failed with %s. Retrying in %.1fs...",
                            func.__name__, attempt, max_attempts, code, delay,
                        )
                        time.sleep(delay)
            logger.error("%s failed after %d attempts", func.__name__, max_attempts)
            raise last_exception
        return wrapper
    return decorator
