import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class ScenarioForecasterAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("scenario_forecaster")
        super().__init__(prompt)
        self.summary = "ScenarioForecaster: No scenarios generated."

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": json.dumps({
                "recent_events": belief_state.get("recent_events", []),
                "active_narratives": belief_state.get("active_narratives", []),
                "reasoning_chain": belief_state.get("reasoning_chain", [])
            })}
        ]

        try:
            raw_response = await call_gpt(messages)
            if not raw_response.strip():
                raise ValueError("Empty response from LLM.")

            logging.debug(f"ScenarioForecasterAgent raw LLM response:\n{raw_response}")

            cleaned = self._try_json_repair(raw_response.strip())
            logging.debug(f"ScenarioForecasterAgent cleaned JSON:\n{cleaned}")

            scenarios = json.loads(cleaned)
            belief_state["scenarios"] = scenarios

            if scenarios:
                self.summary = f"ScenarioForecaster: Generated {len(scenarios)} scenarios."
            else:
                self.summary = "ScenarioForecaster: Empty scenario list returned."

        except Exception as e:
            logging.warning("ScenarioForecasterAgent: Failed to parse JSON response. %s", str(e))
            self.summary = f"ScenarioForecaster: Failed to generate scenarios ({str(e)})"

        return belief_state

    def _try_json_repair(self, raw_text):
        try:
            # Extract only the JSON array portion
            match = re.search(r"\[\s*{.*?}\s*\]", raw_text, re.DOTALL)
            if match:
                raw_text = match.group(0)

            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace("'", '"')
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # Remove trailing commas
            return cleaned
        except Exception as e:
            logging.warning("ScenarioForecasterAgent: JSON repair failed: %s", str(e))
            return raw_text
