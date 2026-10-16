"""External tools the model can call.

Both APIs are free and need no API key:
- Open-Meteo: geocoding + daily weather forecast
- Frankfurter: currency exchange rates (ECB data)
"""

import json
from datetime import date, timedelta

import requests

TIMEOUT = 10

WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle",
    55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "rain showers", 82: "violent rain showers", 95: "thunderstorm",
    96: "thunderstorm with hail", 99: "thunderstorm with hail",
}


def get_weather_forecast(city: str, start_date: str | None = None, days: int = 3) -> dict:
    """Daily forecast for a city. Open-Meteo only forecasts ~16 days ahead."""

    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=TIMEOUT,
    ).json()

    if not geo.get("results"):
        return {"error": f"Could not find a location called '{city}'."}

    place = geo["results"][0]
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = start + timedelta(days=max(days, 1) - 1)

    if start > today + timedelta(days=15):
        return {
            "error": "Forecasts are only available about 16 days ahead. "
                     "The trip is too far in the future for a forecast."
        }

    # Clamp to the supported window.
    start = max(start, today)
    end = min(end, today + timedelta(days=15))

    data = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_probability_max",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "timezone": "auto",
        },
        timeout=TIMEOUT,
    ).json()

    daily = data.get("daily", {})
    forecast = []
    for i, day in enumerate(daily.get("time", [])):
        forecast.append({
            "date": day,
            "conditions": WEATHER_CODES.get(daily["weather_code"][i], "unknown"),
            "temp_min_c": daily["temperature_2m_min"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
            "rain_chance_percent": daily["precipitation_probability_max"][i],
        })

    return {"location": f"{place['name']}, {place.get('country', '')}", "forecast": forecast}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount using the latest ECB rate via Frankfurter."""

    response = requests.get(
        "https://api.frankfurter.dev/v1/latest",
        params={
            "amount": amount,
            "base": from_currency.upper(),
            "symbols": to_currency.upper(),
        },
        timeout=TIMEOUT,
    )

    if response.status_code != 200:
        return {"error": f"Could not convert {from_currency} to {to_currency}."}

    data = response.json()
    return {
        "amount": data["amount"],
        "from": data["base"],
        "to": to_currency.upper(),
        "converted": data["rates"].get(to_currency.upper()),
        "rate_date": data["date"],
    }


# Tool definitions in the Responses API format.
FUNCTION_TOOLS = [
    {
        "type": "function",
        "name": "get_weather_forecast",
        "description": (
            "Get a daily weather forecast for a city. Only works for dates "
            "within the next ~16 days."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Rome'"},
                "start_date": {
                    "type": ["string", "null"],
                    "description": "First day, YYYY-MM-DD. Null means today.",
                },
                "days": {"type": "integer", "description": "Number of days (1-16)"},
            },
            "required": ["city", "start_date", "days"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "convert_currency",
        "description": "Convert an amount between two currencies at the latest rate.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from_currency": {"type": "string", "description": "ISO code, e.g. EUR"},
                "to_currency": {"type": "string", "description": "ISO code, e.g. JPY"},
            },
            "required": ["amount", "from_currency", "to_currency"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

TOOL_FUNCTIONS = {
    "get_weather_forecast": get_weather_forecast,
    "convert_currency": convert_currency,
}


def run_tool(name: str, arguments_json: str) -> str:
    """Execute a tool call and return a JSON string. Never raises."""

    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = func(**json.loads(arguments_json))
    except Exception as exc:  # network errors, bad arguments, etc.
        result = {"error": f"Tool '{name}' failed: {exc}"}

    return json.dumps(result)
