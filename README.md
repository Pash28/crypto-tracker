# CryptoTracker

Production-ready Telegram bot for cryptocurrency prices and price alerts.

## Stack

- Python 3.11+
- aiogram 3.x
- aiohttp + CoinGecko API
- SQLite with aiosqlite
- APScheduler
- Docker and Docker Compose

## MVC Layout

- `app/db` and `app/services`: models for database access, schemas, CoinGecko API access, and alert domain logic.
- `app/bot/keyboards.py`: views for Telegram formatting and UI components.
- `app/bot/handlers`: controllers that receive Telegram commands, call models, and return views.

## Commands

- `/start` - welcome message and command list
- `/price BTC` - current ticker price
- `/alert BTC above 70000` - alert when price rises above target
- `/alert ETH below 2000` - alert when price drops below target
- `/alerts` - list active alerts
- `/delete 12` - delete an alert by ID
- `/top` - top 10 cryptocurrencies by market capitalization

## Local Run

```bash
cp .env.example .env
# edit .env and set BOT_TOKEN
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

## Docker Run

```bash
cp .env.example .env
# edit .env and set BOT_TOKEN
docker compose up --build -d
```

The SQLite database is stored in the `crypto-tracker-data` Docker volume. The alert checker runs every `ALERT_INTERVAL_MINUTES` minutes, defaulting to `5`.
