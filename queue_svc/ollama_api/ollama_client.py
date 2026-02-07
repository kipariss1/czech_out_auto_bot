import requests
from pathlib import Path
from typing import TypedDict, Literal, Union
from src.models.models import CarModel
import re


class NotValidCarAd(TypedDict):
    is_valid_ad: Literal[False]

class ValidCarAd(TypedDict):
    is_valid_ad: Literal[True]
    brand: str
    model: str
    engine: str
    year: str
    mileage: str

CarAdParseResult = Union[ValidCarAd, NotValidCarAd]


class OllamaClient:
    
    def __init__(self):
        self.url = "http://ollama:11434"
        self.prompt_path = Path(__file__).parent / "prompts" / "ollama_prompt.txt"

    def _generate_prompt(self, ad_text: str, car: CarModel) -> str:
        mapping = {
            "<CAR_BRAND>": car.manufacturer,
            "<CAR_MODEL>": car.model,
            "<AD_TEXT>": ad_text
        }
        with open(self.prompt_path, "r") as f:
            template = f.read()
        for k, v in mapping.items():
            template = re.sub(k, v, template)
        return template

    def process(self, ad_text: str, car: CarModel) -> CarAdParseResult:
        prompt = self._generate_prompt(ad_text, car)
        response = requests.post(
            f"{self.url}/api/generate",
            json={
                "model": "gemma3:4b",
                "prompt": prompt
            }
        )
        return response.json()["response"]