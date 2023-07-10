import openai
import os
import json
import aiohttp
import tiktoken
import asyncio
from util import num_tokens_from_string, get_links
from dotenv import load_dotenv

load_dotenv()

def generate_system_prompt(links):
    prompt_str = """
# Task
Convert the style of this personal note from bullet points to cohesive easy-to-read structured paragraphs with [keywords] in English. 

[Keywords] in the input are in square brackets, so all in the output must be in square brackets too. 

Links like [https://gyazo.com/~] in the input are in square brackets, so all in the output must be in square brackets too. 

# Output Rules 
Include all the keywords and links below in the output. Translate non-English keywords to English.
"""

    links_str = ""
    for link in links:
        links_str += "[" + link + "]\n"

    return prompt_str + "\n" + links_str


MAX_TOKENS = {
    "gpt-3.5-turbo": 2048,
    "gpt-3.5-turbo-16k": 8192
}

# global variables for log output
translation_start_count = 1
translation_end_count = 1

# Set OpenAI API Key
openai.api_key = os.environ.get("OPENAI_API_KEY")

async def fetch_page_translation(pageId, page, max_retries=3):
    """
    Fetches the translation of a page from OpenAI API

    Args:
        pageId (str): The pageId of the page
        page (str): The page to be translated
        max_retries (int): The maximum number of retries in case of failure

    Returns:
        (str, str): A tuple of the pageId and the translated page
    """
    temperature = 0

    for attempt in range(max_retries):
        system_prompt = generate_system_prompt(get_links(page))
        prompt_token_count = num_tokens_from_string(system_prompt)
        token_count = num_tokens_from_string(page)
        model = ""
        if token_count <= 2048 - prompt_token_count - 100:
            model = "gpt-3.5-turbo"
        elif token_count <= 8192 - prompt_token_count - 100:
            model = "gpt-3.5-turbo-16k"
        else:
            model = "gpt-3.5-turbo-16k"
            page_token_count = num_tokens_from_string(page)
            cutoff_len = int(len(page) * ((8192 - prompt_token_count - 100) / page_token_count))
            print("Page too long, cutting off: " + page[:25].replace('\n', ' ') + "...")
            page = page[:cutoff_len]
        
        max_tokens = MAX_TOKENS[model]

        try:
            global translation_start_count
            print("(#" + str(translation_start_count) + ") Starting Page Translation: " + page[:25].replace('\n', ' ') + "...")
            translation_start_count += 1
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": generate_system_prompt(get_links(page))
                    },
                    {
                        "role": "user",
                        "content": page
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            translated_page = response['choices'][0]['message']['content']
            global translation_end_count
            print("(#" + str(translation_end_count) + ") Finished Page Translation: " + page[:25].replace('\n', ' ') + "...")
            translation_end_count += 1

            return (pageId, translated_page)
        except Exception as e:
            print(f"Error in fetch_page_translation, attempt #{attempt + 1}: " + page[:25].replace('\n', ' ') + "...")
            print(e)
            if attempt == max_retries - 1:  # If this was the last attempt
                return (pageId, page)
            else:
                print("Retrying...")
                temperature += 0.5
