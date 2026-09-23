import os
import re
from functools import lru_cache
from generation_limits import reserve_attempt, GenerationLimitError

from openai import OpenAI, APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError, APIStatusError


class GenerationUnavailableError(RuntimeError):
    """Safe actionable message without provider payloads or credentials."""


DEFAULT_MODEL = "gpt-5.4-mini"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Add it to .env (never commit .env).")
    return OpenAI(api_key=api_key, timeout=90.0, max_retries=0)


def generate_text(messages: list[dict[str, str]], *, model: str | None = None,
                  response_schema: dict | None = None,
                  schema_name: str = "generated_response") -> str:
    """Generate text, optionally constrained by a strict provider-side JSON Schema."""
    if not isinstance(messages, list) or not messages or any(
        not isinstance(item, dict) or item.get('role') not in {'system', 'user', 'assistant'}
        or not isinstance(item.get('content'), str) for item in messages
    ):
        raise GenerationUnavailableError('Invalid generation input. Your saved draft is unchanged.')
    if sum(len(item['content']) for item in messages) > 150000:
        raise GenerationUnavailableError('The lesson context is too large. Shorten the source excerpts or sections before generating.')
    if response_schema is not None:
        if (not isinstance(response_schema, dict) or response_schema.get('type') != 'object'
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', schema_name)):
            raise GenerationUnavailableError('Invalid structured-output configuration. Your saved draft is unchanged.')
    client = get_client()
    try:
        reserve_attempt()
    except GenerationLimitError as exc:
        raise GenerationUnavailableError(str(exc)) from None
    try:
        request = {
            'model': model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
            'input': messages,
            'store': False,
            'max_output_tokens': 12000,
        }
        if response_schema is not None:
            request['text'] = {'format': {
                'type': 'json_schema',
                'name': schema_name,
                'strict': True,
                'schema': response_schema,
            }}
        response = client.responses.create(**request)
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
    if response.status != 'completed' or not isinstance(response.output_text, str):
        raise GenerationUnavailableError('The AI response was incomplete. Your saved draft is unchanged; retry with a smaller request.')
    text = response.output_text.strip()
    if not text or len(text) > 200000:
        raise GenerationUnavailableError('The AI response was empty or too large. Your saved draft is unchanged.')
    return text
