"""Retry logic with exponential backoff for LLM API calls."""

import asyncio
import random
from typing import Any, Awaitable, Callable, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


async def call_with_retry(
    fn: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    timeout: float = 30.0,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Call async function with exponential backoff retry.

    Args:
        fn: Async function to call
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds (doubled each retry)
        timeout: Timeout per attempt in seconds
        *args: Positional arguments for fn
        **kwargs: Keyword arguments for fn

    Returns:
        Result from fn

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            result = await asyncio.wait_for(fn(*args, **kwargs), timeout=timeout)

            if attempt > 0:
                logger.info("Call succeeded after retry", attempt=attempt + 1)

            return result

        except asyncio.TimeoutError as e:
            last_exception = e
            logger.warning(
                "Call timed out",
                attempt=attempt + 1,
                max_attempts=max_attempts,
                timeout=timeout,
            )

        except Exception as e:
            last_exception = e
            logger.warning(
                "Call failed",
                attempt=attempt + 1,
                max_attempts=max_attempts,
                error=str(e),
            )

        if attempt < max_attempts - 1:
            # Add jitter to prevent thundering herd
            delay = base_delay * (2**attempt) + random.uniform(0, 0.1)
            await asyncio.sleep(delay)

    logger.warning("All retry attempts failed", max_attempts=max_attempts)
    raise last_exception
