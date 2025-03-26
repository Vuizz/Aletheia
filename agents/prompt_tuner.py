import json
import logging
import re
import ast
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from core.prompt_loader import load_prompt

class PromptTunerAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("prompt_tuner")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        meta_review = belief_state.get("meta_review", "")
        weakest_output = belief_state.get("report", "")

        target_agent = self._extract_field(meta_review, "Target Agent")
        problem = self._extract_field(meta_review, "Problem Summary")
        prev_snippet = self._extract_field(meta_review, "Improved Prompt Snippet")

        structured_input = json.dumps({
            "target_agent": target_agent,
            "problem": problem,
            "last_output_sample": weakest_output[:400],
            "last_prompt_snippet": prev_snippet
        })

        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": structured_input}
        ]

        try:
            raw = await call_gpt(messages)
            if not isinstance(raw, str):
                logging.warning("PromptTunerAgent: Unexpected GPT response type: %s", type(raw))
                raw = str(raw)
            raw = raw.strip()
            suggestion = self._try_json_repair(raw)
            if not self._validate_format(suggestion):
                logging.warning("PromptTunerAgent: Invalid format in GPT response, skipping patch.")
                self.summary = "PromptTuner: Skipped invalid suggestion."
            else:
                belief_state["prompt_tuner_suggestions"] = suggestion
                self.summary = f"PromptTuner: Suggested improvement for agent '{target_agent}'."
                logging.info("PromptTunerAgent: Structured prompt improvement suggestion created.")
        except Exception as e:
            logging.warning("PromptTunerAgent: Failed to generate suggestions: %s", str(e))
            self.summary = "PromptTuner: Failed to run."

        return belief_state

    def _extract_field(self, text, label):
        for line in text.splitlines():
            if line.lower().startswith(label.lower()):
                return line.split(":", 1)[-1].strip()
        return ""

    def _validate_format(self, suggestion):
        required = ["Target Agent:", "Improved Prompt Snippet:"]
        return all(section in suggestion for section in required)

    def _try_json_repair(self, raw_text):
        """Attempt to sanitize broken JSON-style output."""
        try:
            cleaned = raw_text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)  # collapse excessive whitespace
            cleaned = cleaned.replace("'", '"')       # single to double quotes
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # remove trailing commas
            return cleaned
        except Exception as e:
            logging.warning("PromptTunerAgent: Failed JSON repair: %s", str(e))
            return raw_text