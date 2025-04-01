import json
import logging
import re
import copy
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
from pydantic import BaseModel


class SearchQuery(BaseModel):
    queries: list[str]


class SearchPlannerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("search_planner")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        mapped_assets = belief_state.get("event_branches", [])
        existing_queries = belief_state.get("search_queries", [])

        # Track existing signatures to avoid duplication
        existing_signatures = {
            self._query_signature(q) for q in existing_queries
        }

        new_search_plans = []

        for asset in mapped_assets:
            if asset.get("analyzed"):
                continue

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(asset)}
            ]

            try:
                raw_response = await call_gpt(messages, response_format=SearchQuery)
                logging.debug(
                    f"SearchPlannerAgent raw response: {raw_response}")

                queries_output = json.loads(raw_response.model_dump_json())
                search_queries = copy.deepcopy(asset)
                search_queries["queries"] = queries_output.get("queries", [])
                search_queries["analyzed"] = False

                signature = self._query_signature(search_queries)
                if signature not in existing_signatures:
                    new_search_plans.append(search_queries)
                    existing_signatures.add(signature)

                asset["analyzed"] = True

            except Exception as e:
                logging.warning(
                    f"SearchPlannerAgent: Failed to generate queries. {str(e)}")
                continue

        # Append new plans to existing ones
        belief_state["search_queries"] = existing_queries + new_search_plans
        self.summary = f"SearchPlannerAgent: Generated {len(new_search_plans)} new search plans."
        return belief_state

    def _query_signature(self, item: dict) -> str:
        """Create a unique signature to prevent query duplication."""
        return json.dumps({
            "event": item.get("event"),
            "ticker": item.get("ticker"),
            "queries": sorted(item.get("queries", []))
        }, sort_keys=True)

    def _try_json_repair(self, raw_text: str) -> str:
        try:
            match = re.search(
                r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", raw_text, re.DOTALL)
            if match:
                raw_text = match.group(0)

            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            return cleaned
        except Exception as e:
            logging.warning(
                "SearchPlannerAgent: JSON repair failed: %s", str(e))
            return raw_text
