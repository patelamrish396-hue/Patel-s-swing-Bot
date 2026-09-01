import io
import requests
import pandas as pd

from . import config


def _nse_session():
    """
    NSE requires a browser-like session (cookies from the homepage) before
    it will serve any of its archive/index CSVs.
    """
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    return session, headers


def get_nifty1000_symbols() -> list:
    """
    Fetch the official Nifty 1000 index constituent list from NSE.
    This is a curated, liquid subset of NSE -- a much lighter universe
    than scanning every listed equity (~2000+).
    """
    session, headers = _nse_session()
    resp = session.get(config.NIFTY1000_LIST_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    symbol_col = "Symbol" if "Symbol" in df.columns else "SYMBOL"
    symbols = df[symbol_col].dropna().astype(str).str.strip().tolist()
    return [f"{s}.NS" for s in symbols]


def get_all_nse_symbols() -> list:
    """Fallback: the full list of every NSE-listed equity symbol."""
    session, headers = _nse_session()
    resp = session.get(config.NSE_EQUITY_LIST_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    symbols = df["SYMBOL"].dropna().astype(str).str.strip().tolist()
    return [f"{s}.NS" for s in symbols]


def get_nse_symbols() -> list:
    """
    Returns the configured stock universe. Defaults to Nifty 1000; falls
    back to the full NSE list if the Nifty 1000 fetch fails, and raises
    if both fail.
    """
    if config.UNIVERSE == "all":
        try:
            return get_all_nse_symbols()
        except Exception as e:
            raise RuntimeError(f"Could not fetch the full NSE symbol list ({e}).")

    try:
        return get_nifty1000_symbols()
    except Exception as e:
        print(f"[warn] Nifty 1000 list fetch failed ({e}), falling back to full NSE list.")
        try:
            return get_all_nse_symbols()
        except Exception as e2:
            raise RuntimeError(
                f"Could not fetch either the Nifty 1000 list ({e}) or the "
                f"full NSE list ({e2}). NSE occasionally blocks automated "
                "requests -- if this persists, save a known-good copy of the "
                "constituent CSV into the repo and load it as a fallback."
            )
