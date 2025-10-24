"""LLM provider abstraction for Claude and OpenAI."""

import anthropic
import openai
from ..config import get_settings


def call_llm(messages: list[dict], system_prompt: str) -> str:
    """
    Call the configured LLM provider (Claude or OpenAI).

    Args:
        messages: List of message dicts with role and content
        system_prompt: System prompt to guide the LLM

    Returns:
        Assistant's response text

    Raises:
        Exception: If LLM call fails
    """
    settings = get_settings()

    if settings.llm_provider == "openai":
        # OpenAI API
        client = openai.OpenAI(api_key=settings.openai_api_key)

        # OpenAI format includes system message in messages array
        api_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=api_messages,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature
        )

        return response.choices[0].message.content

    else:
        # Claude API (default)
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Claude uses separate system parameter
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=settings.temperature
        )

        return response.content[0].text


def get_provider_info() -> tuple[str, str]:
    """
    Get the current provider and model name.

    Returns:
        Tuple of (provider_name, model_name)
    """
    settings = get_settings()

    if settings.llm_provider == "openai":
        return ("OpenAI", settings.openai_model)
    else:
        return ("Claude", settings.claude_model)
