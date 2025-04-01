import yfinance as yf
import numpy as np
from typing import Dict, Any
import json


def get_market_data_for_ticker(ticker: str, event_date: str) -> Dict[str, Any]:
    data = yf.Ticker(ticker)
    hist = data.history(period="3mo", interval="1d")

    if len(hist) < 30:
        raise ValueError(f"Not enough data for ticker {ticker}")

    hist.reset_index(inplace=True)

    try:
        event_row = hist[hist["Date"] == event_date].iloc[0]
    except IndexError:
        raise ValueError(
            f"Event date {event_date} not found in data for {ticker}")

    close = hist["Close"]
    volume = hist["Volume"]
    high = hist["High"]
    low = hist["Low"]

    price_change_5d = (
        (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]) * 100
    rolling_vol_change_5d = (
        (volume.iloc[-1] - volume.iloc[-6]) / volume.iloc[-6]) * 100

    sma_5 = close[-5:].mean()
    sma_20 = close[-20:].mean()

    trend_signal = (
        "bullish" if sma_5 > sma_20 else "bearish" if sma_5 < sma_20 else "neutral"
    )

    support_levels = sorted(low[-20:].nsmallest(3).unique())
    resistance_levels = sorted(high[-20:].nlargest(3).unique(), reverse=True)

    return {
        "ticker": ticker,
        "opening_price": float(event_row["Open"]),
        "current_price": float(close.iloc[-1]),
        "price_change_5d": float(price_change_5d),
        "volume": float(volume.iloc[-1]),
        "rolling_volume_change_5d": float(rolling_vol_change_5d),
        "daily_high": float(high.iloc[-1]),
        "daily_low": float(low.iloc[-1]),
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "trend_signal": trend_signal,
    }


if __name__ == "__main__":
    # Example usage
    ticker = "VWAGY"
    date = "2025-03-27"
    data = get_market_data_for_ticker(ticker, date)
    print(json.dumps(data, indent=4))
