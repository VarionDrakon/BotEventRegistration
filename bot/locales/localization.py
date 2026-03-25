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
    
    async def get(self, key_path: str) -> str:
        if not key_path:
            return key_path
        
        parts = key_path.split('.')
        current = self.translations
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
        
        return str(current) if current is not None else key_path

localization = Localization()

async def initialize_localization():
    await localization.load_translations()