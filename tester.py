import asyncio
from agents.position_evaluator import PositionEvaluatorAgent

from agents.position_planner import PositionPlannerAgent

import time
import json


if __name__ == "__main__":
    # Example usage
    start = time.time()
    agent = PositionEvaluatorAgent()
    example_belief_state = {
        "websearch_results": [
            {
                "event": "President Trump announced a 25% tariff on imported cars and car parts.",
                "type": "policy",
                "date": "2025-03-27",
                "analyzed": False,
                "entities": [
                    "President Trump",
                    "automakers",
                    "importers"
                ],
                "regions": [
                    "United States"
                ],
                "sectors": [
                    "Automotive"
                ],
                "themes": [
                    "trade policy",
                    "tariffs"
                ],
                "notable_entities": [
                    "General Motors",
                    "Ford",
                    "Toyota",
                    "Volkswagen",
                    "Fiat Chrysler Automobiles"
                ],
                "market_statistics": [
                    "U.S. auto sales fell 3.5% year-over-year in Q1 2025",
                    "The average price of new cars in the U.S. reached $45,000 in early 2025",
                    "Import share of the U.S. automotive market was 30% in Q4 2024"
                ],
                "regional_context": "The U.S. automotive industry is grappling with supply chain disruptions and inflationary pressures. President Trump's tariff announcement aims to protect domestic manufacturing but risks escalating trade tensions, particularly with key trading partners like Japan and Germany.",
                "branch": "The announcement of a 25% tariff on imported cars may lead to increased production costs for automakers reliant on foreign parts, potentially reducing their profit margins.",
                "target_entities": [
                    "General Motors"
                ],
                "expected_impact": "negative",
                "affected_regions": [
                    "United States"
                ],
                "sector": "Automotive",
                "parent_event": "President Trump announced a 25% tariff on imported cars and car parts.",
                "queries": [
                    "What has been the impact of the 25% tariff on the production costs for General Motors and other automakers since March 2025?",
                    "How have profit margins for U.S. automakers like Ford and General Motors changed in the first half of 2025 in response to the new tariffs?",
                    "What are the current sales trends for imported cars compared to domestic cars in the U.S. automotive market since the tariff announcement?",
                    "What commentary have automotive industry analysts provided regarding the long-term effects of the 25% tariff on profit margins and production strategies?",
                    "Have there been any shifts in supply chain sourcing for automakers in the U.S. following the implementation of the 25% tariff on imported cars?"
                ],
                "web_evidence": [
                    "General Motors and other automakers are expected to face significant cost increases due to the 25% tariffs on imported auto parts, which could lead to reduced profit margins.",
                    "Analysts indicate that the auto tariffs could push up the prices of vehicles, making them less affordable for consumers and potentially reducing sales.",
                    "Shares of General Motors fell sharply following the announcement of the tariffs, indicating investor concerns about the impact on profitability.",
                    "The tariffs could disrupt the automotive market and create affordability challenges for consumers, which may lead to a trade-down effect to used vehicles.",
                    "Industry experts warn that the tariffs will likely lead to a restructured auto market favoring domestic production but at a cost to consumer pricing and company profit margins."
                ],
                "verdict": "supported",
                "commentary": "The evidence strongly supports the hypothesis that the 25% tariff on imported cars will increase production costs for automakers like General Motors, negatively impacting their profit margins. The anticipated increase in vehicle prices and the drop in stock values further reinforce the negative outlook for the automotive sector."
            }
        ]
    }
    result = asyncio.run(agent.run(example_belief_state))
    end = time.time()

    print("Result:", json.dumps(result['position_candidates'], indent=2))
    print(f"Execution time: {end - start:.2f} seconds")

    start2 = time.time()
    agent2 = PositionPlannerAgent()

    result2 = asyncio.run(agent2.run(result))

    end2 = time.time()
    print("Result2:", json.dumps(result2['confirmed_positions'], indent=2))
    print(f"Execution time2: {end2 - start2:.2f} seconds")
