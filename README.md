# LangGraph Chatbot Reference Implementation

A comprehensive reference implementation of a LangGraph-based chatbot with FastAPI server, CLI client, modular tool system, and Human-in-the-Loop (HITL) capabilities.

## Features

- **Prebuilt ReAct Agent**: Modern LangGraph prebuilt ReAct agent implementation
- **Human-in-the-Loop (HITL)**: Tool call approval workflows with human oversight
- **Multiple Agent Implementations**: Traditional, memory-enabled, and HITL variants
- **FastAPI Servers**: Standard and HITL-specific API endpoints
- **Rich CLI Clients**: Terminal clients with markdown rendering and approval workflows
- **Modular Tools System**: Reusable tools organized by category
- **Dynamic Visualization**: Enhanced graph visualization showing available tools
- **Streaming Support**: Real-time response streaming with thinking animations
- **Custom LLM Support**: Easy integration with enterprise LLMs as drop-in replacement for Gemini

## LLM Configuration

This project supports both Gemini (default) and Vertex AI Gemini for enterprise deployment.

- **Gemini** (default): Uses Google's Gemini API for development and testing
- **Vertex AI Gemini**: Enterprise-grade deployment using Google Cloud Vertex AI

To use Vertex AI Gemini, simply set `USE_CUSTOM_LLM=true` in your environment.

## Project Structure

```
langgraph-chatbot/
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── chatbot_with_tools.py     # Traditional agent with tools
│   ├── chatbot_with_memory.py    # Agent with conversation memory
│   ├── chatbot_with_hitl.py      # Legacy HITL agent
│   ├── prebuilt_react.py         # Modern prebuilt ReAct agent
│   └── prebuilt_react_hitl.py    # HITL prebuilt ReAct agent
├── tools/                     # Reusable tools module
│   ├── __init__.py
│   ├── README.md
│   ├── search.py                 # Google search tool
│   ├── weather.py                # Weather tool
│   └── database.py               # PostgreSQL database tools
├── custom_llm.py              # Vertex AI Gemini wrapper for enterprise
├── llm_factory.py             # Simple LLM selection factory
├── server.py                  # Main FastAPI server (port 8000)
├── server_hitl.py             # HITL FastAPI server (port 8001)
├── cli_client.py              # Standard CLI client
├── cli_hitl_client.py         # HITL CLI client with approval workflow
├── cli_hitl_test.py           # Automated HITL testing
├── test_search.py             # Search functionality tests
└── requirements.txt
```

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file with your API keys and database configuration:

```bash
# Required for search functionality
GOOGLE_API_KEY=your_google_api_key_here

# Required for database tools (optional if not using database features)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Vertex AI Configuration (optional - only needed for enterprise deployment)
USE_CUSTOM_LLM=false
CUSTOM_LLM_MODEL=gemini-1.5-pro
CUSTOM_LLM_TEMPERATURE=0.7
CUSTOM_LLM_MAX_TOKENS=2048
CUSTOM_LLM_TOP_P=0.95
CUSTOM_LLM_TOP_K=40
```

### 3. Start the Server

**Standard Server (Prebuilt ReAct Agent):**
```bash
python server.py
```
Server runs at `http://localhost:8000`

**HITL Server (Human-in-the-Loop):**
```bash
python server_hitl.py
```
Server runs at `http://localhost:8001`

### 4. Use the CLI Clients

**Standard CLI Client:**
```bash
# Interactive mode (default)
python cli_client.py

# Send a single message
python cli_client.py -m "What's the weather in London?"

# Disable streaming
python cli_client.py --no-stream
```

**HITL CLI Client (Human Approval Workflow):**
```bash
# Interactive mode with approval prompts
python cli_hitl_client.py

# Single message with approval
python cli_hitl_client.py -m "Search for AI news"

# Test HITL functionality
python cli_hitl_test.py
```

## API Endpoints

### Standard Server Endpoints (Port 8000)
- `POST /chat` - Send a message to the prebuilt ReAct agent
- `POST /chat/stream` - Send a message with streaming response
- `POST /chat/history` - Send conversation with message history
- `GET /visualize` - Get basic graph visualization as PNG
- `GET /visualize/enhanced` - Get enhanced visualization with tool information
- `GET /visualize/info` - Get structured graph and tool information
- `GET /docs` - Interactive API documentation (Swagger UI)

### HITL Server Endpoints (Port 8001)
- `POST /chat` - Send a message to the HITL agent (may return interrupt)
- `POST /approve` - Approve, reject, or edit a tool call
- `GET /visualize` - Get HITL graph visualization as PNG
- `GET /docs` - HITL API documentation

## Available Tools

### Search Tools
- **google_search**: Search the web using Google Search via Gemini
  - Input: Search query string
  - Output: Comprehensive search results summary

### Weather Tools
- **get_weather**: Get current weather for a specific city
  - Input: City name
  - Output: Weather description (mock implementation)

### Database Tools
- **list_database_tables**: List all available tables in the PostgreSQL database
  - Input: None
  - Output: Comma-separated list of table names
- **get_database_schema**: Get schema information and sample rows for specified tables
  - Input: Comma-separated list of table names
  - Output: Detailed schema information including column types and sample data
- **query_database**: Execute SELECT queries against the PostgreSQL database
  - Input: SQL SELECT query string
  - Output: Query results (read-only, security validated)
- **check_database_query**: Validate SQL query syntax and safety before execution
  - Input: SQL query string
  - Output: Query validation status and feedback

## Agent Implementations

### Prebuilt ReAct Agent (`agents/prebuilt_react.py`) ⭐
Modern LangGraph prebuilt ReAct agent:
- Uses LangGraph's `create_react_agent()` function
- Automatic tool selection and execution
- Gemini 2.5 Flash model integration
- Structured output variant available
- **Recommended for new projects**

### HITL Prebuilt ReAct Agent (`agents/prebuilt_react_hitl.py`) ⭐
Human-in-the-loop version with approval workflow:
- Built on prebuilt ReAct agent foundation
- Requires human approval for all tool executions
- Supports approve/reject/edit workflows
- Follows LangGraph's official HITL patterns
- Perfect for sensitive or high-stakes applications

### Traditional Agents
- **Tool-Enabled Chatbot** (`chatbot_with_tools.py`): Traditional custom implementation
- **Memory Chatbot** (`chatbot_with_memory.py`): Agent with conversation memory
- **Legacy HITL** (`chatbot_with_hitl.py`): Older HITL implementation

## Human-in-the-Loop (HITL) Workflows

The HITL implementation provides human oversight for AI tool executions, following LangGraph's official patterns.

### HITL Features
- **Tool Call Interception**: All tool calls pause for human review
- **Approval Workflow**: Three response options for each tool call:
  - **Approve**: Execute tool with original arguments
  - **Reject**: Cancel tool execution with explanation
  - **Edit**: Modify tool arguments before execution
- **Rich UI**: Visual approval prompts with clear tool information
- **Persistent State**: Proper interrupt/resume using LangGraph checkpointers
- **Thread Management**: Maintains conversation context across approvals

### HITL Usage Example
```bash
# Start HITL server
python server_hitl.py

# Use HITL client (in another terminal)
python cli_hitl_client.py

# User: "What's the weather in Paris?"
# → Tool approval prompt appears
# → Human approves/rejects/edits
# → Tool executes (if approved)
# → Response delivered
```

### HITL API Workflow
```python
# 1. Send message
POST /chat {"message": "Search for AI news"}

# 2. Response with interrupt
{
  "interrupted": true,
  "interrupt_data": {
    "tool_name": "google_search",
    "tool_args": {"query": "AI news"},
    "message": "Requesting approval to search for: AI news"
  }
}

# 3. Human decision
POST /approve {
  "action": "approve",  # or "reject" or "edit"
  "thread_id": "abc123"
}

# 4. Final response
{
  "response": "Here are the latest AI news...",
  "tools_used": ["Google Search"]
}
```

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
- `DB_HOST`: PostgreSQL database host (default: localhost)
- `DB_PORT`: PostgreSQL database port (default: 5432)
- `DB_NAME`: PostgreSQL database name (required for database tools)
- `DB_USER`: PostgreSQL database user (required for database tools)  
- `DB_PASSWORD`: PostgreSQL database password (required for database tools)

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