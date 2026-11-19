from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.errors import AppError


async def ainvoke_structured(
    llm: Any,
    schema: type[BaseModel],
    messages: list[Any],
    max_attempts: int = 2,
) -> BaseModel:
    """Invoke `llm.with_structured_output(schema, include_raw=True)`.

    On a validation failure the Pydantic error is sent back to the model.
    At most `max_attempts` calls are made (default 2). This does not construct
    an OpenAI client; callers pass a fake in tests.
    """

    if max_attempts < 1:
        raise AppError(
            400,
            "ai_structured_output_invalid",
            "max_attempts must be at least 1.",
        )
    structured = llm.with_structured_output(schema, include_raw=True)
    conversation = list(messages)
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        result = await structured.ainvoke(conversation)
        try:
            parsed = _validated(result, schema)
        except (ValidationError, ValueError) as exc:
            last_error = exc
        else:
            return parsed
        if attempt + 1 >= max_attempts:
            break
        conversation = [
            *conversation,
            {"role": "assistant", "content": _raw_content(result)},
            {
                "role": "user",
                "content": (
                    "The previous response failed schema validation. "
                    "Return an object that satisfies the schema.\n"
                    f"{last_error}"
                ),
            },
        ]
    message = str(last_error) if last_error else "Structured output failed validation."
    raise AppError(502, "ai_structured_output_invalid", message)


def _validated(result: Any, schema: type[BaseModel]) -> BaseModel:
    if isinstance(result, schema):
        return result
    if isinstance(result, dict) and ("parsed" in result or "parsing_error" in result):
        error = result.get("parsing_error")
        parsed = result.get("parsed")
        if error is not None and parsed is None:
            if isinstance(error, ValidationError | ValueError):
                raise error
            raise ValueError(str(error))
        if parsed is None:
            raise ValueError(str(error) if error else "Structured output was empty.")
        if isinstance(parsed, schema):
            return parsed
        return schema.model_validate(parsed)
    return schema.model_validate(result)


def _raw_content(result: Any) -> str:
    if not isinstance(result, dict):
        return ""
    raw = result.get("raw")
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    content = raw.get("content") if isinstance(raw, dict) else getattr(raw, "content", None)
    if isinstance(content, str):
        return content
    return str(raw)
