from queue_svc.worker.llm_client import (
    CarAdParseResult,
    LangChainCarAdClient,
    NotValidCarAd,
    ValidCarAd,
)


class OllamaClient(LangChainCarAdClient):
    def __init__(self, model: str = "gemma3:4b"):
        super().__init__(provider="local", ollama_model=model)
