from pathlib import Path
from types import SimpleNamespace

import pytest

from queue_svc.worker.llm_client import LLMConfigurationError, LangChainCarAdClient


def test_prompt_template_formats_car_and_ad_text(tmp_path: Path):
    prompt_path = tmp_path / "prompt.txt"
    prompt_path.write_text(
        "Brand=<CAR_BRAND>\nModel=<CAR_MODEL>\nJSON={\"ok\": true}\nText=<AD_TEXT>",
        encoding="utf-8",
    )

    client = LangChainCarAdClient(provider="local", prompt_path=prompt_path)

    prompt = client._generate_prompt(
        ad_text="BMW F20 2016",
        car=SimpleNamespace(manufacturer="BMW", model="F20"),
    )

    assert "Brand=BMW" in prompt
    assert "Model=F20" in prompt
    assert 'JSON={"ok": true}' in prompt
    assert "Text=BMW F20 2016" in prompt


def test_parse_response_extracts_json_from_text():
    response = """
    ```json
    {
      "is_valid_ad": true,
      "brand": "BMW",
      "model": "F20",
      "engine": "2.0",
      "year": 2016,
      "mileage": 120000
    }
    ```
    """

    assert LangChainCarAdClient._parse_response(response) == {
        "is_valid_ad": True,
        "brand": "BMW",
        "model": "F20",
        "engine": "2.0",
        "year": "2016",
        "mileage": "120000",
    }


def test_api_key_provider_requires_gemini_api_key():
    with pytest.raises(LLMConfigurationError, match="GEMINI_API_KEY"):
        LangChainCarAdClient(provider="api-key", gemini_api_key="")
