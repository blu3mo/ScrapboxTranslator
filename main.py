import json
import asyncio
import aiohttp
import openai

MAX_TOKENS = 8000
INPUT_PATH = "input_json/test1.json"
OUTPUT_PATH = "output_json/test1_2.json"

PROMPT = """
You are a translator. 
# Task
You get multiple texts to translate. Translate texts to English, and return translated texts.
# Rules
Keep the number of lines and newlines. Never remove spaces at the beginning of each line. Keep the number of spaces the same. 
Brackets of [text] and [text.icon] must be kept. The content inside the bracket must never be changed.
"""

async def async_translate(session, text, role="user"):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": role, "content": text}
        ]
    }

    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as resp:
        response = await resp.json()
        print(response)
        return response["choices"][0]["message"]["content"]

async def translate_titles(session, title_list):
    translated_titles = []
    title_chunk = ""

    for title in title_list:
        if len(title_chunk) + len(title) + 1 < MAX_TOKENS:
            title_chunk += title + "\n"
        else:
            translated_chunk = await async_translate(session, title_chunk)
            translated_titles.extend(translated_chunk.split("\n")[:-1])
            title_chunk = title + "\n"

    if title_chunk:
        translated_chunk = await async_translate(session, title_chunk)
        translated_titles.extend(translated_chunk.split("\n")[:-1])

    return translated_titles

async def translate_page(session, page_text):
    if len(page_text) <= MAX_TOKENS:
        return await async_translate(session, page_text)
    else:
        split_point = page_text.rfind("\n", 0, MAX_TOKENS)
        first_half = page_text[:split_point]
        second_half = page_text[split_point + 1:]
        first_half_translated = await async_translate(session, first_half)
        second_half_translated = await translate_page(session, second_half)
        return first_half_translated + "\n" + second_half_translated

async def translate_json_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    title_translation_dict = {}

    # Translate page titles
    title_list = [page['title'] for page in data['pages']]

    async with aiohttp.ClientSession() as session:
        translated_titles = await translate_titles(session, title_list)

        for original_title, translated_title in zip(title_list, translated_titles):
            title_translation_dict[original_title] = translated_title

        for page, translated_title in zip(data['pages'], translated_titles):
            page['title'] = translated_title

        # Translate lines with translated titles replaced
        for page in data['pages']:
            page_text = "\n".join(page['lines'])

            for jp_title, en_title in title_translation_dict.items():
                page_text = page_text.replace(f"[{jp_title}]", f"[{en_title}]")
            translated_text = await translate_page(session, page_text)
            page['lines'] = translated_text.split("\n")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Replace 'input.json' and 'output.json' with your desired file paths
async def main():
    await translate_json_file(INPUT_PATH, OUTPUT_PATH)

asyncio.run(main())