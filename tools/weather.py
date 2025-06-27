from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """
    Use this tool to get the current weather for a specific city.
    Returns a string describing the weather.
    """
    if "london" in city.lower():
        return "It's currently 15°C and cloudy in London."
    elif "paris" in city.lower():
        return "It's a sunny 22°C in Paris."
    else:
        return f"Sorry, I don't have the weather for {city}."