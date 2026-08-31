import os

# --- Universe ---
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

# --- Signal thresholds (override via repo/workflow env vars if you want) ---
VOLUME_SURGE_MULTIPLIER = float(os.environ.get("VOLUME_SURGE_MULTIPLIER", 3.0))
BREAKOUT_LOOKBACK_DAYS = int(os.environ.get("BREAKOUT_LOOKBACK_DAYS", 20))
PRICE_MOVE_THRESHOLD_PCT = float(os.environ.get("PRICE_MOVE_THRESHOLD_PCT", 3.0))

# --- Data fetching ---
YF_PERIOD = "60d"        # max history yfinance allows for 15m bars
YF_INTERVAL = "15m"
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 150))  # tickers per yf.download call

# --- Dedup / cooldown so you don't get spammed every 15 min for the same thing ---
COOLDOWN_MINUTES = int(os.environ.get("COOLDOWN_MINUTES", 60))
STATE_FILE = "state.json"

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
