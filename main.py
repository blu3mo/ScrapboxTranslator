import json
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

def translate(text, role="user"):
    print(text)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text}
        ]
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

def translate_titles(title_list):
    translated_titles = []
    title_chunk = ""

    for title in title_list:
        if len(title_chunk) + len(title) + 1 < MAX_TOKENS:
            title_chunk += title + "\n"
        else:
            translated_chunk = translate(title_chunk, role="title_translation")
            translated_titles.extend(translated_chunk.split("\n")[:-1])
            title_chunk = title + "\n"

    if title_chunk:
        translated_chunk = translate(title_chunk, role="title_translation")
        translated_titles.extend(translated_chunk.split("\n")[:-1])

    return translated_titles

def translate_page(page_text):
    if len(page_text) <= MAX_TOKENS:
        return translate(page_text, role="page_translation")
    else:
        split_point = page_text.rfind("\n", 0, MAX_TOKENS)
        first_half = page_text[:split_point]
        second_half = page_text[split_point + 1:]
        return translate_page(first_half) + "\n" + translate_page(second_half)

def translate_json_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    title_translation_dict = {}

    # Translate page titles
    title_list = [page['title'] for page in data['pages']]
    print(title_list)
    translated_titles = translate_titles(title_list)
    print("title translation done");

    for original_title, translated_title in zip(title_list, translated_titles):
        title_translation_dict[original_title] = translated_title

    print(translated_titles)

    for page, translated_title in zip(data['pages'], translated_titles):
        page['title'] = translated_title


    # Translate lines with translated titles replaced
    for page in data['pages']:
        page_text = "\n".join(page['lines'])

        for jp_title, en_title in title_translation_dict.items():
            page_text = page_text.replace(f"[{jp_title}]", f"[{en_title}]")

        translated_text = translate_page(page_text)
        page['lines'] = translated_text.split("\n")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("start")
translate_json_file(INPUT_PATH, OUTPUT_PATH)
