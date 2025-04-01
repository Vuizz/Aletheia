import json
import logging
import copy
from typing import List, Literal
from pydantic import BaseModel
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt
from core.llm_interface import call_gpt


class PositionCandidate(BaseModel):
    direction: Literal["long", "short"]
    latency: Literal["short_term", "medium_term", "long_term"]
    reasoning: str


class PositionEvaluatorAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("position_evaluator")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        websearch_results = belief_state.get("websearch_results", [])
        position_candidates = belief_state.get("position_candidates", [])

        new_candidates = 0
        for result in websearch_results:
            if result.get("analyzed"):
                continue

            if result.get("verdict") != "supported":
                result["analyzed"] = True
                continue

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(result)}
            ]

            try:
                response = await call_gpt(messages, response_format=PositionCandidate)
                parsed = json.loads(response.model_dump_json())

                candidate = copy.deepcopy(result)
                candidate.update({
                    "direction": parsed.get("direction"),
                    "latency": parsed.get("latency"),
                    "reasoning": parsed.get("reasoning"),
                    "analyzed": False
                })
                new_candidates += 1
                position_candidates.append(candidate)
                result["analyzed"] = True

            except Exception as e:
                logging.warning(
                    f"PositionEvaluatorAgent: Failed to evaluate position. {str(e)}")
                continue

        belief_state["position_candidates"] = position_candidates
        self.summary = f"PositionEvaluatorAgent: Created {len(new_candidates)} position candidates."
        return belief_state
