import json
import asyncio
from core.state_manager import load_state, save_state
from core.orchestrator import run_analysis


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

trap_articles = [
    {
        "source": "MarketPulseNews",
        "title": "Investors Cheer as Hong Kong Real Estate 'Poised for a Comeback'",
        "description": "A single analyst notes a 'possible' rebound in certain Hong Kong property sectors, despite ongoing reports of high vacancy and price drops.",
        "url": "https://marketpulsenews.com/articles/hk-recovery-buzz",
        "published_at": "2025-03-25T14:12:00Z",
        "content": "While most indicators continue to reflect strain in Hong Kong's commercial real estate market, one analyst from a mid-tier firm speculates that select segments *could* see a mild rebound if macro conditions align favorably. This contrasts with widespread data showing falling rents, high vacancies, and prolonged recovery timelines.\r\nStory first appeared on hkobserver.com, 2025-03-25 13:55:00."
    },
    {
        "source": "WorldFinanceInsider.com",
        "title": "Hong Kong's Office Market Surges as Big Tech Firms Flood Back, Experts Claim",
        "description": "Despite widespread reports of oversupply, anonymous insiders say major tech firms are aggressively leasing premium office space in Central Hong Kong, reversing vacancy trends.",
        "url": "https://worldfinanceinsider.com/news/hk-office-boom",
        "published_at": "2025-03-27T08:15:42Z",
        "content": "Citing unnamed sources, World Finance Insider reports that major global tech players, including 'at least two FAANG firms,' are finalizing large-scale leases in Hong Kong’s central business district. The outlet claims these moves could slash office vacancy rates by as much as 50% in 2025.\r\nDespite official vacancy data remaining high, the article suggests that current statistics are 'lagging' and do not reflect the sudden boom in demand. Analysts quoted in the piece predict that rents could spike by 30% this year, reversing prior trends.\r\nThe report did not name any specific companies, lease sizes, or official data to support the claims."
    },
    {
        "source": "WorldFinanceInsider.com",
        "title": "Trump Announces 25% Tariffs on Imported Cars and Car Parts",
        "description": "President Trump said on Wednesday that he would impose a 25 percent tariff on cars and car parts that were imported into the United States, a move that is likely to raise prices for American consumers and throw supply chains into disarray as the president seeks to bolster U.S. manufacturing.",
        "url": "https://worldfinanceinsider.com/news/hk-office-boom",
        "published_at": "2025-03-27T08:15:42Z",
        "content": "test article"
    }
]


async def main():
    print("📡 Fetching latest news...")
    # articles = fetch_top_headlines(max_articles=10)
    articles = trap_articles[-1:]  # For testing purposes

    # ✅ Load the shared belief state once
    belief_state = load_state()

    # controller = ConfidenceController(run_analysis)

    for i, article in enumerate(articles):
        input_text = article['title'] + " " + \
            article["description"] + " " + article["published_at"]
        print(f"\n📰 Article {i+1}: {article['title']}")
        print(input_text.strip())

        print("\n🔍 Running agent pipeline...\n")

        await run_analysis(input_text)

        print("\n📌 Done with this article.\n")

    print("🎯 All articles processed. Final belief state saved.\n")


if __name__ == "__main__":
    asyncio.run(main())
