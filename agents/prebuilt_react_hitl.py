"""
Human-in-the-loop prebuilt ReAct agent implementation using LangGraph's interrupt functionality.
Follows LangGraph's approve/reject pattern for tool call reviews.
"""
from typing import Optional, Literal
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool as create_tool
from langchain_core.tools import BaseTool

# Import base tools from tools module (excluding human_assistance)
from tools.search import google_search
from tools.weather import get_weather
from tools.database import (
    list_database_tables,
    get_database_schema,
    query_database,
    check_database_query
)

load_dotenv()

# --- HUMAN-IN-THE-LOOP TOOL WRAPPER ---

# --- HITL TOOLS CREATED DIRECTLY ---

@create_tool
def google_search_hitl(query: str) -> str:
    """
    Search the web using Google Search (requires human approval).
    Use this tool to find current information, news, or answers to topical questions.
    """
    # Present tool call for human review
    approval_response = interrupt({
        "type": "tool_approval",
        "tool_name": "google_search",
        "tool_args": {"query": query},
        "message": f"Requesting approval to search for: {query}"
    })
    
    # Process human response
    if approval_response.get("action") == "approve":
        # Execute the original tool
        return google_search.invoke({"query": query})
    elif approval_response.get("action") == "reject":
        # Return rejection message
        return "Google search was rejected by human reviewer."
    elif approval_response.get("action") == "edit":
        # Use edited arguments if provided
        edited_args = approval_response.get("edited_args", {"query": query})
        edited_query = edited_args.get("query", query)
        return google_search.invoke({"query": edited_query})
    else:
        # Default to rejection if response is unclear
        return "Google search was not approved."

@create_tool 
def get_weather_hitl(location: str) -> str:
    """
    Get current weather information for a specific location (requires human approval).
    Provide the city, state, and/or country for accurate results.
    """
    # Present tool call for human review
    approval_response = interrupt({
        "type": "tool_approval", 
        "tool_name": "get_weather",
        "tool_args": {"location": location},
        "message": f"Requesting approval to get weather for: {location}"
    })
    
    # Process human response
    if approval_response.get("action") == "approve":
        # Execute the original tool
        return get_weather.invoke({"location": location})
    elif approval_response.get("action") == "reject":
        # Return rejection message
        return "Weather lookup was rejected by human reviewer."
    elif approval_response.get("action") == "edit":
        # Use edited arguments if provided
        edited_args = approval_response.get("edited_args", {"location": location})
        edited_location = edited_args.get("location", location)
        return get_weather.invoke({"location": edited_location})
    else:
        # Default to rejection if response is unclear
        return "Weather lookup was not approved."

@create_tool
def list_database_tables_hitl() -> str:
    """
    List all available tables in the PostgreSQL database (requires human approval).
    Use this tool to discover what tables are available before querying.
    """
    # Present tool call for human review
    approval_response = interrupt({
        "type": "tool_approval",
        "tool_name": "list_database_tables",
        "tool_args": {},
        "message": "Requesting approval to list database tables"
    })
    
    # Process human response
    if approval_response.get("action") == "approve":
        return list_database_tables.invoke({})
    elif approval_response.get("action") == "reject":
        return "Database table listing was rejected by human reviewer."
    else:
        return "Database table listing was not approved."

@create_tool
def get_database_schema_hitl(table_names: str) -> str:
    """
    Get schema information and sample rows for specified database tables (requires human approval).
    
    Args:
        table_names: Comma-separated list of table names to get schema for
    """
    # Present tool call for human review
    approval_response = interrupt({
        "type": "tool_approval",
        "tool_name": "get_database_schema",
        "tool_args": {"table_names": table_names},
        "message": f"Requesting approval to get schema for tables: {table_names}"
    })
    
    # Process human response
    if approval_response.get("action") == "approve":
        return get_database_schema.invoke({"table_names": table_names})
    elif approval_response.get("action") == "reject":
        return "Database schema lookup was rejected by human reviewer."
    elif approval_response.get("action") == "edit":
        edited_args = approval_response.get("edited_args", {"table_names": table_names})
        edited_tables = edited_args.get("table_names", table_names)
        return get_database_schema.invoke({"table_names": edited_tables})
    else:
        return "Database schema lookup was not approved."

@create_tool
def query_database_hitl(query: str) -> str:
    """
    Execute a SELECT query against the PostgreSQL database (requires human approval).
    Only read-only SELECT queries are allowed for security.
    
    Args:
        query: SQL SELECT query to execute
    """
    # Present tool call for human review
    approval_response = interrupt({
        "type": "tool_approval",
        "tool_name": "query_database",
        "tool_args": {"query": query},
        "message": f"Requesting approval to execute database query: {query}"
    })
    
    # Process human response
    if approval_response.get("action") == "approve":
        return query_database.invoke({"query": query})
    elif approval_response.get("action") == "reject":
        return "Database query was rejected by human reviewer."
    elif approval_response.get("action") == "edit":
        edited_args = approval_response.get("edited_args", {"query": query})
        edited_query = edited_args.get("query", query)
        return query_database.invoke({"query": edited_query})
    else:
        return "Database query was not approved."

@create_tool
def check_database_query_hitl(query: str) -> str:
    """
    Validate a SQL query before execution to check for syntax errors and safety (requires human approval).
    Use this tool before executing queries to avoid errors.
    
    Args:
        query: SQL query to validate
    """
    # Present tool call for human review
    approval_response = interrupt({
        "type": "tool_approval",
        "tool_name": "check_database_query",
        "tool_args": {"query": query},
        "message": f"Requesting approval to validate database query: {query}"
    })
    
    # Process human response
    if approval_response.get("action") == "approve":
        return check_database_query.invoke({"query": query})
    elif approval_response.get("action") == "reject":
        return "Database query validation was rejected by human reviewer."
    elif approval_response.get("action") == "edit":
        edited_args = approval_response.get("edited_args", {"query": query})
        edited_query = edited_args.get("query", query)
        return check_database_query.invoke({"query": edited_query})
    else:
        return "Database query validation was not approved."

# List of HITL tools
hitl_tools = [
    google_search_hitl, 
    get_weather_hitl,
    list_database_tables_hitl,
    get_database_schema_hitl,
    query_database_hitl,
    check_database_query_hitl
]

# --- STRUCTURED OUTPUT SCHEMA ---

class AnswerFormat(BaseModel):
    """Structured output format for agent responses"""
    answer: str = Field(description="The main answer to the user's question")
    sources: Optional[list[str]] = Field(description="List of sources used, if applicable")
    confidence: Optional[float] = Field(description="Confidence level between 0 and 1", ge=0, le=1)
    tools_used: Optional[list[str]] = Field(description="List of tools that were used")

# --- CREATE HITL REACT AGENT ---

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Import memory saver for checkpointing
from langgraph.checkpoint.memory import MemorySaver

# Create checkpointer (required for interrupts)
checkpointer = MemorySaver()

# Create the HITL ReAct agent with checkpointer
app = create_react_agent(
    llm,
    tools=hitl_tools,
    checkpointer=checkpointer,
    prompt="""You are a helpful AI assistant with human oversight capabilities. 
    Use the available tools to help answer questions when needed.
    
    Available tools:
    - For weather questions, use get_weather_hitl
    - For web searches, use google_search_hitl  
    - For database operations, use:
      * list_database_tables_hitl to see available tables
      * get_database_schema_hitl to get table schemas
      * query_database_hitl to execute SELECT queries
      * check_database_query_hitl to validate queries
    
    Note that all tool calls require human approval before execution."""
)

# Create structured output version
structured_app = create_react_agent(
    llm,
    tools=hitl_tools,
    checkpointer=checkpointer,
    prompt="""You are a helpful AI assistant with human oversight capabilities.
    Use the available tools to help answer questions when needed.
    Always provide structured responses when possible.
    
    Available tools:
    - For weather questions, use get_weather_hitl
    - For web searches, use google_search_hitl  
    - For database operations, use:
      * list_database_tables_hitl to see available tables
      * get_database_schema_hitl to get table schemas
      * query_database_hitl to execute SELECT queries
      * check_database_query_hitl to validate queries
    
    Include information about which tools were used in your structured response.""",
    response_format=AnswerFormat
)