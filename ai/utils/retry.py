from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def with_retry(max_attempts=3, min_wait=1, max_wait=10, exceptions=(Exception,)):
    """
    Decorator for retrying functions with exponential backoff.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )
