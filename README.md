# ScrapboxTranslator
Translate scrapbox project json file to English.
## Setup
1. `$ pip install -r requirements.txt`
2. Set `OPENAI_API_KEY` envrionmental variable in your computer.
([How to set your API key](https://qiita.com/LingmuSajun/items/8ac6b016e0ecc864851e))

## Usage
1. Export your project as json file at scrapbox.io. Do NOT check "Include metadata such as line.created and line.updated."
2. Edit `INPUT_PATH` variable in the code to load your exported json file.
```
INPUT_FILE = "input/sample.json"
```
3. Run the script
```
$ python main.py
```
4. Wait until the end of translation. It will take approximately `2.7 * {number of page}` seconds.
## Notes
- If you are not in OpenAI paid plan / if you are in your first 48 hours, you might face a rate limit. In that case, increase the value `SLEEP_DURATION` in  to speed down.
