# Tools Module

This module contains reusable tools that can be imported across different agents.

## Available Tools

### Search Tools
- `google_search`: Search the web using Google Search via Gemini

### Weather Tools  
- `get_weather`: Get current weather for a specific city (mock implementation)

### Database Tools
- `list_database_tables`: List all available tables in the PostgreSQL database
- `get_database_schema`: Get schema information and sample rows for specified tables
- `query_database`: Execute SELECT queries against the PostgreSQL database (read-only)
- `check_database_query`: Validate SQL query syntax and safety before execution

## Usage

```python
# Import all tools
from tools import all_tools

# Import specific tools
from tools.search import google_search
from tools.weather import get_weather
from tools.database import list_database_tables, query_database
```

## Adding New Tools

1. Create a new file in the `tools/` directory (e.g., `tools/new_category.py`)
2. Define your tool using the `@tool` decorator from `langchain_core.tools`
3. Import and add your tool to `all_tools` in `tools/__init__.py`

## Tool Categories

- **search.py**: Web search and information retrieval tools
- **weather.py**: Weather-related tools
- **database.py**: PostgreSQL database query and schema tools

## Database Configuration

To use database tools, set these environment variables in your `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

**Security Note**: Database tools only allow read-only SELECT queries for safety.