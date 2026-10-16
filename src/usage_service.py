
from decimal import Decimal

from src.database import get_connection


# USD per 1 million tokens.
# Update these values if OpenAI changes its prices.
MODEL_PRICING = {
    "gpt-6-luna": {
        "input": Decimal("0.10"),
        "cached_input": Decimal("0.01"),
        "output": Decimal("0.50"),
    }
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
):
    """Calculate estimated API cost in USD."""

    rates = MODEL_PRICING.get(model)

    if rates is None:
        return None

    regular_input_tokens = input_tokens - cached_tokens

    input_cost = (
        Decimal(regular_input_tokens)
        * rates["input"]
        / Decimal(1_000_000)
    )

    cached_cost = (
        Decimal(cached_tokens)
        * rates["cached_input"]
        / Decimal(1_000_000)
    )

    output_cost = (
        Decimal(output_tokens)
        * rates["output"]
        / Decimal(1_000_000)
    )

    return input_cost + cached_cost + output_cost


def extract_usage(response, task: str):
    """Extract usage details from an OpenAI response."""

    usage = response.usage

    if usage is None:
        return None

    input_details = getattr(
        usage, "input_tokens_details", None
    )

    cached_tokens = (
        getattr(input_details, "cached_tokens", 0) or 0
    )

    model = response.model

    cost = calculate_cost(
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cached_tokens=cached_tokens,
    )

    return {
        "task": task,
        "model": model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cached_tokens": cached_tokens,
        "total_tokens": usage.total_tokens,
        "estimated_cost_usd": (
            float(cost) if cost is not None else None
        ),
    }


def save_api_usage(usage_data):
    """Save one OpenAI request's usage to PostgreSQL."""

    if usage_data is None:
        return

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO api_usage (
                task,
                model,
                input_tokens,
                output_tokens,
                cached_tokens,
                total_tokens,
                estimated_cost_usd
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                usage_data["task"],
                usage_data["model"],
                usage_data["input_tokens"],
                usage_data["output_tokens"],
                usage_data["cached_tokens"],
                usage_data["total_tokens"],
                usage_data["estimated_cost_usd"],
            ),
        )


def get_usage_summary():
    """Return total recorded tokens and estimated API cost."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS request_count,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                SUM(estimated_cost_usd) AS total_cost_usd,
                COUNT(estimated_cost_usd) AS priced_requests
            FROM api_usage
            """
        ).fetchone()

    return dict(row)


def log_usage(response, task: str):
    """Extract and save token usage from an OpenAI response."""
    usage_data = extract_usage(response, task)
    save_api_usage(usage_data)
    return usage_data
