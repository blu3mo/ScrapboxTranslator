import openai
import os
import asyncio
import json
import aiohttp
import tiktoken
from util import num_tokens_from_string

MODEL = "gpt-3.5-turbo"

PROMPT = """
Translate the given page titles to English.
Input: JSON array of page titles.
Output: JSON dictionary of original titles & translated titles.
"""

# Set OpenAI API Key
openai.api_key = os.environ.get("OPENAI_API_KEY")

async def fetch_title_translation(title_array_str):
    """
    Fetches the translation of a title from OpenAI API

    Args:
        title_array_str (str): The array of titles to be translated

    Returns:
        (dict): A dictionary of original titles & translated titles
        
    """
    print(title_array_str)
    response = await openai.ChatCompletion.acreate(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": PROMPT
            },
            {
                "role": "user",
                "content": title_array_str
            }
        ],
        temperature=0.2,
        max_tokens=2048
    )

    # For each returned translation, add to the translations dictionary
    response_content = response['choices'][0]['message']['content']
    translated_titles = json.loads(response_content)

    return translated_titles
