import asyncio
from agents.webcontent_analyzer import WebContentAnalyzerAgent
import time

if __name__ == "__main__":
    # Example usage
    start = time.time()
    agent = WebContentAnalyzerAgent()
    example_belief_state = {
        "search_queries": [
            {
                "ticker": "F",
                "expected_impact": "positive",
                "confidence": 0.8,
                "rationale": "Ford Motor Company is likely to benefit from tariffs that make imported cars more expensive, potentially boosting domestic sales.",
                "event": "President Trump announces 25% tariffs on imported cars and car parts to bolster U.S. manufacturing.",
                "date": "2025-03-27",
                "analyzed": False,
                "queries": [
                    "How did Ford's stock price change in the month following the March 2025 tariffs announcement?",
                    "What is the exposure of Ford's supply chain to imported car parts affected by the 2025 tariffs?",
                    "Have analysts revised their earnings guidance for Ford post-March 2025 tariffs announcement?",
                    "How did Ford's domestic competitors respond to the March 2025 tariffs on imports?",
                    "What historical impact have similar tariffs had on Ford's market share in previous administrations?"
                ]
            },
            {
                "ticker": "GM",
                "expected_impact": "positive",
                "confidence": 0.8,
                "rationale": "General Motors could see increased demand for its domestically produced vehicles as tariffs make imports more costly.",
                "event": "President Trump announces 25% tariffs on imported cars and car parts to bolster U.S. manufacturing.",
                "date": "2025-03-27",
                "analyzed": False,
                "queries": [
                    "Impact of 25% tariffs on imported cars on General Motors' market share in Q2 2025",
                    "Analysis of General Motors' supply chain vulnerability to increased tariffs as of March 2025",
                    "How have past U.S. tariffs on car imports affected domestic car manufacturers like GM?",
                    "Analyst revisions on GM's earnings forecasts following March 2025 tariff announcement",
                    "Effect of tariff increases on General Motors' cost structure and pricing strategy in 2025"
                ]
            }
        ]
    }
    asyncio.run(agent.run(example_belief_state))
    end = time.time()
    print(f"Execution time: {end - start:.2f} seconds")
