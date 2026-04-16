"""Tests for the telegram_bot module."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from telegram_bot import send_message, delete_message, schedule_delete


@pytest.fixture
def mock_bot():
    """Create a mock Bot instance."""
    bot = MagicMock()
    bot.session = MagicMock()
    bot.session.close = AsyncMock()

    sent_msg = MagicMock()
    sent_msg.message_id = 42
    bot.send_message = AsyncMock(return_value=sent_msg)
    bot.delete_message = AsyncMock()
    return bot


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_sends_and_returns_message_id(self, mock_bot):
        with patch("telegram_bot.Bot", return_value=mock_bot):
            result = await send_message("token", "chat_123", "Hello!")

        assert result == 42
        mock_bot.send_message.assert_called_once_with(chat_id="chat_123", text="Hello!")
        mock_bot.session.close.assert_called_once()


class TestDeleteMessage:
    @pytest.mark.asyncio
    async def test_deletes_message(self, mock_bot):
        with patch("telegram_bot.Bot", return_value=mock_bot):
            await delete_message("token", "chat_123", 42)

        mock_bot.delete_message.assert_called_once_with(chat_id="chat_123", message_id=42)
        mock_bot.session.close.assert_called_once()


class TestScheduleDelete:
    def test_schedules_and_executes_delete(self, mock_bot):
        with patch("telegram_bot.Bot", return_value=mock_bot):
            schedule_delete("token", "chat_123", 42, delay=0)
            # Give the timer thread time to execute
            time.sleep(0.5)

        mock_bot.delete_message.assert_called_once_with(chat_id="chat_123", message_id=42)
