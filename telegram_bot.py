"""Telegram bot integration with auto-delete support."""

import asyncio
import logging
import threading

from aiogram import Bot

logger = logging.getLogger(__name__)


async def send_message(bot_token: str, chat_id: str, text: str) -> int:
    """Send a message to a Telegram chat. Returns the message ID."""
    bot = Bot(token=bot_token)
    try:
        result = await bot.send_message(chat_id=chat_id, text=text)
        return result.message_id
    finally:
        await bot.session.close()


async def delete_message(bot_token: str, chat_id: str, message_id: int) -> None:
    """Delete a message from a Telegram chat."""
    bot = Bot(token=bot_token)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    finally:
        await bot.session.close()


def _delete_in_thread(bot_token: str, chat_id: str, message_id: int) -> None:
    """Run delete_message in a new event loop (called from a Timer thread)."""
    try:
        asyncio.run(delete_message(bot_token, chat_id, message_id))
        logger.info("Auto-deleted message %d", message_id)
    except Exception:
        logger.warning("Could not delete message %d (may already be gone)", message_id)


def schedule_delete(bot_token: str, chat_id: str, message_id: int, delay: int = 60) -> None:
    """Schedule message deletion after `delay` seconds using a background thread."""
    timer = threading.Timer(delay, _delete_in_thread, args=(bot_token, chat_id, message_id))
    timer.daemon = True
    timer.start()
