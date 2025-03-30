import json
import logging
from typing import List
from pydantic import BaseModel
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
import re


# class EventBranch(BaseModel):
#     branch: str
#     target_entities: List[str]
#     expected_impact: str
#     affected_regions: List[str]
#     sector: str


class EventBrancherAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("event_brancher")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        grounded_events = belief_state.get("grounded_events", [])
        event_branches = belief_state.get("event_branches", [])

        for event in grounded_events:
            if event.get("analyzed"):
                continue

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(event)}
            ]

            try:
                raw_response = await call_gpt(messages)
                cleaned = self._try_json_repair(raw_response.strip())
                parsed_branches = json.loads(cleaned)

                branch_entry = {
                    **event,  # include original event metadata
                    "branches": parsed_branches,
                    "analyzed": False
                }
                event_branches.append(branch_entry)

                event["analyzed"] = True

            except Exception as e:
                logging.warning(
                    f"EventBrancherAgent: Failed to branch event. {str(e)}")
                continue

        belief_state["event_branches"] = event_branches
        self.summary = f"EventBrancherAgent: Created {len(event_branches)} event branches."
        return belief_state

    def _try_json_repair(self, text: str) -> str:
        try:
            # Extract the first list (array of branches)
            match = re.search(r"\[\s*{.*?}\s*\]", text, re.DOTALL)
            if match:
                cleaned = match.group(0)
            else:
                cleaned = text.strip()

            # Normalize quotes
            cleaned = cleaned.replace("“", '"').replace("”", '"')
            cleaned = cleaned.replace("‘", "'").replace("’", "'")

            # Fix trailing commas
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

            # Remove excessive whitespace
            cleaned = re.sub(r"\s+", " ", cleaned)

            return cleaned
        except Exception as e:
            logging.warning(f"EventBrancherAgent: JSON repair failed: {e}")
            return text
