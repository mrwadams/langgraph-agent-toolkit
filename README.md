# LangGraph Chatbot Reference Implementation

A comprehensive reference implementation of a LangGraph-based chatbot with FastAPI server, CLI client, and modular tool system.

## Features

- **Multiple Agent Implementations**: Basic chatbot and tool-enabled chatbot
- **FastAPI Server**: RESTful API with streaming support and graph visualization
- **Rich CLI Client**: Terminal client with markdown rendering, streaming, and tool indicators
- **Modular Tools System**: Reusable tools organized by category
- **Dynamic Visualization**: Enhanced graph visualization showing available tools
- **Streaming Support**: Real-time response streaming with thinking animations

## Project Structure

```
langgraph-chatbot/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── chatbot.py         # Basic chatbot without tools
│   └── chatbot_with_tools.py  # Advanced chatbot with tools
├── tools/                 # Reusable tools module
│   ├── __init__.py
│   ├── README.md
│   ├── search.py          # Google search tool
│   └── weather.py         # Weather tool
├── server.py              # FastAPI server
├── cli_client.py          # Rich CLI client
├── test_search.py         # Search functionality tests
└── requirements.txt
```

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file with your Google API key:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Start the Server

```bash
python server.py
```

The server will start at `http://localhost:8000`

### 4. Use the CLI Client

```bash
# Interactive mode (default)
python cli_client.py

# Send a single message
python cli_client.py -m "What's the weather in London?"

# Disable streaming
python cli_client.py --no-stream
```

## API Endpoints

### Chat Endpoints
- `POST /chat` - Send a message to the chatbot
- `POST /chat/stream` - Send a message with streaming response
- `POST /chat/history` - Send conversation with message history

### Visualization Endpoints
- `GET /visualize` - Get basic graph visualization as PNG
- `GET /visualize/enhanced` - Get enhanced visualization with tool information
- `GET /visualize/info` - Get structured graph and tool information

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)

## Available Tools

### Search Tools
- **google_search**: Search the web using Google Search via Gemini
  - Input: Search query string
  - Output: Comprehensive search results summary

### Weather Tools
- **get_weather**: Get current weather for a specific city
  - Input: City name
  - Output: Weather description (mock implementation)

## Agent Implementations

### Basic Chatbot (`agents/chatbot.py`)
Simple conversational agent without tools:
- Uses Gemini 2.5 Flash model
- Basic question-answering capabilities
- No external tool access

### Tool-Enabled Chatbot (`agents/chatbot_with_tools.py`)
Advanced agent with tool capabilities:
- Google Search integration
- Weather information
- Conditional tool execution
- Dynamic tool selection based on user queries

## CLI Client Features

### Rich Terminal Experience
- **Markdown Rendering**: Properly formatted responses
- **Tool Indicators**: Green highlighting of tools being used
- **Streaming Output**: Typewriter effect with thinking animations
- **Spinner Animations**: Visual feedback during processing

### Usage Examples

```bash
# Interactive chat with streaming
python cli_client.py

# Single message mode
python cli_client.py -m "Search for news about AI"

# Test connection
python cli_client.py --test

# Use specific server URL
python cli_client.py --url http://your-server:8000
```

## Adding New Tools

1. Create a new tool file in `tools/` directory:

```python
# tools/new_tool.py
from langchain_core.tools import tool

@tool
def my_new_tool(input_param: str) -> str:
    """
    Description of what this tool does.
    """
    # Your tool implementation
    return "Tool result"
```

2. Add to `tools/__init__.py`:

```python
from .new_tool import my_new_tool

all_tools = [google_search, get_weather, my_new_tool]
```

3. The tool will automatically be available to all agents!

## Creating New Agents

1. Create a new agent file in `agents/` directory
2. Import tools from the tools module:

```python
from tools import all_tools
# or specific tools
from tools.search import google_search
```

3. Follow the LangGraph pattern used in existing agents

## Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Required for Google Search functionality

### Server Configuration
- Default port: 8000
- Host: 0.0.0.0 (configurable in `server.py`)

## Development

### Running Tests
```bash
python test_search.py
```

### API Documentation
Visit `http://localhost:8000/docs` when the server is running for interactive API documentation.

### Graph Visualization
Access enhanced graph visualization at `http://localhost:8000/visualize/enhanced` to see:
- Agent workflow diagram
- Available tools list
- Model configuration
- Dynamic node positioning

## Dependencies

- **LangGraph**: Agent workflow framework
- **LangChain**: LLM integration and tools
- **FastAPI**: Web server framework
- **Rich**: Terminal formatting and UI
- **Pillow**: Image generation for visualizations
- **Google GenAI**: Google's Gemini model integration

## Architecture

### Agent Flow
1. User input received
2. Agent determines if tools are needed
3. If tools required → Execute tools → Return to agent
4. If no tools needed → Generate response → End
5. Response returned with tool usage information

### Tool System
- Modular design allows easy tool addition/removal
- Tools are categorized by functionality
- Automatic tool discovery and binding
- Consistent tool interface across agents

## Contributing

1. Follow the existing project structure
2. Add new tools to the `tools/` module
3. Create new agents in the `agents/` directory
4. Update documentation for new features
5. Test with both CLI client and API endpoints

## License

This project serves as a reference implementation for LangGraph-based chatbots with modular architecture.