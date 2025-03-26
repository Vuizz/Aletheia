def load_prompt(agent_name: str) -> str:
    with open(f"prompts/{agent_name}.txt", "r", encoding="utf-8") as f:
        return f.read()
