import json
import logging
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class MetaEvaluatorAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("meta_evaluator")
        super().__init__(prompt)

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        input_block = json.dumps({
            "recent_events": belief_state.get("recent_events", []),
            "active_narratives": belief_state.get("active_narratives", []),
            "reasoning_chain": belief_state.get("reasoning_chain", []),
            "scenarios": belief_state.get("scenarios", []),
            "report": belief_state.get("report", "")
        })

        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": input_block}
        ]

        try:
            meta_review = await call_gpt(messages)
            belief_state["meta_review"] = meta_review.strip()
            logging.info("MetaEvaluatorAgent: Review generated.")
        except Exception as e:
            logging.warning("MetaEvaluatorAgent: Failed to generate review: %s", str(e))
        return belief_state
