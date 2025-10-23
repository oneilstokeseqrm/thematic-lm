"""Tests for retry logic with exponential backoff."""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from thematic_lm.utils.retry import call_with_retry


@pytest.mark.asyncio
async def test_success_on_first_attempt():
    """Test successful call on first attempt (no retry)."""
    mock_fn = AsyncMock(return_value="success")

    result = await call_with_retry(mock_fn, max_attempts=3, base_delay=1.0, timeout=5.0)

    assert result == "success"
    assert mock_fn.call_count == 1


@pytest.mark.asyncio
async def test_success_after_retry():
    """Test success after 1 retry (should log INFO)."""
    mock_fn = AsyncMock(side_effect=[Exception("Transient error"), "success"])

    with patch("thematic_lm.utils.retry.logger") as mock_logger:
        result = await call_with_retry(
            mock_fn, max_attempts=3, base_delay=0.1, timeout=5.0
        )

        assert result == "success"
        assert mock_fn.call_count == 2

        # Verify INFO log on success after retry
        mock_logger.info.assert_called_once_with(
            "Call succeeded after retry", attempt=2
        )

        # Verify WARNING log on first failure
        assert mock_logger.warning.call_count >= 1


@pytest.mark.asyncio
async def test_timeout_after_max_attempts():
    """Test timeout after max attempts (should raise last exception)."""
    mock_fn = AsyncMock(side_effect=Exception("Persistent error"))

    with pytest.raises(Exception, match="Persistent error"):
        await call_with_retry(mock_fn, max_attempts=3, base_delay=0.1, timeout=5.0)

    assert mock_fn.call_count == 3


@pytest.mark.asyncio
async def test_exponential_backoff_timing():
    """Test exponential backoff timing (verify delays increase)."""
    mock_fn = AsyncMock(side_effect=[Exception("Error 1"), Exception("Error 2"), "success"])

    start_time = time.time()

    with patch("thematic_lm.utils.retry.logger"):
        result = await call_with_retry(
            mock_fn, max_attempts=3, base_delay=0.1, timeout=5.0
        )

    elapsed_time = time.time() - start_time

    assert result == "success"
    assert mock_fn.call_count == 3

    # Expected delays: 0.1 * (2^0) + jitter, 0.1 * (2^1) + jitter
    # = 0.1 + jitter (0-0.1), 0.2 + jitter (0-0.1)
    # Minimum total delay: 0.1 + 0.2 = 0.3 seconds
    # Maximum total delay: 0.1 + 0.1 + 0.2 + 0.1 = 0.5 seconds
    assert elapsed_time >= 0.3, f"Expected at least 0.3s delay, got {elapsed_time:.3f}s"
    assert elapsed_time < 1.0, f"Expected less than 1.0s delay, got {elapsed_time:.3f}s"


@pytest.mark.asyncio
async def test_timeout_error_handling():
    """Test handling of asyncio.TimeoutError."""

    async def slow_fn():
        await asyncio.sleep(10)
        return "too slow"

    with patch("thematic_lm.utils.retry.logger") as mock_logger:
        with pytest.raises(asyncio.TimeoutError):
            await call_with_retry(slow_fn, max_attempts=2, base_delay=0.1, timeout=0.1)

        # Verify WARNING logs for timeouts
        timeout_warnings = [
            call for call in mock_logger.warning.call_args_list
            if "timed out" in str(call).lower()
        ]
        assert len(timeout_warnings) >= 2


@pytest.mark.asyncio
async def test_jitter_applied():
    """Test that jitter is applied to backoff delays."""
    mock_fn = AsyncMock(side_effect=[Exception("Error 1"), Exception("Error 2"), "success"])

    # Run multiple times to verify jitter causes variation
    delays = []
    for _ in range(5):
        start_time = time.time()
        with patch("thematic_lm.utils.retry.logger"):
            await call_with_retry(mock_fn, max_attempts=3, base_delay=0.1, timeout=5.0)
        elapsed_time = time.time() - start_time
        delays.append(elapsed_time)
        mock_fn.reset_mock()
        mock_fn.side_effect = [Exception("Error 1"), Exception("Error 2"), "success"]

    # Verify that delays vary (jitter is working)
    # Not all delays should be exactly the same
    unique_delays = len(set(round(d, 3) for d in delays))
    assert unique_delays > 1, "Jitter should cause variation in delays"


@pytest.mark.asyncio
async def test_no_retry_on_success():
    """Test that no retry occurs when first attempt succeeds."""
    mock_fn = AsyncMock(return_value="immediate success")

    with patch("thematic_lm.utils.retry.logger") as mock_logger:
        result = await call_with_retry(
            mock_fn, max_attempts=3, base_delay=0.1, timeout=5.0
        )

        assert result == "immediate success"
        assert mock_fn.call_count == 1

        # Should not log INFO about retry (no retry occurred)
        mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_warning_on_all_attempts_failed():
    """Test WARNING log when all retry attempts fail."""
    mock_fn = AsyncMock(side_effect=Exception("Always fails"))

    with patch("thematic_lm.utils.retry.logger") as mock_logger:
        with pytest.raises(Exception, match="Always fails"):
            await call_with_retry(mock_fn, max_attempts=3, base_delay=0.1, timeout=5.0)

        # Verify final WARNING log
        final_warning = [
            call for call in mock_logger.warning.call_args_list
            if "All retry attempts failed" in str(call)
        ]
        assert len(final_warning) == 1
