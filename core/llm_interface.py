import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import httpx
import concurrent.futures
import asyncio
import time

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not found. Please set it using conda, system env, or a .env file.")

client = OpenAI(api_key=openai_api_key)

async def call_gpt(messages, model="gpt-4o-mini", temperature=0.8):
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']



if __name__ == "__main__":
    countries = ["Canada", "United States", "Mexico", "Brazil", "Argentina"]
    start = time.time()
    for country in countries:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"What is the capital of {country}?"}
        ]

        response = asyncio.run(call_gpt(messages))
        print(response)
    print(f"\n🕒 Single-threaded Time: {time.time() - start:.2f} seconds")

    def ask_gpt(country):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"What is the capital of {country}?"}
        ]
        return asyncio.run(call_gpt(messages))  # This should be the sync version

    start = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(ask_gpt, country) for country in countries]
        results = [f.result() for f in futures]

    for country, result in zip(countries, results):
        print(f"{country}: {result}")

    print(f"\n🕒 Multi-threaded Time: {time.time() - start:.2f} seconds")



