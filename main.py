import os
import requests
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from concurrent.futures import ThreadPoolExecutor, as_completed

# Download VADER Lexicon for Sentiment Analysis
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram tokens not configured!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def get_all_nse_symbols():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        df = pd.read_csv(url)
        return [f"{symbol}.NS" for symbol in df['Symbol'].dropna().tolist()]
    except Exception as e:
        print(f"Fallback list used: {e}")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]

def get_news_sentiment(ticker_symbol: str):
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        if not news:
            return 0.0, "No recent news"

        compound_scores = []
        top_headline = ""

        for idx, article in enumerate(news[:5]):
            title = article.get('title', '')
            if idx == 0:
                top_headline = title
            score = sia.polarity_scores(title)['compound']
            compound_scores.append(score)

        avg_sentiment = sum(compound_scores) / len(compound_scores) if compound_scores else 0.0
        return avg_sentiment, top_headline
    except Exception:
        return 0.0, "N/A"

def scan_single_stock(ticker: str):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['Vol_Avg'] = ta.sma(df['Volume'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        current_price = float(latest['Close'])
        prev_price = float(previous['Close'])
        sma_20 = float(latest['SMA_20'])
        current_vol = float(latest['Volume'])
        avg_vol = float(latest['Vol_Avg'])
        rsi = float(latest['RSI'])

        is_breakout = (prev_price <= sma_20) and (current_price > sma_20)
        is_high_volume = current_vol >= (1.5 * avg_vol)
        is_good_rsi = 50 <= rsi <= 70

        if is_breakout and is_high_volume and is_good_rsi:
            sentiment_score, headline = get_news_sentiment(ticker)
            
            if sentiment_score >= 0.05:
                clean_ticker = ticker.replace('.NS', '')
                msg = (
                    f"🚀 *BULLISH SWING ALERT: NSE:{clean_ticker}*\n\n"
                    f"📈 *Price:* ₹{current_price:.2f}\n"
                    f"📊 *20-Day SMA:* ₹{sma_20:.2f}\n"
                    f"🔥 *RSI (14):* {rsi:.1f}\n"
                    f"⚡ *Volume:* {int(current_vol):,} (Spike vs 20D Avg)\n"
                    f"🧠 *News Sentiment:* +{sentiment_score:.2f} (Positive)\n"
                    f"📰 *Headline:* _{headline}_\n\n"
                    f"💡 *Trigger:* 20-SMA Breakout + Vol Surge + Positive News"
                )
                send_telegram_alert(msg)
                print(f"✅ ALERT SENT: {ticker}")
    except Exception:
        pass

def main():
    symbols = get_all_nse_symbols()
    print(f"Scanning {len(symbols)} NSE stocks...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(scan_single_stock, sym) for sym in symbols]
        for future in as_completed(futures):
            future.result()

if __name__ == "__main__":
    main()
