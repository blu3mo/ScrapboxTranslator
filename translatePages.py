import openai
import os
import json
import aiohttp
import tiktoken
import asyncio
from util import num_tokens_from_string

PROMPT = """
# Task
Convert the style of this personal note from bullet points to cohesive easy-to-read structured paragraphs with [links] in English. 
Input: Bullet points with links in [Brackets].
Output: Structured English paragarphs with links in [Brackets].

# Input/Output Syntax
[Brackets] are links
[https://gyazo.com/~] are image links
> are quotes

# Rules
When you see [Brackets] and [https://gyazo.com/~], always preserve it.

# Example
Sample Input: 
\"\"\"
[ディープラーニング]の[研究]プロジェクトをやってる。
スクリーショット：[https://gyazo.com/3d6a6de185e26530a73c7ef08a88e390]
\"\"\"
Sample Output: 
\"\"\"
I've been working on a [research] project which is centred around [deep learning].
You can view the screenshot here: 
[https://gyazo.com/3d6a6de185e26530a73c7ef08a88e390]
\"\"\"
"""

MAX_TOKENS = {
    "gpt-3.5-turbo": 2048,
    "gpt-3.5-turbo-16k": 8192
}

# Set OpenAI API Key
openai.api_key = os.environ.get("OPENAI_API_KEY")

async def fetch_page_translation(pageId, page):

    """
    Fetches the translation of a page from OpenAI API

    Args:
        pageId (str): The pageId of the page
        page (str): The page to be translated

    Returns:
        (str, str): A tuple of the pageId and the translated page
    """

    token_count = num_tokens_from_string(page)
    model = ""
    if token_count <= 1800:
        model = "gpt-3.5-turbo"
    elif 1800 < token_count <= 7000:
        model = "gpt-3.5-turbo-16k"
    else:
        model = "gpt-3.5-turbo-16k"
        page_token_count = num_tokens_from_string(page)
        cutoff_len = int(len(page) * (7000 / page_token_count))
        print("cutoff: " + str(cutoff_len))
        page = page[:cutoff_len]
    
    max_tokens = MAX_TOKENS[model]

    try:
        print("Fetch Translation: " + page[:25].replace('\n', ' ') + "...")
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": PROMPT
                },
                {
                    "role": "user",
                    "content": page
                }
            ],
            temperature=0,
            max_tokens=max_tokens
        )
        translated_page = response['choices'][0]['message']['content']

        return (pageId, translated_page)
    except Exception as e:
        print("Error in fetch_page_translation: " + page[:25].replace('\n', ' ') + "...")
        print(e)
        return (pageId, page)