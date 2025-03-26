import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class TickerLinkerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("ticker_linker")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": json.dumps({
                "recent_events": belief_state.get("recent_events", []),
                "active_narratives": belief_state.get("active_narratives", [])
            })}
        ]

        try:
            raw_response = await call_gpt(messages)
            logging.debug(f"TickerLinkerAgent raw LLM response:\n{raw_response}")

            cleaned = self._try_json_repair(raw_response.strip())
            linked = json.loads(cleaned)

            # Validate expected format
            if not isinstance(linked, list) or not all("event" in item and "linked_tickers" in item for item in linked):
                raise ValueError("Invalid format: expected list of {'event', 'linked_tickers'} dictionaries")

            belief_state["linked_tickers"] = linked
            self.summary = f"TickerLinker: Linked {len(linked)} ticker sets."

        except Exception as e:
            logging.warning("TickerLinkerAgent: Failed to parse JSON response. %s", str(e))
            self.summary = "TickerLinker: Failed to generate linked tickers."

        return belief_state

    def _try_json_repair(self, raw_text):
        try:
            # Attempt to extract JSON array even if surrounded by explanation
            match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if match:
                raw_text = match.group(0)

            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # Remove trailing commas
            return cleaned
        except Exception as e:
            logging.warning("TickerLinkerAgent: JSON repair failed: %s", str(e))
            return raw_text
