"""Streamlit UI for Simple Scraping + Telegram Bot Automation."""

import asyncio
import logging
import os
import time
from datetime import datetime

# Configure file logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from cleaner import clean_data, export_data
from scraper import URLValidationError, scrape_page
from telegram_bot import schedule_delete, send_message

load_dotenv()

st.set_page_config(page_title="Simple Scraping + Telegram Bot Automation (POC)", layout="wide")
st.title("Simple Scraping + Telegram Bot Automation (POC)")

# Load Telegram config from Streamlit secrets (cloud) or environment (local)
def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, "")


TELEGRAM_TOKEN = _get_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = _get_secret("TELEGRAM_CHAT_ID")
TELEGRAM_CHANNEL_URL = _get_secret("TELEGRAM_CHANNEL_URL")

# Scraping examples
EXAMPLES = {
    "Quotes to Scrape": ("http://quotes.toscrape.com", ".quote .text"),
    "Hacker News titles": ("https://news.ycombinator.com", ".titleline > a"),
    "Books to Scrape": ("http://books.toscrape.com", ".product_pod h3 a"),
}

# Initialize session state
if "logs" not in st.session_state:
    st.session_state.logs = []
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = []


def _add_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")


def _format_message(data: list[dict]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [item.get("text", str(item)) for item in data]
    return f"Scraped data ({timestamp}):\n\n" + "\n".join(f"• {line}" for line in lines)


def _send_to_telegram(message: str) -> None:
    """Send a message to Telegram and schedule auto-delete."""
    msg_id = asyncio.run(send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message))
    schedule_delete(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg_id, delay=60)


def _do_scrape(url: str, selector: str) -> list[dict]:
    """Scrape and clean data, logging the result."""
    raw = scrape_page(url, selector)
    cleaned = clean_data(raw)
    _add_log(f"Scraped {len(cleaned)} items from {url}")
    return cleaned


# --- Sidebar ---
with st.sidebar:
    st.header("Scraper Configuration")

    example = st.selectbox("Examples", ["Custom"] + list(EXAMPLES.keys()))
    if example != "Custom":
        default_url, default_selector = EXAMPLES[example]
    else:
        default_url, default_selector = "http://quotes.toscrape.com", ".quote .text"

    url = st.text_input("Target URL", value=default_url)
    selector = st.text_input("CSS Selector", value=default_selector)

    with st.expander("How do CSS selectors work?"):
        st.markdown("""
A CSS selector tells the scraper **which elements to extract** from the page.

| Selector | Matches |
|----------|---------|
| `p` | All `<p>` elements |
| `.quote` | Elements with `class="quote"` |
| `#title` | Element with `id="title"` |
| `.quote .text` | `.text` **inside** `.quote` |
| `h3 a` | Links inside `<h3>` headings |
| `.titleline > a` | Links that are **direct children** of `.titleline` |

**How the examples work:**
- **Quotes to Scrape** — `.quote .text` grabs the quote text inside each quote block
- **Hacker News** — `.titleline > a` grabs the link in each title row
- **Books to Scrape** — `.product_pod h3 a` grabs the book title link in each card

**To find selectors for any site:** right-click an element in Chrome → Inspect → note the class names and nesting.
""")

    output_format = st.selectbox("Output Format", ["JSON", "CSV"])

    if st.button("Scrape Now"):
        try:
            st.session_state.scraped_data = _do_scrape(url, selector)
        except URLValidationError as e:
            st.session_state.scraped_data = []
            _add_log(f"ERROR: {e}")
        except Exception as e:
            st.session_state.scraped_data = []
            _add_log(f"ERROR: Could not scrape — {e}")

    # --- Scheduling Controls ---
    st.divider()
    st.header("Auto-Scraping")
    telegram_ready = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)
    interval = st.slider("Interval (seconds)", min_value=30, max_value=120, value=60)
    st.caption("Runs 3 times, then stops. Scrapes and sends to Telegram each run.")

    if not telegram_ready:
        st.caption("Configure Telegram env vars to enable auto-scraping.")

    start_scheduler = st.button("Start Auto-Scraping", disabled=not telegram_ready)

# --- Main Panel ---
st.subheader("Scraped Data")

# Run scheduler in the main panel area so the countdown is visible
if start_scheduler:
    max_runs = 3
    status_container = st.empty()
    for run in range(1, max_runs + 1):
        # Countdown
        for remaining in range(interval, 0, -1) if run > 1 else [0]:
            if remaining > 0:
                status_container.info(f"**Run {run}/{max_runs}** — Scraping and sending in **{remaining}** seconds...")
                time.sleep(1)

        status_container.info(f"**Run {run}/{max_runs}** — Scraping now...")
        try:
            data = _do_scrape(url, selector)
            st.session_state.scraped_data = data
            if data:
                message = _format_message(data)
                _send_to_telegram(message)
                _add_log(f"Sent {len(data)} items to Telegram (auto-deletes in 60s)")
                status_container.success(f"**Run {run}/{max_runs}** — Sent {len(data)} items to Telegram!")
            else:
                status_container.warning(f"**Run {run}/{max_runs}** — No data found.")
        except Exception as e:
            _add_log(f"ERROR: Auto-scrape failed — {e}")
            status_container.error(f"**Run {run}/{max_runs}** — Error: {e}")

        if run < max_runs:
            time.sleep(1)  # Brief pause before countdown starts

    status_container.success(f"Auto-scraping complete ({max_runs} runs). Messages will auto-delete in 60 seconds.")
    _add_log("Auto-scraping complete")

if st.session_state.scraped_data:
    df = pd.DataFrame(st.session_state.scraped_data)
    st.dataframe(df, width="stretch")

    exported = export_data(st.session_state.scraped_data, output_format)
    file_ext = "json" if output_format == "JSON" else "csv"
    mime = "application/json" if output_format == "JSON" else "text/csv"
    st.download_button(
        f"Download {output_format}",
        data=exported,
        file_name=f"scraped_data.{file_ext}",
        mime=mime,
    )

    # --- Telegram Integration ---
    st.divider()
    if telegram_ready:
        if st.button("Send to Telegram"):
            message = _format_message(st.session_state.scraped_data)
            try:
                _send_to_telegram(message)
                _add_log(f"Sent {len(st.session_state.scraped_data)} items to Telegram (auto-deletes in 60s)")
                st.success("Sent to Telegram! Message will auto-delete in 60 seconds.")
                if TELEGRAM_CHANNEL_URL:
                    st.markdown(f"[View on Telegram]({TELEGRAM_CHANNEL_URL})")
            except Exception as e:
                _add_log(f"ERROR: Telegram send failed — {e}")
                st.error(f"Telegram send failed: {e}")
    else:
        st.warning("Telegram not configured. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in environment.")
else:
    if not start_scheduler:
        st.info("No data yet. Configure the scraper in the sidebar and click 'Scrape Now'.")

# --- Logs Panel ---
with st.expander("Logs", expanded=False):
    if st.session_state.logs:
        for log in reversed(st.session_state.logs):
            st.text(log)
    else:
        st.text("No activity yet.")
