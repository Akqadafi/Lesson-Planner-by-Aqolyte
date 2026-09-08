import os
from functools import lru_cache

from openai import OpenAI


DEFAULT_MODEL = "gpt-5.4-mini"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Add it to .env (never commit .env).")
    return OpenAI(api_key=api_key)


def generate_text(messages: list[dict[str, str]], *, model: str | None = None) -> str:
    """Generate text without logging prompts, responses, or credentials."""
    response = get_client().responses.create(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        input=messages,
        store=False,
    )
    text = response.output_text.strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty response.")
    return text
