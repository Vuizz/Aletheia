import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt

CHUNK_SIZE = 5  # max number of recent events per GPT check


class EventParserAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("event_parser")
        self.dedup_prompt = load_prompt(
            "event_deduplicator")  # New prompt file
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

            existing_events = belief_state.get("recent_events", [])
            new_valid_events = []

            for event in parsed:
                if await self._is_duplicate(event, existing_events):
                    logging.info(
                        f"EventParser: Skipping duplicate event: {event['event']}")
                    continue
                new_valid_events.append(event)

            combined_events = existing_events + new_valid_events
            belief_state["recent_events"] = combined_events
            self.summary = f"EventParser: Parsed {len(new_valid_events)} new events (total: {len(combined_events)})."
        except Exception as e:
            logging.warning(
                "EventParserAgent: Failed to parse events. %s", str(e))
            self.summary = "EventParser: Failed to parse events."

        return belief_state

    async def _is_duplicate(self, new_event, existing_events):
        # Break recent events into blocks
        for i in range(0, len(existing_events), CHUNK_SIZE):
            chunk = existing_events[i:i + CHUNK_SIZE]
            messages = [
                {"role": "system", "content": self.dedup_prompt},
                {"role": "user", "content": json.dumps({
                    "new_event": new_event,
                    "existing_events": chunk
                }, indent=2)}
            ]

            try:
                result = await call_gpt(messages)
                parsed = json.loads(result)
                if parsed.get("is_duplicate") is True:
                    return True
            except Exception as e:
                logging.warning(f"Deduplication check failed: {e}")
                continue
        return False

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
