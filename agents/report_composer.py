import json
import logging
import re
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class ReportComposerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("report_composer")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": json.dumps({
                "recent_events": belief_state.get("recent_events", []),
                "active_narratives": belief_state.get("active_narratives", []),
                "reasoning_chain": belief_state.get("reasoning_chain", []),
                "scenarios": belief_state.get("scenarios", [])
            })}
        ]

        try:
            raw_response = await call_gpt(messages)
            belief_state["report"] = raw_response.strip()
            self.summary = f"ReportComposer: Composed report ({len(raw_response.split())} words)."
        except Exception as e:
            logging.warning("ReportComposerAgent: Failed to compose report. %s", str(e))
            self.summary = "ReportComposer: Failed to generate report."

        return belief_state