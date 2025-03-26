import logging
from agents.prompt_tuner import PromptTunerAgent
from agents.meta_evaluator import MetaEvaluatorAgent
from utils.prompt_editor import apply_prompt_patch

MAX_ATTEMPTS = 1

class ConfidenceController:
    def __init__(self, pipeline_function):
        self.pipeline_function = pipeline_function
        self.patched_agents = set()

    async def run_with_autotune(self, input_text, belief_state):
        attempt = 0
        old_state = dict(belief_state)

        while attempt < MAX_ATTEMPTS:
            logging.info(f"ConfidenceController: Attempt {attempt + 1} of {MAX_ATTEMPTS}...")

            # 🧠 Run async pipeline
            state = await self.pipeline_function(input_text)

            # 🔍 Evaluate output (async)
            evaluator = MetaEvaluatorAgent()
            state = await evaluator.run(state)
            review = state.get("meta_review", "")

            if "[ACCEPT]" in review:
                logging.info("ConfidenceController: Analysis accepted.")
                break
            elif "[REVISE]" in review or "[REJECT]" in review:
                logging.warning("ConfidenceController: Analysis flagged for revision.")

                # 🔧 Run prompt tuner (async)
                tuner = PromptTunerAgent()
                state = await tuner.run(state)
                suggestion = state.get("prompt_tuner_suggestions", "")

                if suggestion:
                    # Prevent repeat patching of the same agent
                    for line in suggestion.splitlines():
                        if "Target Agent:" in line:
                            target_agent = line.split(":", 1)[-1].strip()
                            if target_agent not in self.patched_agents:
                                logging.info(f"ConfidenceController: Applying patch to {target_agent}...")
                                apply_prompt_patch(suggestion)
                                self.patched_agents.add(target_agent)
                            else:
                                logging.info(f"ConfidenceController: Agent {target_agent} already patched this session. Skipping.")
                            break

            attempt += 1

        if attempt == MAX_ATTEMPTS:
            logging.error("ConfidenceController: Maximum attempts reached. Final state may still need revision.")

        return state
