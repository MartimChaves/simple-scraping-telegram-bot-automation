"""AsyncIO-based scheduler with iteration limits."""

import asyncio
from collections.abc import Callable, Awaitable


async def run_scheduler(
    interval: int,
    scrape_fn: Callable[[], list[dict]],
    send_fn: Callable[[str], Awaitable[int]],
    format_fn: Callable[[list[dict]], str],
    max_iterations: int = 3,
    stop_event: asyncio.Event | None = None,
    on_log: Callable[[str], None] | None = None,
) -> None:
    """Run scrape+send in a loop.

    Args:
        interval: Seconds between iterations.
        scrape_fn: Sync function that returns scraped + cleaned data.
        send_fn: Async function that sends a formatted message.
        format_fn: Formats data list into a message string.
        max_iterations: Stop after this many iterations.
        stop_event: Set this event to stop the scheduler early.
        on_log: Optional callback for log messages.
    """
    if stop_event is None:
        stop_event = asyncio.Event()

    for i in range(max_iterations):
        if stop_event.is_set():
            break

        iteration = i + 1
        _log(on_log, f"Scheduler iteration {iteration}/{max_iterations}")

        try:
            data = scrape_fn()
            if data:
                message = format_fn(data)
                await send_fn(message)
                _log(on_log, f"Sent {len(data)} items to Telegram")
            else:
                _log(on_log, "No data scraped this iteration")
        except Exception as e:
            _log(on_log, f"Scheduler error: {e}")

        # Wait for the interval or until stopped
        if iteration < max_iterations:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                break  # stop_event was set
            except asyncio.TimeoutError:
                pass  # Timeout means we continue to next iteration

    _log(on_log, "Scheduler stopped")


def _log(on_log: Callable[[str], None] | None, message: str) -> None:
    if on_log:
        on_log(message)
