
"""Reusable security checks for TravelAdvisor AI."""

import re
from typing import Any

MAX_MESSAGE_LENGTH = 2000
MAX_TOOL_CALLS_PER_TURN = 3


def validate_user_message(user_text: str) -> str:
    """Validate and normalize a user message."""

    if not isinstance(user_text, str):
        raise ValueError("Message must be text.")

    cleaned = user_text.strip()

    if not cleaned:
        raise ValueError("Please enter a message.")

    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"Message is too long. Please keep it under "
            f"{MAX_MESSAGE_LENGTH} characters."
        )

    return cleaned


def validate_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    allowed_tools: dict[str, set[str]],
    calls_so_far: int = 0,
) -> dict[str, Any]:
    """
    Validate a proposed tool call before execution.

    allowed_tools maps tool names to permitted argument names.
    This function does not execute the tool.
    """

    if not isinstance(tool_name, str):
        raise ValueError("Invalid tool name.")

    if tool_name not in allowed_tools:
        raise ValueError("Tool is not allowed.")

    if not isinstance(calls_so_far, int) or isinstance(
        calls_so_far, bool
    ) or calls_so_far < 0:
        raise ValueError("Invalid tool-call counter.")

    if calls_so_far >= MAX_TOOL_CALLS_PER_TURN:
        raise ValueError("Tool-call limit reached.")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object.")

    permitted_arguments = allowed_tools[tool_name]

    if not isinstance(permitted_arguments, set):
        raise ValueError("Invalid tool configuration.")

    if set(arguments) != permitted_arguments:
        raise ValueError(
            "Missing or unexpected tool arguments."
        )

    for name, value in arguments.items():
        if not isinstance(value, str):
            raise ValueError(
                f"Argument '{name}' must be text."
            )

        if not value.strip() or len(value) > 100:
            raise ValueError(
                f"Argument '{name}' has an invalid length."
            )

        if re.search(r"[\x00-\x1f\x7f]", value):
            raise ValueError(
                f"Argument '{name}' contains control characters."
            )

    return {
        name: value.strip()
        for name, value in arguments.items()
    }
