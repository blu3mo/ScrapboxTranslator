# ScrapboxTranslator
Translates scrapbox project json file to English.
## Usage
1. Set `OPENAI_API_KEY` envrionmental variable in your computer.
([How to set your API key](https://qiita.com/LingmuSajun/items/8ac6b016e0ecc864851e))

2. Edit `INPUT_PATH` variable in the code to load your file.
```
INPUT_PATH = "input_json/test1.json"
```
3. Run the script
```
$ python main.py
```
## Notes
- Since it uses GPT3.5 to generate translation, it is unstable. Do not expect every translation to be clean; some could be in weird format.
