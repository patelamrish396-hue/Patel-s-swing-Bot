import pandas as pd

from . import config


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

    signals = []

    # --- Volume surge: this bar's volume vs. the average volume seen in
    # the same time-of-day slot on previous sessions ---
    same_slot = history[history["time_of_day"] == latest_time.time()]
    if not same_slot.empty:
        avg_vol = same_slot["Volume"].mean()
        if avg_vol > 0 and latest["Volume"] >= config.VOLUME_SURGE_MULTIPLIER * avg_vol:
            signals.append({
                "type": "VOLUME_SURGE",
                "detail": (
                    f"Vol {int(latest['Volume']):,} vs avg {int(avg_vol):,} "
                    f"({latest['Volume'] / avg_vol:.1f}x) for this time of day"
                ),
            })

    # --- Breakout above N-day high ---
    daily_high = history.groupby("date")["High"].max()
    lookback_high = daily_high.tail(config.BREAKOUT_LOOKBACK_DAYS)
    if not lookback_high.empty:
        prior_high = lookback_high.max()
        if latest["Close"] > prior_high:
            signals.append({
                "type": "BREAKOUT_HIGH",
                "detail": (
                    f"Price {latest['Close']:.2f} broke above "
                    f"{config.BREAKOUT_LOOKBACK_DAYS}-day high {prior_high:.2f}"
                ),
            })

    # --- Breakdown below N-day low ---
    daily_low = history.groupby("date")["Low"].min()
    lookback_low = daily_low.tail(config.BREAKOUT_LOOKBACK_DAYS)
    if not lookback_low.empty:
        prior_low = lookback_low.min()
        if latest["Close"] < prior_low:
            signals.append({
                "type": "BREAKDOWN_LOW",
                "detail": (
                    f"Price {latest['Close']:.2f} broke below "
                    f"{config.BREAKOUT_LOOKBACK_DAYS}-day low {prior_low:.2f}"
                ),
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
                })

    return signals
