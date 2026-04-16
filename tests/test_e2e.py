"""End-to-end test: scrape -> clean -> format -> send (all mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cleaner import clean_data, export_data
from scraper import scrape_page, URLValidationError
from telegram_bot import send_message, schedule_delete


SAMPLE_HTML = """
<html><body>
  <div class="quote"><span class="text">  Quote one  </span></div>
  <div class="quote"><span class="text">Quote two</span></div>
  <div class="quote"><span class="text">  Quote one  </span></div>
</body></html>
"""


@patch("scraper.requests.get")
@patch("scraper.socket.gethostbyname", return_value="93.184.216.34")
def test_full_scrape_clean_export_flow(_mock_dns, mock_get):
    """Test the full scrape -> clean -> export pipeline."""
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_HTML
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    # Step 1: Scrape
    raw = scrape_page("http://example.com", ".quote .text")
    assert len(raw) == 3

    # Step 2: Clean (dedup + trim)
    cleaned = clean_data(raw)
    assert len(cleaned) == 2
    assert cleaned[0] == {"text": "Quote one"}
    assert cleaned[1] == {"text": "Quote two"}

    # Step 3: Export
    json_out = export_data(cleaned, "JSON")
    assert "Quote one" in json_out
    assert "Quote two" in json_out

    csv_out = export_data(cleaned, "CSV")
    assert "text" in csv_out  # header
    assert "Quote one" in csv_out


@pytest.mark.asyncio
async def test_full_scrape_clean_send_flow():
    """Test the full scrape -> clean -> send to Telegram pipeline."""
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_HTML
    mock_resp.raise_for_status = MagicMock()

    mock_bot = MagicMock()
    mock_bot.session = MagicMock()
    mock_bot.session.close = AsyncMock()
    sent_msg = MagicMock()
    sent_msg.message_id = 99
    mock_bot.send_message = AsyncMock(return_value=sent_msg)

    with (
        patch("scraper.socket.gethostbyname", return_value="93.184.216.34"),
        patch("scraper.requests.get", return_value=mock_resp),
        patch("telegram_bot.Bot", return_value=mock_bot),
    ):
        # Scrape + clean
        raw = scrape_page("http://example.com", ".quote .text")
        cleaned = clean_data(raw)

        # Format message
        lines = [item["text"] for item in cleaned]
        message = "\n".join(f"• {line}" for line in lines)

        # Send to Telegram + schedule delete
        msg_id = await send_message("token", "chat_123", message)
        schedule_delete("token", "chat_123", msg_id, delay=9999)  # long delay so it doesn't fire during test

        assert msg_id == 99
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert "Quote one" in call_kwargs["text"]
        assert "Quote two" in call_kwargs["text"]


def test_blocked_url_does_not_scrape():
    """Verify that blocked URLs are rejected before any HTTP request."""
    with (
        patch("scraper.socket.gethostbyname", return_value="127.0.0.1"),
        patch("scraper.requests.get") as mock_get,
    ):
        with pytest.raises(URLValidationError):
            scrape_page("http://localhost/admin", ".data")
        mock_get.assert_not_called()
