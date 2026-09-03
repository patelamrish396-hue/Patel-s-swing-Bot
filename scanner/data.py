import yfinance as yf
import pandas as pd

from . import config


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def fetch_intraday(tickers: list) -> dict:
    """
    Download 15m bars (up to 60 days of history) for a batch of tickers.
    Returns {ticker: dataframe} for tickers that returned usable data.
    Silently skips chunks/tickers that fail so one bad symbol doesn't
    kill the whole run.
    """
    out = {}
    for chunk in chunked(tickers, config.CHUNK_SIZE):
        try:
            data = yf.download(
                tickers=chunk,
                period=config.YF_PERIOD,
                interval=config.YF_INTERVAL,
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False,
            )
        except Exception as e:
            print(f"[warn] chunk download failed ({len(chunk)} tickers): {e}")
            continue

        if data is None or data.empty:
            continue

        if len(chunk) == 1:
            t = chunk[0]
            df = data.dropna(how="all")
            if not df.empty:
                out[t] = df
            continue

        for t in chunk:
            try:
                df = data[t].dropna(how="all")
                if not df.empty:
                    out[t] = df
            except (KeyError, TypeError):
                continue

    return out
