import json
import os
from json_repair import repair_json
from pathlib import Path
from typing import AsyncGenerator, List
import anthropic
from ..config import settings

MODEL = "claude-sonnet-4-6"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

_client: anthropic.AsyncAnthropic = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


async def stream_response(messages: List[dict]) -> AsyncGenerator[str, None]:
    system_prompt = load_prompt("requirements_system.md")
    client = get_client()
    async with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def generate_requirements_json(messages: List[dict]) -> dict:
    extraction_prompt = load_prompt("pdf_generation.md")
    client = get_client()

    async def _call(extra_instruction: str = "") -> anthropic.types.Message:
        return await client.messages.create(
            model=MODEL,
            max_tokens=8192,
            messages=messages + [{"role": "user", "content": extraction_prompt + extra_instruction}],
        )

    response = await _call()

    if response.stop_reason == "max_tokens":
        # Output was truncated — retry asking for brevity
        response = await _call(
            "\n\nIMPORTANT: Be very concise. Keep every field to one or two sentences. "
            "The entire JSON response must fit within a single reply."
        )
        if response.stop_reason == "max_tokens":
            raise ValueError("Conversation too long to generate PDF in one pass.")

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(repair_json(raw))
