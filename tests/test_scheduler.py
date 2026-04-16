"""Tests for the scheduler module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from scheduler import run_scheduler


@pytest.mark.asyncio
async def test_runs_max_iterations():
    scrape_fn = MagicMock(return_value=[{"text": "hello"}])
    send_fn = AsyncMock()
    format_fn = MagicMock(return_value="formatted")

    await run_scheduler(
        interval=0,
        scrape_fn=scrape_fn,
        send_fn=send_fn,
        format_fn=format_fn,
        max_iterations=3,
    )

    assert scrape_fn.call_count == 3
    assert send_fn.call_count == 3


@pytest.mark.asyncio
async def test_stops_on_event():
    scrape_fn = MagicMock(return_value=[{"text": "hello"}])
    send_fn = AsyncMock()
    format_fn = MagicMock(return_value="formatted")
    stop = asyncio.Event()

    # Stop after first iteration
    call_count = 0
    original_send = send_fn.side_effect

    async def stop_after_first(msg):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            stop.set()

    send_fn.side_effect = stop_after_first

    await run_scheduler(
        interval=10,
        scrape_fn=scrape_fn,
        send_fn=send_fn,
        format_fn=format_fn,
        max_iterations=3,
        stop_event=stop,
    )

    assert scrape_fn.call_count == 1


@pytest.mark.asyncio
async def test_handles_empty_scrape():
    scrape_fn = MagicMock(return_value=[])
    send_fn = AsyncMock()
    format_fn = MagicMock(return_value="formatted")

    await run_scheduler(
        interval=0,
        scrape_fn=scrape_fn,
        send_fn=send_fn,
        format_fn=format_fn,
        max_iterations=2,
    )

    assert scrape_fn.call_count == 2
    assert send_fn.call_count == 0  # No data, so no sends


@pytest.mark.asyncio
async def test_logs_callback():
    scrape_fn = MagicMock(return_value=[{"text": "hello"}])
    send_fn = AsyncMock()
    format_fn = MagicMock(return_value="formatted")
    logs = []

    await run_scheduler(
        interval=0,
        scrape_fn=scrape_fn,
        send_fn=send_fn,
        format_fn=format_fn,
        max_iterations=1,
        on_log=logs.append,
    )

    assert any("iteration 1/1" in log for log in logs)
    assert any("Sent 1 items" in log for log in logs)
    assert any("stopped" in log.lower() for log in logs)
