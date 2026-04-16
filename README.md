# Simple Scraping + Telegram Bot Automation (MVP)

A lightweight Python automation tool that scrapes websites, cleans the data, and sends updates via Telegram — all controlled through a Streamlit UI.

## Features

- **Web scraping** — Enter any URL + CSS selector to extract data
- **Data cleaning** — Automatic deduplication and whitespace trimming
- **Export** — Download results as JSON or CSV
- **Telegram integration** — Send scraped data to a Telegram channel with one click
- **Auto-delete** — Telegram messages self-destruct after 60 seconds (for demo privacy)
- **Auto-scraping** — Schedule recurring scrapes (30-120s interval, max 3 runs)
- **SSRF protection** — Blocks requests to private/internal addresses

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure Telegram (optional, for bot features)

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts to create a bot
3. Copy the bot token
4. Create a **public** Telegram channel and add the bot as admin
5. Get the chat ID by sending a message in the channel, then visiting:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Create a `.env` file:

```bash
cp .env.example .env
```

Fill in your values:

```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_CHANNEL_URL=https://t.me/your_channel_name
```

### 3. Run the app

```bash
uv run streamlit run app.py
```

## Usage

1. Enter a target URL and CSS selector in the sidebar
2. Click **Scrape Now** to extract data
3. View results in the table, download as JSON/CSV
4. Click **Send to Telegram** to push data to your channel
5. Use **Auto-Scraping** to schedule recurring scrapes

## Running tests

```bash
uv run pytest
```

## Project structure

```
app.py              — Streamlit UI
scraper.py          — Web scraper with URL validation
cleaner.py          — Data cleaning and export
telegram_bot.py     — Telegram bot with auto-delete
scheduler.py        — AsyncIO scheduler with iteration limits
tests/              — Unit and E2E tests
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Target channel/chat ID |
| `TELEGRAM_CHANNEL_URL` | Public channel URL (for "View on Telegram" link) |

## Deployment (Streamlit Cloud)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the main file
4. Add Telegram env vars in the Streamlit Cloud secrets panel
