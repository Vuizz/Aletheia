import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class NarrativeTrackerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("narrative_tracker")
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
            cleaned = self._try_json_repair(raw_response.strip())
            parsed = json.loads(cleaned)
            belief_state["active_narratives"] = parsed
            self.summary = f"NarrativeTracker: Updated {len(parsed)} narratives."
        except Exception as e:
            logging.warning("NarrativeTrackerAgent: Failed to parse response. %s", str(e))
            self.summary = "NarrativeTracker: Failed to update narratives."

        return belief_state

    def _try_json_repair(self, raw_text):
        try:
            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            return cleaned
        except Exception as e:
            logging.warning("NarrativeTrackerAgent: JSON repair failed: %s", str(e))
            return raw_text