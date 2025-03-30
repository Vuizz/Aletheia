import json
import logging
import re
import copy
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
from pydantic import BaseModel

# {
#   "notable_entities": ["Sun Hung Kai Properties", "Henderson Land", "Link REIT", "Hong Kong Housing Society"],
#   "market_statistics": [
#     "Grade A office vacancy rate in Hong Kong was 15.3% in Q4 2024",
#     "Office rents fell 7.2% year-over-year in early 2025",
#     "New commercial space completions exceeded leasing demand by 20% in 2024"
#   ],
#   "regional_context": "Hong Kong's commercial real estate market is facing persistent oversupply due to reduced demand from multinationals, a slow post-pandemic recovery, and increased remote work. Government efforts to revitalize the market have had limited impact so far."
# }


class GroundedEvent(BaseModel):
    notable_entities: list[str]
    market_statistics: list[str]
    regional_context: str


class EventGroundingAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("event_grounding")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        enriched_events = belief_state.get("enriched_events", [])
        grounded_events = belief_state.get("grounded_events", [])

        for event in enriched_events:
            if event.get("analyzed", False):
                continue  # Skip already-analyzed events

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(event)}
            ]

            try:
                raw_response = await call_gpt(messages, response_format=GroundedEvent)
                logging.debug(
                    f"EventGroundingAgent raw response: {raw_response}")

                # repaired = self._try_json_repair(raw_response.strip())
                additions = json.loads(raw_response.model_dump_json())

                # Merge enriched_event copy + new grounding fields
                grounded_event = copy.deepcopy(event)
                grounded_event.update({
                    "notable_entities": additions.get("notable_entities", []),
                    "market_statistics": additions.get("market_statistics", []),
                    "regional_context": additions.get("regional_context", ""),
                    "analyzed": False  # This grounded event hasn't been processed further
                })

                grounded_events.append(grounded_event)
                event["analyzed"] = True  # mark enriched event as processed

            except Exception as e:
                logging.warning(
                    "EventGroundingAgent: Failed to parse or enrich response. %s", str(e))
                # If grounding fails, retain the enriched event as-is
                fallback_event = copy.deepcopy(event)
                fallback_event["analyzed"] = False
                grounded_events.append(fallback_event)

        belief_state["grounded_events"] = grounded_events
        self.summary = f"EventGroundingAgent: Grounded {len(grounded_events)} events with contextual data."

        return belief_state

    def _try_json_repair(self, raw_text: str) -> str:
        try:
            # Extract only the first valid JSON object from noisy text
            match = re.search(
                r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", raw_text, re.DOTALL)
            if match:
                raw_text = match.group(0)

            # Replace smart quotes and normalize characters
            cleaned = raw_text.strip()
            cleaned = cleaned.replace('“', '"').replace('”', '"')
            cleaned = cleaned.replace("’", "'").replace("‘", "'")
            cleaned = cleaned.replace("–", "-").replace("—", "-")
            cleaned = cleaned.replace("…", "...").replace(
                "′", "'").replace("″", '"')
            cleaned = cleaned.replace("•", "-")

            # Remove trailing commas before closing braces/brackets
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

            # Remove invisible unicode and normalize whitespace
            cleaned = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned)

            return cleaned

        except Exception as e:
            logging.warning(
                "EventGroundingAgent: JSON repair failed: %s", str(e))
            return raw_text
