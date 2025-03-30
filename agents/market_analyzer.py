import logging
from core.agent_runner import AgentRunner
from core.market_data_interface import get_market_data_for_ticker  # <- You'll build this
from utils.benchmark_mapping import get_sector_benchmark  # <- Optional helper
from pydantic import BaseModel
from typing import List


class MarketSignal(BaseModel):
    ticker: str
    price_change_5d: float
    volume_spike: bool
    technical_trend_signal: str
    benchmark_relative_strength: float
    supports_expected_impact: bool


class MarketDataAnalyzerAgent(AgentRunner):
    def __init__(self):
        super().__init__(prompt=None)  # No GPT call here
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        mapped_assets = belief_state.get("mapped_assets", [])
        market_signals = belief_state.get("market_signals", [])

        for asset in mapped_assets:
            if asset.get("analyzed_market"):
                continue

            ticker = asset.get("ticker")
            expected = asset.get("expected_impact", "uncertain")

            try:
                raw_data = await get_market_data_for_ticker(ticker)
                # optional, if available
                benchmark = await get_sector_benchmark(ticker)

                # Calculate derived metrics
                price_change = raw_data["price_change_5d"]
                volume_spike = raw_data["volume"] > 1.5 * \
                    raw_data["avg_volume_20d"]
                trend = raw_data["trend_signal"]  # must be precomputed
                rel_strength = price_change - \
                    benchmark["price_change_5d"] if benchmark else 0.0

                # Align with expected impact
                impact_alignment = (
                    (expected == "positive" and price_change > 0 and trend == "bullish") or
                    (expected == "negative" and price_change <
                     0 and trend == "bearish")
                )

                signal = MarketSignal(
                    ticker=ticker,
                    price_change_5d=price_change,
                    volume_spike=volume_spike,
                    technical_trend_signal=trend,
                    benchmark_relative_strength=rel_strength,
                    supports_expected_impact=impact_alignment
                )

                market_signals.append(signal.model_dump())
                asset["analyzed_market"] = True

            except Exception as e:
                logging.warning(
                    f"MarketDataAnalyzerAgent: Failed for {ticker}: {e}")
                continue

        belief_state["market_signals"] = market_signals
        self.summary = f"MarketDataAnalyzerAgent: Added market signals for {len(market_signals)} assets."
        return belief_state
