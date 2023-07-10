import json
import asyncio
import aiohttp
import openai
import tiktoken
import os
from asyncio import Semaphore
from translateTitles import fetch_title_translation
from translatePages import fetch_page_translation
from util import split_titles

INPUT_FILE = "input/blu3mo-public.json"
OUTPUT_DIR = "output"

SLEEP_DURATION = 60 / (90000 / 4000)
# 90000 token per min. 4000 token per request. 90000/4000 = 22.5 requests per min. 60/22.5 = 2.67 sec per request

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

async def translate_titles(titles):
    """
    Translates a list of titles from OpenAI API

    Args:
        titles (list): A list of titles to be translated

    Returns:
        dict: A dictionary of original titles & translated titles
    """
    max_tokens = 800
    split_title_arrays = split_titles(titles, max_tokens)

    translations = {title: title for title in titles}

    print(f"Translation of {len(titles)} titles started.")

    tasks = []
    for title_array in split_title_arrays:
        # convert array to string in JSON format
        title_array_str = json.dumps(title_array, ensure_ascii=False)
        tasks.append(asyncio.create_task(fetch_title_translation(title_array_str)))
        await asyncio.sleep(SLEEP_DURATION)

    results = []
    for task in tasks:
        await task  # Wait for task to complete
        results.append(task.result())  # Get the task's result

    for translated_titles in results:
        for original, translated in translated_titles.items():
            translations[original] = translated

    print(f"Translation of {len(titles)} titles completed.")

    return translations

async def translate_pages(pages):
    """
    Translates a list of pages from OpenAI API

    Args:
        pages (dict): A dictionary of pageId and page

    Returns:
        dict: A dictionary of pageId and translated page
    """
    translations = {}
    tasks = []
    
    print(f"Translation of {len(pages)} pages started.")

    for pageId, page in pages.items():
        # run the translation in async and wait for sleep_duration
        tasks.append(asyncio.create_task(fetch_page_translation(pageId, page)))
        await asyncio.sleep(SLEEP_DURATION) 

    # gather all the tasks
    results = []
    for task in tasks:
        await task  # Wait for task to complete
        results.append(task.result())  # Get the task's result

    for (pageId, translatedPage) in results:
        translations[pageId] = translatedPage

    print(f"Translation of {len(pages)} pages completed.")

    return translations

async def main():
    # read input json
    with open(INPUT_FILE, "r") as f:
        input_json = json.load(f)

    # translate the list of titles. obtain dictionary of original titles to translated titles
    titles = [page["title"] for page in input_json["pages"]]
    translated_titles = await translate_titles(titles)
    print(translated_titles)

    # Join lines in each page into a single string, and create a dictionary of pageId and string
    pages = {}
    for page in input_json["pages"]:
        pages[page["id"]] = '\n'.join(page["lines"])
    
    # for each pages, replace all occurrences of links to other pages with the translated title
    for pageId, page in pages.items():
        print("Replacing links in page " + page[:15].replace('\n', ' ') + "...")
        for title in translated_titles:
            page = page.replace('[{}]'.format(title), '[' + translated_titles[title] + ']')
        pages[pageId] = page

    # translate the list of pages. obtain list of pages
    translated_pages = await translate_pages(pages)

    output_json = input_json
    # replace original pages with translated pages
    for page in output_json["pages"]:
        pageId = page["id"]
        old_title = page["title"]
        page["title"] = translated_titles[old_title]
        page["lines"] = (translated_pages[pageId] or "").split('\n') # Split the translated page back into lines
        page["lines"].insert(0, translated_titles[old_title]) # Insert the translated title as the first line

    print("Final translations are ready. Writing them into the output JSON file.")

    # make a new directiroy of OUTPUT_DIR if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # get input file name
    input_file_name = INPUT_FILE.split('/')[-1]

    # write output json
    with open(f"{OUTPUT_DIR}/{input_file_name}", "w") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=4)

    print("Output JSON file written successfully.")

asyncio.run(main())
