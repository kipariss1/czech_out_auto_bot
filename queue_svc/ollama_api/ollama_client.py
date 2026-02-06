import requests
from pathlib import Path
from queue_svc.bazos_api.auto_bazos_api import AutoAdvertisementPage


class OllamaClient:
    
    def __init__(self):
        self.url = "http://ollama:11434"
        self.prompt_path = Path(__file__).parent / "prompts" / "ollama_prompt.txt"

    def process(ad_text: str):
        pass