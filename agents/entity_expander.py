import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
import copy
from pydantic import BaseModel


class Entity(BaseModel):
    event: str
    entities: list[str]
    regions: list[str]
    sectors: list[str]
    themes: list[str]


class EntityExpanderAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("entity_expander")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        recent_events = belief_state.get("recent_events", [])
        enriched_events = belief_state.get("enriched_events", [])

        existing_signatures = {
            self._event_signature(event) for event in enriched_events
        }

        new_enriched = []

        for event in recent_events:
            if event.get("analyzed", False):
                continue

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(event)}
            ]

            try:
                raw_response = await call_gpt(messages, response_format=Entity)
                parsed = json.loads(raw_response.model_dump_json())

                if isinstance(parsed, list):
                    parsed = parsed[0]

                if not isinstance(parsed, dict):
                    raise ValueError("Expected a dictionary in GPT response.")

                enriched_event = copy.deepcopy(event)
                enriched_event.update({
                    "entities": parsed.get("entities", []),
                    "regions": parsed.get("regions", []),
                    "sectors": parsed.get("sectors", []),
                    "themes": parsed.get("themes", []),
                    "analyzed": False
                })

                # Avoid duplicates
                if self._event_signature(enriched_event) not in existing_signatures:
                    new_enriched.append(enriched_event)
                    existing_signatures.add(
                        self._event_signature(enriched_event))

                event["analyzed"] = True  # mark original event as processed

            except Exception as e:
                logging.warning(
                    "EntityExpanderAgent: Failed to enrich event. %s", str(e))
                enriched_event = copy.deepcopy(event)
                if self._event_signature(enriched_event) not in existing_signatures:
                    new_enriched.append(enriched_event)

        enriched_events += new_enriched
        belief_state["enriched_events"] = enriched_events
        self.summary = f"EntityExpander: Expanded {len(new_enriched)} new events."

        return belief_state

    def _event_signature(self, event: dict) -> str:
        """Create a hashable signature to deduplicate enriched events."""
        return json.dumps({
            "event": event.get("event"),
            "entities": event.get("entities"),
            "regions": event.get("regions"),
            "sectors": event.get("sectors"),
            "themes": event.get("themes")
        }, sort_keys=True)

    def _try_json_repair(self, raw_text):
        try:
            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            return cleaned
        except Exception as e:
            logging.warning(
                "EntityExpanderAgent: JSON repair failed: %s", str(e))
            return raw_text
