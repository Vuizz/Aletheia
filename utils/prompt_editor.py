import os
import re
import logging


def extract_patch_components(suggestion: str):
    try:
        # Match line: **Target Agent:** ScenarioForecasterAgent
        agent_match = re.search(
            r"\*\*Target Agent:\*\*\s*(\w+)", suggestion)

        # Match block: **Improved Prompt Snippet:** <capture until next heading>
        patch_match = re.search(
            r"\*\*Improved Prompt Snippet:\*\*\s*(.*?)(?:\n\*\*|\Z)",
            suggestion,
            re.DOTALL
        )

        if not agent_match or not patch_match:
            return None, None

        agent_name = agent_match.group(1).strip().lower().replace("agent", "")
        patch_snippet = patch_match.group(1).strip()
        return agent_name, patch_snippet

    except Exception as e:
        logging.error(f"PromptEditor: Failed to extract components: {str(e)}")
        return None, None


def apply_prompt_patch(suggestion: str, prompt_dir="prompts"):
    agent_name, new_clause = extract_patch_components(suggestion)

    if not agent_name or not new_clause:
        logging.warning(
            "PromptEditor: Could not extract target agent or snippet.")
        return False

    prompt_path = os.path.join(prompt_dir, f"{agent_name}.txt")
    if not os.path.exists(prompt_path):
        logging.error(
            f"PromptEditor: Prompt file not found for agent: {agent_name}")
        return False

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            original = f.read()

        # Remove any previous patch
        patched = re.sub(
            r"\n?# \[AUTOPATCHED CLAUSE\](.*?)($|\n#|\Z)",
            "",
            original,
            flags=re.DOTALL
        ).strip()

        # Skip if the patch is already in place
        if new_clause in patched:
            logging.info("PromptEditor: Patch already present. Skipping.")
            return True

        patched += f"\n\n# [AUTOPATCHED CLAUSE]\n{new_clause}"

        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(patched.strip())

        logging.info(
            f"PromptEditor: Patch successfully applied to {prompt_path}.")
        return True

    except Exception as e:
        logging.error(f"PromptEditor: Error applying patch: {str(e)}")
        return False
