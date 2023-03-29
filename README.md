# ScrapboxTranslator
Translate scrapbox project json file to English.
## Usage
1. Set `OPENAI_API_KEY` envrionmental variable in your computer.
([How to set your API key](https://qiita.com/LingmuSajun/items/8ac6b016e0ecc864851e))
2. Export scrapbox json file. Do NOT check "Include metadata such as line.created and line.updated."
3. Edit `INPUT_PATH` variable in the code to load your exported json file.
```
INPUT_PATH = "input_json/test1.json"
```
4. Run the script
```
$ python main.py
```
## Notes
- Since it uses GPT3.5 to generate translation, it is unstable. Do not expect every translation to be clean; some could be in weird format.
- If you are not in OpenAI paid plan or during your first 48 hours, you might face rate limit. In that case, lower the number of `Semaphore(40)` to speed down the rate of API request.
