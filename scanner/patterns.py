"""
Lightweight, rule-based chart pattern detection.

Important honesty note: these are algorithmic approximations, not true
pattern recognition. A human chartist uses judgment a script can't fully
replicate, so expect some false positives — treat these as "worth a
look," not confirmed setups.

Only bullish/breakout patterns are implemented (no bearish patterns),
to match the rest of the scanner's breakout-only focus.
"""

import numpy as np
import pandas as pd

from . import config


def find_swing_points(df: pd.DataFrame, window: int):
    """
    A bar is a swing high if it's the highest High within +/- `window`
    bars either side of it (and similarly for swing lows). This is a
    simple, standard way to find local turning points.
    """
    highs = df["High"]
    lows = df["Low"]
    span = window * 2 + 1
    swing_high = highs == highs.rolling(span, center=True).max()
    swing_low = lows == lows.rolling(span, center=True).min()
    return swing_high.fillna(False), swing_low.fillna(False)


def detect_ascending_triangle(df: pd.DataFrame) -> dict:
    """
    Flat resistance (swing highs clustered near the same level) + rising
    support (swing lows trending upward). Breakout = latest close above
    the flat resistance.
    """
    recent = df.tail(config.PATTERN_LOOKBACK_BARS)
    if len(recent) < 20:
        return None

    swing_high, swing_low = find_swing_points(recent, config.PATTERN_PIVOT_WINDOW)
    highs = recent.loc[swing_high, "High"]
    lows = recent.loc[swing_low, "Low"]
    if len(highs) < 2 or len(lows) < 2:
        return None

    resistance = highs.mean()
    if resistance <= 0:
        return None
    flatness_pct = (highs.std() / resistance) * 100
    if flatness_pct > config.TRIANGLE_RESISTANCE_TOLERANCE_PCT:
        return None  # highs aren't flat enough to call it a triangle top

    x = np.arange(len(lows))
    slope, _ = np.polyfit(x, lows.values, 1)
    if slope <= 0:
        return None  # support isn't rising

    latest_close = df["Close"].iloc[-1]
    if latest_close > resistance:
        pct_above = (latest_close - resistance) / resistance * 100
        return {
            "type": "TRIANGLE_BREAKOUT",
            "detail": (
                f"Ascending triangle breakout above resistance "
                f"{resistance:.2f} (+{pct_above:.1f}%)"
            ),
            "strength": pct_above,
        }
    return None


def detect_double_bottom(df: pd.DataFrame) -> dict:
    """
    Two swing lows within tolerance of each other, with a bounce (the
    "neckline") between them. Breakout = latest close above the neckline.
    """
    recent = df.tail(config.PATTERN_LOOKBACK_BARS)
    if len(recent) < 20:
        return None

    _, swing_low = find_swing_points(recent, config.PATTERN_PIVOT_WINDOW)
    lows = recent.loc[swing_low, "Low"]
    if len(lows) < 2:
        return None

    last_two = lows.tail(2)
    (idx1, low1), (idx2, low2) = last_two.items()
    if low1 <= 0:
        return None
    diff_pct = abs(low1 - low2) / low1 * 100
    if diff_pct > config.DOUBLE_BOTTOM_TOLERANCE_PCT:
        return None  # the two lows aren't close enough in price

    between = recent.loc[idx1:idx2]
    if between.empty:
        return None
    neckline = between["High"].max()

    latest_close = df["Close"].iloc[-1]
    if latest_close > neckline:
        pct_above = (latest_close - neckline) / neckline * 100
        return {
            "type": "DOUBLE_BOTTOM_BREAKOUT",
            "detail": (
                f"Double bottom breakout above neckline "
                f"{neckline:.2f} (+{pct_above:.1f}%)"
            ),
            "strength": pct_above,
        }
    return None


def detect_range_breakout(df: pd.DataFrame) -> dict:
    """
    A tight trading range (small high-low spread) over recent bars,
    followed by a close above the top of that range.
    """
    lookback = config.RANGE_BREAKOUT_LOOKBACK_BARS
    if len(df) < lookback + 1:
        return None

    # The range itself excludes the current (breakout) bar.
    range_bars = df.iloc[-(lookback + 1):-1]
    range_high = range_bars["High"].max()
    range_low = range_bars["Low"].min()
    if range_low <= 0:
        return None

    range_pct = (range_high - range_low) / range_low * 100
    if range_pct > config.RANGE_BREAKOUT_MAX_RANGE_PCT:
        return None  # too wide to call it a tight consolidation

    latest_close = df["Close"].iloc[-1]
    if latest_close > range_high:
        pct_above = (latest_close - range_high) / range_high * 100
        return {
            "type": "RANGE_BREAKOUT",
            "detail": (
                f"Broke out of a {range_pct:.1f}% range above "
                f"{range_high:.2f} (+{pct_above:.1f}%)"
            ),
            "strength": pct_above,
        }
    return None


def detect_all(df: pd.DataFrame) -> list:
    detectors = [detect_ascending_triangle, detect_double_bottom, detect_range_breakout]
    results = []
    for detector in detectors:
        try:
            sig = detector(df)
        except Exception:
            # A malformed/short dataframe for one ticker shouldn't kill the run.
            sig = None
        if sig:
            results.append(sig)
    return results
