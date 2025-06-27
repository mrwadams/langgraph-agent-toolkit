# Tools Module

This module contains reusable tools that can be imported across different agents.

## Available Tools

### Search Tools
- `google_search`: Search the web using Google Search via Gemini

### Weather Tools  
- `get_weather`: Get current weather for a specific city (mock implementation)

## Usage

```python
# Import all tools
from tools import all_tools

# Import specific tools
from tools.search import google_search
from tools.weather import get_weather
```

## Adding New Tools

1. Create a new file in the `tools/` directory (e.g., `tools/new_category.py`)
2. Define your tool using the `@tool` decorator from `langchain_core.tools`
3. Import and add your tool to `all_tools` in `tools/__init__.py`

## Tool Categories

- **search.py**: Web search and information retrieval tools
- **weather.py**: Weather-related tools