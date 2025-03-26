import logging
from core.llm_interface import call_gpt

REVIEW_PROMPT = """
You are a system improvement reviewer.

You are given a diff between two snapshots of an AI agent's belief state. Your task is to:

1. Determine if the newer version shows meaningful improvement.
2. Highlight areas that got better or worse.
3. Score the improvement from -1.0 (worse) to +1.0 (much better).
4. Suggest one concrete improvement for future iterations.

Focus on:
- Clarity and uniqueness of reasoning
- Narrative evolution
- Better or worse scenario coverage
- Usefulness of the final report

Respond in bullet points.
"""

async def review_diff(diff_text: str) -> str:
    messages = [
        {"role": "system", "content": REVIEW_PROMPT},
        {"role": "user", "content": diff_text}
    ]

    try:
        result = await call_gpt(messages)
        logging.info("DiffReviewer: Analysis complete.")
        return result.strip()
    except Exception as e:
        logging.error(f"DiffReviewer: Error during review: {str(e)}")
        return "Review failed."