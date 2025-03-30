import json
import logging
import copy
import asyncio
import time

from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
from core.llm_interface import call_gpt
from utils.custom_websearch import get_articles_for_query_async

from pydantic import BaseModel


class WebContent(BaseModel):
    evidence: list[str]
    verdict: str
    commentary: str


class WebContentAnalyzerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("web_content_analyzer")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        search_queries = belief_state.get("search_queries", [])
        existing_results = belief_state.get("websearch_results", [])

        # Create set of existing query signatures
        existing_signatures = {
            self._signature(result) for result in existing_results
        }

        new_results = []
        overall_start = time.time()

        # Build tasks with references to the original blocks
        pending_blocks = [
            block for block in search_queries if not block.get("analyzed")]
        tasks = [self.process_query_block(block, idx)
                 for idx, block in enumerate(pending_blocks)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for block, result in zip(pending_blocks, results):
            if isinstance(result, dict):
                sig = self._signature(result)
                if sig not in existing_signatures:
                    result["analyzed"] = False
                    new_results.append(result)
                    existing_signatures.add(sig)
                block["analyzed"] = True
            elif isinstance(result, Exception):
                logging.warning(
                    f"WebContentAnalyzerAgent: Error processing block: {result}")

        belief_state["websearch_results"] = existing_results + new_results
        self.summary = f"WebContentAnalyzerAgent: Completed analysis for {len(new_results)} new query blocks in {time.time() - overall_start:.2f}s."
        logging.info(self.summary)
        return belief_state

    async def process_query_block(self, query_block, block_index: int):
        block_start = time.time()
        queries = query_block.get("queries", [])
        if not queries:
            return None

        # Step 1: Fetch articles
        fetch_start = time.time()
        article_text_blocks = []
        article_tasks = [get_articles_for_query_async(q) for q in queries]
        all_articles = await asyncio.gather(*article_tasks, return_exceptions=True)
        fetch_end = time.time()

        for result in all_articles:
            if isinstance(result, Exception):
                logging.warning(f"Error fetching articles: {result}")
                continue
            for article in result:
                article_text_blocks.append(
                    f"Title: {article['title']}\nURL: {article['url']}\nContent:\n{article['text']}\n"
                )

        if not article_text_blocks:
            logging.warning(
                f"WebContentAnalyzerAgent: No articles found for query block: {queries}")
            return None

        # Step 2: Prepare prompt
        hypothesis_intro = (
            f"You are evaluating a hypothesis related to the following market event.\n\n"
            f"Ticker: {query_block.get('ticker')}\n"
            f"Event: {query_block.get('event')}\n"
            f"Expected Impact: {query_block.get('expected_impact')}\n"
            f"Rationale: {query_block.get('rationale')}\n\n"
            f"Use the articles below to evaluate whether the evidence supports, refutes, or leaves uncertain the expected impact.\n\n"
        )
        user_prompt = hypothesis_intro + "\n\n".join(article_text_blocks)

        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_prompt.strip()},
        ]

        # Step 3: Call GPT
        gpt_start = time.time()
        try:
            raw_result = await call_gpt(messages=messages, response_format=WebContent)
            structured_result = json.loads(raw_result.model_dump_json())
            gpt_end = time.time()

            enriched_block = copy.deepcopy(query_block)
            enriched_block["web_evidence"] = structured_result.get(
                "evidence", [])
            enriched_block["verdict"] = structured_result.get("verdict", "")
            enriched_block["commentary"] = structured_result.get(
                "commentary", "")
            enriched_block["analyzed"] = True

            total_time = time.time() - block_start
            logging.info(
                f"Query Block {block_index}: Total={total_time:.2f}s | Fetch={fetch_end - fetch_start:.2f}s | GPT={gpt_end - gpt_start:.2f}s"
            )
            return enriched_block

        except Exception as e:
            logging.warning(
                f"WebContentAnalyzerAgent: Failed to analyze query block: {e}")
            return None

    def _signature(self, item: dict) -> str:
        return json.dumps({
            "event": item.get("event"),
            "ticker": item.get("ticker"),
            "queries": sorted(item.get("queries", []))
        }, sort_keys=True)
