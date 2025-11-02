from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from functools import lru_cache
from typing import Iterable, Mapping

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

LOGGER = logging.getLogger(__name__)

CJK_REGEX = re.compile(r"[\u3400-\u9FFF]")
MAX_TOKENS_PER_REQUEST = int(os.getenv("RINGSHELL_TRANSLATION_MAX_TOKENS", "4000"))
TRANSLATION_MODEL = os.getenv("RINGSHELL_TRANSLATION_MODEL", "openai:gpt-4o-mini")
TRANSLATION_TEMPERATURE = float(os.getenv("RINGSHELL_TRANSLATION_TEMPERATURE", "0.0"))


class TranslationError(RuntimeError):
    """Raised when translation fails irrecoverably."""


def _chunks(items: list[tuple[str, str]], max_tokens: int) -> Iterable[list[tuple[str, str]]]:
    """Split items into batches capped by max_tokens to avoid overly long prompts."""
    batch: list[tuple[str, str]] = []
    total = 0
    for item in items:
        size = len(item[1])
        if batch and total + size > max_tokens:
            yield batch
            batch = []
            total = 0
        batch.append(item)
        total += size
    if batch:
        yield batch


@lru_cache(maxsize=1)
def _get_translation_model():
    try:
        return init_chat_model(model=TRANSLATION_MODEL, temperature=TRANSLATION_TEMPERATURE)
    except Exception as exc:  # pragma: no cover - depends on external configuration
        raise TranslationError("Failed to initialise translation model") from exc


def _build_prompt(items: list[tuple[str, str]], target_locale: str) -> list:
    instructions = (
        "You are a translation engine. Translate each input text to the target locale while preserving all numbers, "
        "tickers, URLs, and proper nouns. Return a strict JSON object where each key matches the input id."
    )
    examples = [{"id": identifier, "text": text} for identifier, text in items]
    payload = json.dumps({"target_locale": target_locale, "items": examples}, ensure_ascii=False)
    return [
        SystemMessage(content=instructions),
        HumanMessage(
            content=(
                "Translate every item in the payload to the specified target locale. Respond ONLY with a JSON object "
                "mapping ids to translations. Do not add explanations.\n\n"
                f"{payload}"
            )
        ),
    ]


async def _translate_batch(items: list[tuple[str, str]], target_locale: str) -> Mapping[str, str]:
    """Translate a batch of texts into the target locale."""
    if not items:
        return {}
    model = _get_translation_model()
    prompt = _build_prompt(items, target_locale)
    try:
        response = await model.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else response
        if isinstance(content, str):
            return json.loads(content)
        if isinstance(content, list):
            combined = "".join(str(part) for part in content)
            return json.loads(combined)
        raise TranslationError("Unexpected translation response format")
    except json.JSONDecodeError as exc:
        raise TranslationError("Translation output is not valid JSON") from exc
    except Exception as exc:
        raise TranslationError("Translation model invocation failed") from exc


async def translate_items(items: list[tuple[str, str]], target_locale: str) -> Mapping[str, str]:
    """Translate text items using the configured translation model.

    Args:
        items: List of (identifier, text) tuples.
        target_locale: BCP 47 locale code for the translation target.

    Returns:
        Mapping of item identifiers to translated strings. Items that could not be translated will map to the original
        text.
    """
    filtered_items = [(identifier, text) for identifier, text in items if identifier and text]
    if not filtered_items:
        return {}

    if target_locale.lower().startswith("en"):
        # Already English; no translation required
        return {identifier: text for identifier, text in filtered_items}

    pending: dict[str, str] = {}
    try:
        batches = list(_chunks(filtered_items, MAX_TOKENS_PER_REQUEST))
        results = await asyncio.gather(
            *[_translate_batch(batch, target_locale) for batch in batches],
            return_exceptions=True
        )

        for batch, result in zip(batches, results):
            if isinstance(result, Exception):
                LOGGER.warning("Translation batch failed: %s", result)
                for identifier, text in batch:
                    pending[identifier] = text
                continue
            for identifier, text in batch:
                translated = result.get(identifier)
                if translated and CJK_REGEX.search(translated):
                    # Ensure translation looks like the requested locale (rough heuristic)
                    pending[identifier] = translated.strip()
                else:
                    pending[identifier] = translated.strip() if translated else text
    except TranslationError as exc:
        LOGGER.error("Translation failed: %s", exc)
        return {identifier: text for identifier, text in filtered_items}

    return pending
