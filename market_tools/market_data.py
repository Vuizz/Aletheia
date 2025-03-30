import yfinance as yf
import numpy as np
from typing import Dict


def get_market_data_for_ticker(ticker: str) -> Dict:
    data = yf.Ticker(ticker)
    hist = data.history(period="1mo", interval="1d")

    if len(hist) < 10:
        raise ValueError(f"Not enough data for ticker {ticker}")

    close = hist["Close"]
    volume = hist["Volume"]

    price_change_5d = (
        (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]) * 100

    avg_volume_20d = volume[-20:].mean()
    latest_volume = volume.iloc[-1]

    # Simple trend logic: 5-day SMA vs 20-day SMA
    sma_5 = close[-5:].mean()
    sma_20 = close[-20:].mean()

    if sma_5 > sma_20:
        trend_signal = "bullish"
    elif sma_5 < sma_20:
        trend_signal = "bearish"
    else:
        trend_signal = "neutral"

    return {
        "price_change_5d": float(price_change_5d),
        "volume": float(latest_volume),
        "avg_volume_20d": float(avg_volume_20d),
        "trend_signal": trend_signal
    }


if __name__ == "__main__":
    # Example usage
    ticker = "VWAGY"
    data = get_market_data_for_ticker(ticker)
    print(data)
