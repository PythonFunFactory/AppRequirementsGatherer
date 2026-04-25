import json
import os
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

    # Build a summary request as the last user message
    extraction_messages = messages + [
        {"role": "user", "content": extraction_prompt}
    ]

    response = await client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=extraction_messages,
    )
    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw)
