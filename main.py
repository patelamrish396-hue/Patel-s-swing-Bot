import datetime
import os
import time
import pandas as pd
import pandas_ta_classic as ta
import requests
import yfinance as yf

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"
)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

# Watchlist to monitor
WATCHLIST = [
    "RELIANCE.NS",
    "TATAMOTORS.NS",
    "INFY.NS",
    "TCS.NS",
    "HDFCBANK.NS",
]

# Indicator parameters
LOOKBACK_PERIODS = 20  # Resistance lookback period
VOLUME_MULTIPLIER = 1.5  # Required volume spike factor
CONSOLIDATION_THRESHOLD = (
    0.06  # 6% max price spread during pattern consolidation
)
INTERVAL = "15m"  # Candle timeframe
FETCH_PERIOD = "5d"

# Prevent duplicate alerts during the same trading session
alerted_symbols = set()
# =======================================================


def send_telegram_message(message: str):
  """Sends formatted Markdown alerts to Telegram."""
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("[ERROR] Telegram credentials missing!")
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(url, data=payload, timeout=10)
    if response.status_code == 200:
      print(f"[SUCCESS] Telegram notification delivered.")
    else:
      print(f"[ERROR] Delivery failed: {response.text}")
  except Exception as e:
    print(f"[EXCEPT] Request exception: {e}")


def is_market_open() -> bool:
  """Checks if Indian Stock Market (NSE) is in active trading hours (Mon-Fri, 9:15 AM - 3:30 PM IST)."""
  now = datetime.datetime.now()
  if now.weekday() >= 5:  # Weekend check
    return False

  market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
  market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
  return market_start <= now <= market_end


def check_breakouts():
  """Scans watchlist for Chart Pattern Consolidation + Volume Surge + Price Resistance Breakouts."""
  print(
      f"\n--- Running Scan at"
      f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---"
  )

  for symbol in WATCHLIST:
    if symbol in alerted_symbols:
      continue

    try:
      df = yf.download(
          symbol, period=FETCH_PERIOD, interval=INTERVAL, progress=False
      )

      if df.empty or len(df) < (LOOKBACK_PERIODS + 1):
        print(f"[{symbol}] Insufficient candle history.")
        continue

      # MultiIndex adjustment for recent yfinance versions
      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      # 1. Volume Moving Average Calculation
      df["Vol_Avg"] = ta.sma(df["Volume"], length=LOOKBACK_PERIODS)
      df = df.dropna(subset=["Vol_Avg"])

      if len(df) < 2:
        continue

      # Extract price metrics
      latest_close = float(df["Close"].iloc[-1])
      latest_vol = float(df["Volume"].iloc[-1])
      avg_vol = float(df["Vol_Avg"].iloc[-1])

      # Prior 20-candle high & low (excluding current active candle)
      prior_high = float(df["High"].iloc[-(LOOKBACK_PERIODS + 1) : -1].max())
      prior_low = float(df["Low"].iloc[-(LOOKBACK_PERIODS + 1) : -1].min())

      # Calculate consolidation contraction range (High - Low) / Low
      consolidation_range = (
          (prior_high - prior_low) / prior_low if prior_low > 0 else 1.0
      )
      vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 0.0

      print(
          f"[{symbol}] Close: ₹{latest_close:.2f} | 20-High: ₹{prior_high:.2f} |"
          f" Pattern Range: {consolidation_range*100:.1f}% | Vol:"
          f" {vol_ratio:.2f}x"
      )

      # --- BREAKOUT & PATTERN CONDITIONS ---
      # Condition A: Price breaks above the consolidation pattern resistance line
      is_price_breakout = latest_close > prior_high

      # Condition B: High volume surge confirms institutional participation
      is_volume_confirmed = latest_vol >= (VOLUME_MULTIPLIER * avg_vol)

      # Condition C: Pattern compression (price range was tightly squeezed before breakout)
      is_pattern_tight = consolidation_range <= CONSOLIDATION_THRESHOLD

      if is_price_breakout and is_volume_confirmed and is_pattern_tight:
        clean_ticker = symbol.replace(".NS", "")
        alert_msg = (
            f"📐 *CHART PATTERN BREAKOUT: NSE:{clean_ticker}*\n\n"
            f"📈 *Breakout Price:* ₹{latest_close:.2f}\n"
            f"🎯 *Pattern Resistance:* ₹{prior_high:.2f}\n"
            f"📦 *Tight Consolidation Range:* {consolidation_range*100:.2f}%\n"
            f"🔥 *Volume Surge:* {vol_ratio:.2f}x (Req: >={VOLUME_MULTIPLIER}x)\n"
            f"🕒 *Timestamp:* {datetime.datetime.now().strftime('%H:%M:%S IST')}\n\n"
            f"💡 *Setup:* Narrow Range Consolidation Pattern + Volume Explosion"
        )
        send_telegram_message(alert_msg)
        alerted_symbols.add(symbol)

    except Exception as e:
      print(f"[{symbol}] Error parsing breakout: {e}")


if __name__ == "__main__":
  print("Chart Pattern & Breakout Bot initialized...")

  while True:
    if is_market_open():
      check_breakouts()
    else:
      print(
          f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Market is CLOSED."
          " Waiting..."
      )

    # 60-second polling sleep interval
    time.sleep(60)
