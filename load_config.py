import json

SAVE_FILE = "bot_data.json"

def load_config() -> dict: #загрузка конфига
    with open(SAVE_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_config(config): #его сохранение
    with open(SAVE_FILE,"w",encoding="utf-8") as f:
        json.dump(config,f,ensure_ascii=False,indent=4)