import json
import asyncio
import aiohttp
import openai
import re
import tiktoken

MAX_TOKENS = 1800 # 4096 (gpt3.5 max token) - 200 (prompt) - 2000 (output)
INPUT_PATH = "input_json/blu3mo_filtered.json"
OUTPUT_PATH = "output_json/blu3mo_filtered.json"

PROMPT = """
You are a language translator.
Target Language: English

# Task
Translate texts from the source language to English, and output the translated texts.

# Rules
- Always preserve \\n and \\s.
- Keep brackets unchanged: Brackets of [text] and [text.icon] must be kept. The content inside square brackets must never be changed.
- Preserve markup symbols like >, `, [].

# Example
Original Text:
[りんご]\\n\\s\\sバナナ\\n\\s\\s\\s[ダイアモンド.icon]

Translated Text:
[apple]\\n\\s\\sbanana\\n\\s\\s\\s[diamond.icon]
"""

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

async def async_translate(session, text):
    # Replace leading spaces/tabs/full width spaces with \s
    text = re.sub(r'^([ \t　]+)', lambda m: '\\s' * len(m.group(1)), text, flags=re.MULTILINE)

    # Replace newlines with \n
    text = text.replace('\n', '\\n')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": 0,
        "max_tokens": 2000,
    }

    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as resp:
        response = await resp.json()
        print(response)
        translated_text = response["choices"][0]["message"]["content"]

    # Replace \n back to newline
    translated_text = translated_text.replace('\\n', '\n')

    # Replace \s back to spaces
    translated_text = re.sub(r'\\s', ' ', translated_text)

    return translated_text

async def translate_titles(session, title_list):
    translated_titles = []
    title_chunk = ""

    for title in title_list:
        tokens_count = num_tokens_from_string(title_chunk + title + "\n", "p50k_base")
        if tokens_count < MAX_TOKENS:
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
    token_count = num_tokens_from_string(page_text, "cl100k_base")
    if token_count <= MAX_TOKENS:
        return await async_translate(session, page_text)
    else:
        lines = page_text.split("\n")
        current_token_count = 0
        split_index = 0

        for idx, line in enumerate(lines):
            line_token_count = num_tokens_from_string(line, "cl100k_base")
            if current_token_count + line_token_count >= MAX_TOKENS:
                split_index = idx
                break
            else:
                current_token_count += line_token_count

        first_half = "\n".join(lines[:split_index])
        second_half = "\n".join(lines[split_index:])
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
        translation_tasks = []

        for page in data['pages']:
            page_text = "\n".join(page['lines'])

            for jp_title, en_title in title_translation_dict.items():
                page_text = page_text.replace(f"{jp_title}", f"{en_title}")

            translation_tasks.append(translate_page(session, page_text))

        translated_texts = await asyncio.gather(*translation_tasks)

        for page, translated_text in zip(data['pages'], translated_texts):
            page['lines'] = translated_text.split("\n")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def main():
    await translate_json_file(INPUT_PATH, OUTPUT_PATH)

asyncio.run(main())
