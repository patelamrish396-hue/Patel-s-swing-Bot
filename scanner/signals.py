import pandas as pd

from . import config
from . import patterns


def analyze(ticker: str, df: pd.DataFrame) -> list:
    """
    Look at the latest 15m bar for `ticker` and decide whether it deserves
    an alert. Returns a list of signal dicts (possibly empty).
    """
    if df is None or len(df) < 10:
        return []

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df["time_of_day"] = df.index.time
    df["date"] = df.index.date

    latest = df.iloc[-1]
    latest_time = df.index[-1]
    today = latest_time.date()

    history = df[df["date"] < today]
    today_bars = df[df["date"] == today]
    if history.empty:
        return []

    if latest["Close"] < config.MIN_STOCK_PRICE:
        return []

    # --- Liquidity filter: skip stocks that don't typically trade much,
    # so a "surge" isn't just noise on a handful of shares ---
    daily_volume = history.groupby("date")["Volume"].sum()
    if daily_volume.empty:
        return []
    avg_daily_volume = daily_volume.mean()
    if avg_daily_volume < config.MIN_AVG_DAILY_VOLUME:
        return []

    signals = []

    # --- Volume surge: this bar's volume vs. the average volume seen in
    # the same time-of-day slot on previous sessions ---
    same_slot = history[history["time_of_day"] == latest_time.time()]
    if not same_slot.empty:
        avg_vol = same_slot["Volume"].mean()
        if avg_vol > 0 and latest["Volume"] >= config.VOLUME_SURGE_MULTIPLIER * avg_vol:
            multiple = latest["Volume"] / avg_vol
            signals.append({
                "type": "VOLUME_SURGE",
                "detail": (
                    f"Vol {int(latest['Volume']):,} vs avg {int(avg_vol):,} "
                    f"({multiple:.1f}x) for this time of day"
                ),
                "strength": multiple,
            })

    # --- Breakout above N-day high ---
    daily_high = history.groupby("date")["High"].max()
    lookback_high = daily_high.tail(config.BREAKOUT_LOOKBACK_DAYS)
    if not lookback_high.empty:
        prior_high = lookback_high.max()
        if latest["Close"] > prior_high:
            pct_above = (latest["Close"] - prior_high) / prior_high * 100
            signals.append({
                "type": "BREAKOUT_HIGH",
                "detail": (
                    f"Price {latest['Close']:.2f} broke above "
                    f"{config.BREAKOUT_LOOKBACK_DAYS}-day high {prior_high:.2f} "
                    f"(+{pct_above:.1f}%)"
                ),
                "strength": pct_above,
            })

    # --- Sharp move within this single 15m bar ---
    if len(today_bars) >= 2:
        prev_close = today_bars["Close"].iloc[-2]
        if prev_close > 0:
            pct = (latest["Close"] - prev_close) / prev_close * 100
            if abs(pct) >= config.PRICE_MOVE_THRESHOLD_PCT:
                direction = "up" if pct > 0 else "down"
                signals.append({
                    "type": "SHARP_MOVE",
                    "detail": (
                        f"Moved {direction} {abs(pct):.1f}% in the last "
                        f"{config.YF_INTERVAL} bar"
                    ),
                    "strength": abs(pct),
                })

    # --- Chart pattern breakouts (triangle, double bottom, range) ---
    signals.extend(patterns.detect_all(df))

    return signals
