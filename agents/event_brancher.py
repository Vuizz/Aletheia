import json
import logging
from typing import List
from pydantic import BaseModel
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
import re


class EventBrancherAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("event_brancher")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        grounded_events = belief_state.get("grounded_events", [])
        event_branches = belief_state.get("event_branches", [])

        new_branches = 0
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

                for branch in parsed_branches:
                    branch_entry = {
                        **event,
                        **branch,  # flatten the branch object
                        "parent_event": event["event"],
                        "analyzed": False  # to be processed by next agent
                    }
                    # Remove keys already merged from event to avoid redundancy
                    branch_entry.pop("branches", None)
                    new_branches += 1
                    event_branches.append(branch_entry)

                event["analyzed"] = True

            except Exception as e:
                logging.warning(
                    f"EventBrancherAgent: Failed to branch event. {str(e)}")
                continue

        belief_state["event_branches"] = event_branches
        self.summary = f"EventBrancherAgent: Created {len(new_branches)} individual branches."
        return belief_state

    def _try_json_repair(self, text: str) -> str:
        try:
            match = re.search(r"\[\s*{.*?}\s*\]", text, re.DOTALL)
            cleaned = match.group(0) if match else text.strip()

            cleaned = cleaned.replace("“", '"').replace("”", '"')
            cleaned = cleaned.replace("‘", "'").replace("’", "'")
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned)

            return cleaned
        except Exception as e:
            logging.warning(f"EventBrancherAgent: JSON repair failed: {e}")
            return text
