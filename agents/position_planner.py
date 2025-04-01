import json
import logging
from typing import List
from datetime import datetime, timedelta
import re

from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt


class PositionPlannerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("position_planner")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        position_candidates = belief_state.get("position_candidates", [])
        confirmed_positions = belief_state.get("confirmed_positions", [])

        new_positions_count = 0

        for candidate in position_candidates:
            if candidate.get("analyzed"):
                continue  # Skip already analyzed

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(candidate, indent=2)}
            ]

            try:
                raw_response = await call_gpt(messages)
                repaired_json = self._try_json_repair(raw_response)
                parsed_response = json.loads(repaired_json)

                # Ensure we're dealing with a list
                if not isinstance(parsed_response, list):
                    parsed_response = [parsed_response]

                event_date_str = candidate.get("date")
                event_date = datetime.strptime(
                    event_date_str, "%Y-%m-%d") if event_date_str else datetime.now()

                for trade in parsed_response:
                    # Add start and end dates
                    latency = trade.get("latency", "").lower()
                    if latency == "short_term":
                        delta = (1, 2)
                    elif latency == "medium_term":
                        delta = (3, 7)
                    elif latency == "long_term":
                        delta = (8, 20)
                    else:
                        delta = (2, 5)

                    trade["start_date"] = event_date.strftime("%Y-%m-%d")
                    trade["end_date"] = (
                        event_date + timedelta(days=delta[1])).strftime("%Y-%m-%d")
                    trade["status"] = "pending"
                    trade["analyzed"] = False

                    confirmed_positions.append(trade)
                    new_positions_count += 1

                # Mark candidate as analyzed
                candidate["analyzed"] = True

            except Exception as e:
                logging.warning(
                    f"PositionPlannerAgent: Failed to process candidate: {e}")
                continue

        belief_state["confirmed_positions"] = confirmed_positions
        self.summary = f"PositionPlannerAgent: Added {new_positions_count} confirmed positions."
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
            logging.warning(f"PositionPlannerAgent: JSON repair failed: {e}")
            return text
