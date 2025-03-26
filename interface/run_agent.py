import json
import asyncio
from core.confidence_controller import ConfidenceController
from core.state_manager import load_state, save_state
from core.orchestrator import run_analysis
from utils.news_ingestor import fetch_top_headlines, build_news_input_block
from utils.prompt_editor import apply_prompt_patch
from utils.memory_explorer import compare_belief_states, print_diff_summary
from agents.diff_reviewer import review_diff

test_articles = [
    {
    "source": "Biztoc.com",
    "title": "Hong Kong landlords may take 7 to 15 years to end office glut, market experts say",
    "description": "The city has 15 million square feet of excess office space, more than all the current space in the main business district.",
    "url": "https://biztoc.com/x/620eeb1347ab6fca",
    "published_at": "2025-03-24T01:38:25Z",
    "content": "The city has 15 million square feet of excess office space, more than all the current space in the main business district.\r\nThis story appeared on scmp.com, 2025-03-24 01:30:14."
    },
    {
    "source": "The Times of India",
    "title": "US stock futures rise as new tariffs seen targeted",
    "description": "S&P 500 futures rose, Japanese shares fluctuated between gains and losses in early trade, while Australia’s market fell. The dollar was softer against major peers, while the 10-year US Treasury yield advanced.",
    "url": "https://economictimes.indiatimes.com/markets/stocks/news/us-stock-futures-rise-as-new-tariffs-seen-targeted/articleshow/119399818.cms",
    "published_at": "2025-03-24T01:13:33Z",
    "content": "US stock-index futures climbed in early Asia trading on signs that the next round of President Donald Trumps trade tariffs could be more measured than had previously been suggested. S&amp;P 500 futur… [+2410 chars]"
  },
  {
    "source": "BusinessLine",
    "title": "Share Market Highlights: Sensex jumps 1.4%, Nifty gains 1.32% as foreign buying lifts markets",
    "description": "Sensex, Nifty updates on 24 March 2025: The benchmark BSE Sensex jumped 1.4% to 77,984.38, while the NSE Nifty gained 1.32% to 23,658, driven by renewed foreign investor interest and bargain hunting. Banking and IT stocks led the rally. The Indian rupee surge…",
    "url": "https://www.thehindubusinessline.com/markets/stock-market-highlights-24-march-2025/article69365394.ece",
    "published_at": "2025-03-24T01:10:00Z",
    "content": "<li></li>\r\nMarch 24, 2025 16:03The live blog is now closed.\r\n<li></li>\r\nMarch 24, 2025 15:51Stock market live updates today: IndusInd Bank ends 2% lower, Yes Bank in green \r\nIndusInd Bank Stocks &amp… [+81372 chars]"
  },
  {
    "source": "BusinessLine",
    "title": "Stock Market Live Updates 24 March 2025: Stock to buy today: Indian Bank (₹547.65) – BUY",
    "description": "Sensex, Nifty, Share Price LIVE: The short-term outlook is bullish for Indian Bank. The stock has been trading in a wide range for more than a year now. The trading range has been ₹467-₹626 since February last year.",
    "url": "https://www.thehindubusinessline.com/markets/share-market-nifty-sensex-live-updates-24-march-2025/article69365394.ece",
    "published_at": "2025-03-24T01:10:00Z",
    "content": "LAST TRADING DAY FOR\r\nFY 2024-25 is 27th MARCH 2025\r\nTrades Done (ALL Segments) \r\non 27-Mar-2025 Will be Settled on \r\n28-Mar-2025 Friday FY 24-25\r\nTrades Done (ALL Segments) \r\non 28-Mar-2025 Will be … [+2987 chars]"
  },
  {
    "source": "pymnts.com",
    "title": "Small Business Insurer Next Sold to ERGO for $2.6 Billion",
    "description": "German insurance giant ERGO is expanding into the U.S. after acquiring Next Insurance. The $2.6 billion deal, announced in a news release Friday (March 21), will allow ERGO — owned by Munich Re — to target the small business community in the U.S., comprising …",
    "url": "https://www.pymnts.com/acquisitions/2025/small-business-insurer-next-sold-to-ergo-for-2-6-billion/",
    "published_at": "2025-03-24T01:08:55Z",
    "content": "German insurance giant ERGO is expanding into the U.S. after acquiring Next Insurance.\r\nThe $2.6 billion deal, announced in a news release Friday (March 21), will allow ERGO owned by Munich Re to tar… [+2438 chars]"
  }
]

async def main():
    print("📡 Fetching latest news...")
    # articles = fetch_top_headlines(max_articles=10)
    articles = test_articles[:2]  # For testing purposes
    
    # ✅ Load the shared belief state once
    belief_state = load_state()

    controller = ConfidenceController(run_analysis)

    for i, article in enumerate(articles):
        input_text = article['title'] + " " + article["description"] 
        print(f"\n📰 Article {i+1}: {article['title']}")
        print(input_text.strip())

        print("\n🔍 Running agent pipeline...\n")
        
        # 🔄 Pass current belief state in — and keep the updated one
        final_state = await controller.run_with_autotune(input_text, belief_state)
        belief_state = final_state  # stack it

        # ✅ Save after each run
        save_state(final_state)

        print("\n🔮 Scenarios:")
        for s in final_state.get("scenarios", []):
            print(f"- {s['label'].title()}: {s['summary']} ({int(s['probability']*100)}%)")

        # Apply patch if needed
        suggestion = final_state.get("prompt_tuner_suggestions", "")
        if suggestion:
            print("\n🛠️ Applying prompt tuner patch...")
            apply_prompt_patch(suggestion)

        # Memory diff
        diffs = compare_belief_states(belief_state, final_state)
        if diffs:
            print("\n📊 Memory Diff Summary:")
            print_diff_summary(diffs)

            diff_text = "\n\n".join(f"=== {k.upper()} ===\n{v}" for k, v in diffs.items())
            review = review_diff(diff_text)
            final_state["diff_review"] = review

            print("\n🧠 GPT Diff Review:")
            print(review)

        print("\n📌 Done with this article.\n")

    print("🎯 All articles processed. Final belief state saved.\n")


if __name__ == "__main__":
    asyncio.run(main())
