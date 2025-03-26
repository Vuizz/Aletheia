import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class EventParserAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("event_parser")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str) -> dict:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": input_data.strip()}
        ]

        try:
            raw_response = await call_gpt(messages)
            cleaned = self._try_json_repair(raw_response.strip())
            parsed = json.loads(cleaned)
            belief_state["recent_events"] = parsed
            self.summary = f"EventParser: Parsed {len(parsed)} events."
        except Exception as e:
            logging.warning("EventParserAgent: Failed to parse events. %s", str(e))
            self.summary = "EventParser: Failed to parse events."

        return belief_state

    def _try_json_repair(self, raw_text):
        try:
            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            return cleaned
        except Exception as e:
            logging.warning("EventParserAgent: JSON repair failed: %s", str(e))
            return raw_text
