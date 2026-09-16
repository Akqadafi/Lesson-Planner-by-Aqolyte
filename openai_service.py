import os
from functools import lru_cache

from openai import OpenAI, APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError, APIStatusError


class GenerationUnavailableError(RuntimeError):
    """Safe actionable message without provider payloads or credentials."""


DEFAULT_MODEL = "gpt-5.4-mini"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Add it to .env (never commit .env).")
    return OpenAI(api_key=api_key, timeout=90.0, max_retries=1)


def generate_text(messages: list[dict[str, str]], *, model: str | None = None) -> str:
    """Generate text without logging prompts, responses, or credentials."""
    try:
        response = get_client().responses.create(
            model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
            input=messages,
            store=False,
            max_output_tokens=12000,
        )
    except AuthenticationError:
        raise GenerationUnavailableError("The API key was not accepted. Update the app's API configuration, then retry. Your saved draft is unchanged.") from None
    except RateLimitError as exc:
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get('error', body)
        code = error.get('code') if isinstance(error, dict) else None
        if code in {'credit_balance_exhausted', 'insufficient_quota', 'billing_hard_limit_reached'}:
            raise GenerationUnavailableError("OpenAI reports that API credits or quota are exhausted. The app owner needs to check API billing and project limits before retrying. You can still edit and download saved drafts.") from None
        raise GenerationUnavailableError("The AI service is temporarily rate-limited. Wait a moment and retry; your saved draft is unchanged.") from None
    except APITimeoutError:
        raise GenerationUnavailableError("The AI service took too long to respond. Please retry; your saved draft is unchanged.") from None
    except APIConnectionError:
        raise GenerationUnavailableError("The app could not connect to OpenAI. Check the server's internet access and retry. Your saved draft is unchanged.") from None
    except APIStatusError:
        raise GenerationUnavailableError("The AI service could not complete the request. Check the app's model configuration or retry shortly. Your saved draft is unchanged.") from None
    text = response.output_text.strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty response.")
    return text
