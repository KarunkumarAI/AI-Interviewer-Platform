
import os

from backend.app.llm.providers import (
    gemini_chat,
    openai_chat,
    openrouter_chat,
)
from backend.app.core.language import resolve_language


PROVIDERS = {
    "gemini": gemini_chat,
    "openai": openai_chat,
    "openrouter": openrouter_chat,
}


def chat(
    message: str,
    language: str,
    provider: str | None = None,
) -> tuple[str, str]:

    language = resolve_language(message, language)

    system = (
        "You are the general AI chatbot in a multilingual assistant. "
        f"Reply in {language}. "
        "Do not claim to use uploaded documents or RAG evidence."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": message},
    ]

    preferred = (
        provider or os.getenv("LLM_PROVIDER", "gemini")
    ).strip().lower()

    if preferred not in PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider: {preferred}. "
            f"Available providers: {', '.join(PROVIDERS)}"
        )

    fallback_enabled = (
        os.getenv("LLM_FALLBACK_ENABLED", "false").strip().lower()
        == "true"
    )

    if fallback_enabled:
        order = [preferred] + [
            name for name in PROVIDERS if name != preferred
        ]
    else:
        order = [preferred]

    errors = []

    for name in order:
        try:
            response = PROVIDERS[name](messages)
            return response, name

        except Exception as exc:
            # Avoid printing request URLs, which may contain API keys.
            if hasattr(exc, "response") and exc.response is not None:
                detail = (
                    f"HTTP {exc.response.status_code}: "
                    f"{exc.response.text[:1000]}"
                )
            elif isinstance(exc, RuntimeError):
                detail = str(exc)[:1000]
            else:
                detail = type(exc).__name__

            errors.append(f"{name}: {detail}")

    raise RuntimeError(
        "No configured LLM provider succeeded: "
        + "; ".join(errors)
    )
