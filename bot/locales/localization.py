import json
import logging
from pathlib import Path
from run import language

class Localization:
    def __init__(self, language: str = language):
        self.language = language
        self.translations = {}
    
    async def load_translations(self):
        try:
            file_path = Path(f"locales/{self.language}.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError as e:
            logging.error(f"{e}")
    
    def get(self, key: str, **kwargs) -> str:
        if not key:
            return key
        
        key_path = key.split('.')
        value = self.translations

        for k in key_path:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return key

        if kwargs:
            try:
                if isinstance(value, list):
                    items = []
                    for val in value:
                        item = str(val)
                        try:
                            items.append(item.format(**kwargs))
                        except KeyError as e:
                            items.append(item)
                            logging.error(f"Error:> {e} [:] {item} + {kwargs}")
                    return "".join(items)
                else:
                    return value.format(**kwargs)
            except KeyError as e:
                logging.error(f"Error:> {e} [:] {key}")
                return value
        elif isinstance(value, list):
            return "".join(value)
        
        return str(value)

localization = Localization()

async def initialize_localization():
    await localization.load_translations()