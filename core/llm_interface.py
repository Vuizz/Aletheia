import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import httpx
import concurrent.futures
import asyncio
import time
from pydantic import BaseModel
import json

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise EnvironmentError(
        "OPENAI_API_KEY environment variable not found. Please set it using conda, system env, or a .env file.")

client = OpenAI(api_key=openai_api_key)


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def call_gpt(messages, model="gpt-4o-mini", temperature=0.8, response_format: type[BaseModel] = None):
    """
    Calls the OpenAI GPT model, optionally parsing structured output with a Pydantic schema.

    Args:
        messages (list): List of message dictionaries.
        model (str): Model name (default: gpt-4o).
        temperature (float): Sampling temperature.
        response_format (BaseModel or None): Optional Pydantic class for structured output.

    Returns:
        Either the parsed object (if response_format provided) or raw string response.
    """
    if response_format:
        # Use OpenAI SDK’s structured output via `.parse()`
        completion = await asyncio.to_thread(
            client.beta.chat.completions.parse,
            model=model,
            messages=messages,
            temperature=temperature,
            response_format=response_format
        )
        return completion.choices[0].message.parsed
    else:
        # Fall back to normal completion if no schema is provided
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=messages,
            temperature=temperature
        )
        return completion.choices[0].message.content


if __name__ == "__main__":
    start = time.time()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"what are the countries in europe? provide a list of countries with their capitals, some towns, and the continent they belong to."}
    ]

    class TestOutput(BaseModel):
        country_name: str
        town_name: list[str]
        continent: str

    response = asyncio.run(call_gpt(messages, response_format=TestOutput))
    loaded = json.loads(response.model_dump_json())
    print(loaded)
