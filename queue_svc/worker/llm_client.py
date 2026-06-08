import json
import logging
import re
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, Union, cast

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain_ollama import OllamaLLM

from src.models.models import CarModel
from src.settings.settings import settings


logger = logging.getLogger(__name__)


class NotValidCarAd(TypedDict):
    is_valid_ad: Literal[False]


class ValidCarAd(TypedDict):
    is_valid_ad: Literal[True]
    brand: str
    model: str
    engine: str
    year: str
    mileage: str
    price: NotRequired[str]


CarAdParseResult = Union[ValidCarAd, NotValidCarAd]


class LLMConfigurationError(RuntimeError):
    pass


class LangChainCarAdClient:
    def __init__(
        self,
        provider: Literal["local", "api-key"] | None = None,
        ollama_model: str | None = None,
        ollama_base_url: str | None = None,
        gemini_model: str | None = None,
        gemini_api_key: str | None = None,
        prompt_path: Path | None = None,
    ):
        self.provider = provider if provider is not None else settings.llm
        self.ollama_model = ollama_model if ollama_model is not None else settings.ollama_model
        self.ollama_base_url = (
            ollama_base_url if ollama_base_url is not None else settings.ollama_base_url
        )
        self.gemini_model = gemini_model if gemini_model is not None else settings.gemini_model
        self.gemini_api_key = (
            gemini_api_key if gemini_api_key is not None else settings.gemini_api_key
        )
        self.prompt_path = (
            prompt_path
            or Path(__file__).parents[1] / "ollama_api" / "prompts" / "ollama_prompt.txt"
        )
        self.prompt = self._load_prompt_template()
        self.llm = self._build_llm()

    def _load_prompt_template(self) -> PromptTemplate:
        template = self.prompt_path.read_text(encoding="utf-8")
        template = template.replace("{", "{{").replace("}", "}}")
        template = template.replace("<CAR_BRAND>", "{car_brand}")
        template = template.replace("<CAR_MODEL>", "{car_model}")
        template = template.replace("<AD_TEXT>", "{ad_text}")
        return PromptTemplate.from_template(template)

    def _build_llm(self):
        if self.provider == "local":
            logger.info(
                "Configuring local Ollama LLM provider model=%s base_url=%s",
                self.ollama_model,
                self.ollama_base_url,
            )
            return OllamaLLM(
                model=self.ollama_model,
                base_url=self.ollama_base_url,
                temperature=0,
            )

        if self.provider == "api-key":
            if not self.gemini_api_key:
                raise LLMConfigurationError("LLM=api-key requires GEMINI_API_KEY")
            logger.info(
                "Configuring Gemini LLM provider model=%s",
                self.gemini_model,
            )
            return GoogleGenerativeAI(
                model=self.gemini_model,
                google_api_key=self.gemini_api_key,
                temperature=0,
            )

        raise LLMConfigurationError(f"Unsupported LLM provider: {self.provider}")

    def _generate_prompt(self, ad_text: str, car: CarModel) -> str:
        return self.prompt.format(
            car_brand=car.manufacturer,
            car_model=car.model,
            ad_text=ad_text,
        )

    def process(self, ad_text: str, car: CarModel) -> CarAdParseResult:
        prompt = self._generate_prompt(ad_text=ad_text, car=car)
        response = self.llm.invoke(prompt)
        response_text = self._response_to_text(response)
        return self._parse_response(response_text)

    @staticmethod
    def _response_to_text(response: Any) -> str:
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "\n".join(str(item) for item in content)
        return str(content)

    @classmethod
    def _parse_response(cls, response_text: str) -> CarAdParseResult:
        data = json.loads(cls._extract_json(response_text))
        if not isinstance(data, dict):
            raise ValueError(f"LLM response must be a JSON object, got {type(data).__name__}")

        if data.get("is_valid_ad") is not True:
            return {"is_valid_ad": False}

        required_fields = ("brand", "model", "engine", "year", "mileage")
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                "Valid LLM response is missing required fields: "
                + ", ".join(missing_fields)
            )

        result: dict[str, Any] = {"is_valid_ad": True}
        for field in required_fields:
            result[field] = str(data[field])
        if "price" in data and data["price"] is not None:
            result["price"] = str(data["price"])
        return cast(ValidCarAd, result)

    @staticmethod
    def _extract_json(response_text: str) -> str:
        text = response_text.strip()
        fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
        if fenced_match:
            return fenced_match.group(1).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text
