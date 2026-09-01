import os

# --- Universe ---
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

# --- Signal thresholds (override via repo/workflow env vars if you want) ---
VOLUME_SURGE_MULTIPLIER = float(os.environ.get("VOLUME_SURGE_MULTIPLIER", 12.0))
BREAKOUT_LOOKBACK_DAYS = int(os.environ.get("BREAKOUT_LOOKBACK_DAYS", 20))
PRICE_MOVE_THRESHOLD_PCT = float(os.environ.get("PRICE_MOVE_THRESHOLD_PCT", 3.0))

# --- List-length controls ---
# Skip low-priced/illiquid stocks that tend to spike on tiny volume and
# flood the alert list with noise.
MIN_STOCK_PRICE = float(os.environ.get("MIN_STOCK_PRICE", 20))
# Skip stocks whose typical daily trading volume is below this — a "12x
# surge" on a stock that normally trades 500 shares/day isn't meaningful.
MIN_AVG_DAILY_VOLUME = float(os.environ.get("MIN_AVG_DAILY_VOLUME", 2500))
# Hard cap on how many alerts get sent per run, keeping only the
# strongest ones (highest volume multiple / furthest breakout / biggest move).
TOP_N_PER_RUN = int(os.environ.get("TOP_N_PER_RUN", 15))

# --- Chart pattern detection (approximate, rule-based) ---
PATTERN_LOOKBACK_BARS = int(os.environ.get("PATTERN_LOOKBACK_BARS", 120))
PATTERN_PIVOT_WINDOW = int(os.environ.get("PATTERN_PIVOT_WINDOW", 3))
TRIANGLE_RESISTANCE_TOLERANCE_PCT = float(os.environ.get("TRIANGLE_RESISTANCE_TOLERANCE_PCT", 1.0))
DOUBLE_BOTTOM_TOLERANCE_PCT = float(os.environ.get("DOUBLE_BOTTOM_TOLERANCE_PCT", 2.0))
RANGE_BREAKOUT_LOOKBACK_BARS = int(os.environ.get("RANGE_BREAKOUT_LOOKBACK_BARS", 40))
RANGE_BREAKOUT_MAX_RANGE_PCT = float(os.environ.get("RANGE_BREAKOUT_MAX_RANGE_PCT", 6.0))

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
