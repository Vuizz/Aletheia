import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt


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

            for event in parsed:
                event["analyzed"] = False

            # Get existing events from belief state
            existing_events = belief_state.get("recent_events", [])

            # Convert to set of unique identifiers (e.g., stringified form)
            existing_signatures = {
                self._event_signature(e) for e in existing_events
            }

            # Add only new unique events
            new_events = [
                e for e in parsed
                if self._event_signature(e) not in existing_signatures
            ]

            combined_events = existing_events + new_events
            belief_state["recent_events"] = combined_events

            self.summary = f"EventParser: Parsed {len(new_events)} new events (total: {len(combined_events)})."
        except Exception as e:
            logging.warning(
                "EventParserAgent: Failed to parse events. %s", str(e))
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

    def _event_signature(self, event: dict) -> str:
        """Create a simplified hashable signature for deduplication."""
        return json.dumps({
            "event": event.get("event"),
            "date": event.get("date"),
            "type": event.get("type")
        }, sort_keys=True)
