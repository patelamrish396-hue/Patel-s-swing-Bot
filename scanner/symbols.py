import io
import requests
import pandas as pd

from . import config


def get_nse_symbols() -> list:
    """
    Fetch the full list of NSE-listed equity symbols.
    NSE requires a browser-like session (cookies from the homepage) before
    it will serve the archives CSV, so we visit the homepage first.
    """
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        resp = session.get(config.NSE_EQUITY_LIST_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        symbols = df["SYMBOL"].dropna().astype(str).str.strip().tolist()
        return [f"{s}.NS" for s in symbols]
    except Exception as e:
        raise RuntimeError(
            f"Could not fetch the NSE symbol list ({e}). NSE occasionally "
            "blocks automated requests. If this keeps happening, save a "
            "known-good copy of EQUITY_L.csv into the repo and load it as "
            "a fallback here."
        )
