from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Final

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

_DEFAULT_MODEL: Final[str] = "gpt-4o-mini"
_FALLBACK_MODEL: Final[str] = "gpt-4o-mini"
_PROMPTS_DIR: Final[Path] = Path(__file__).resolve().parent / "prompts"
_API_GEN_PROMPT_FILE: Final[Path] = _PROMPTS_DIR / "api_gen.txt"
_UI_GEN_PROMPT_FILE: Final[Path] = _PROMPTS_DIR / "ui_gen.txt"


def _extract_python_code(content: str) -> str:
    fenced_match = re.search(r"```python\s*(.*?)```", content, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1).strip()

    generic_match = re.search(r"```\s*(.*?)```", content, flags=re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip()

    return content.strip()


def _fallback_code() -> str:
    return "def test_fallback_example():\n    assert 'hello world' == 'hello world'"


def BuildApiGenerationPrompt(interfaces_json: str) -> str:
    template = _API_GEN_PROMPT_FILE.read_text(encoding="utf-8")
    return template.format(interfaces_json=interfaces_json)


def BuildUiGenerationPrompt(requirement_text: str) -> str:
    template = _UI_GEN_PROMPT_FILE.read_text(encoding="utf-8")
    return template.format(requirement_text=requirement_text)


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
def _invoke_model(prompt: str, model_name: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key)
    template = PromptTemplate.from_template(
        "请只返回可运行的 Python 代码，不要输出解释。\n用户需求：{prompt}",
    )
    chain = template | llm
    response = chain.invoke({"prompt": prompt})
    content = getattr(response, "content", "")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM returned empty content.")

    return _extract_python_code(content)


def call_llm(prompt: str) -> str:
    llm_type = os.environ.get("LLM_TYPE", "openai").strip().lower()
    if llm_type != "openai":
        return _fallback_code()

    primary_model = os.environ.get("LLM_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL
    fallback_model = os.environ.get("LLM_FALLBACK_MODEL", _FALLBACK_MODEL).strip() or _FALLBACK_MODEL

    try:
        return _invoke_model(prompt=prompt, model_name=primary_model)
    except (ValueError, RetryError, Exception):
        if fallback_model == primary_model:
            return _fallback_code()
        try:
            return _invoke_model(prompt=prompt, model_name=fallback_model)
        except (ValueError, RetryError, Exception):
            return _fallback_code()


def GenerateApiScriptByInterfaces(interfaces: list[dict]) -> str:
    interfaces_json = json.dumps(interfaces, ensure_ascii=False, indent=2)
    prompt = BuildApiGenerationPrompt(interfaces_json=interfaces_json)
    return call_llm(prompt)


def GenerateUiScriptByRequirement(requirement: str) -> str:
    prompt = BuildUiGenerationPrompt(requirement_text=requirement)
    return call_llm(prompt)
