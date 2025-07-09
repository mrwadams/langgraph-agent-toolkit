from typing import Optional
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path to import llm_providers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import LLM provider
from langchain_google_genai import ChatGoogleGenerativeAI

# Import tools from tools module
from tools import all_tools

load_dotenv()

# --- DEFINE STRUCTURED OUTPUT SCHEMA ---

class AnswerFormat(BaseModel):
    """Structured output format for agent responses"""
    answer: str = Field(description="The main answer to the user's question")
    sources: Optional[list[str]] = Field(description="List of sources used, if applicable")
    confidence: Optional[float] = Field(description="Confidence level between 0 and 1", ge=0, le=1)


# --- CREATE PREBUILT REACT AGENT ---

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Create the basic ReAct agent with tools
try:
    app = create_react_agent(
        llm,
        tools=all_tools,
        prompt="""You are a helpful AI assistant. You can answer many questions directly using your knowledge.

Only use the available tools when:
- You need current/real-time information (like weather, current events, stock prices)
- You need to search the web for specific information you don't know
- You need to query a database for specific data
- The user explicitly asks you to use a tool or search for something

For general knowledge questions, explanations, creative writing, coding help, and other topics you can answer from your training, respond directly without using tools.

Available tools:
- google_search: Use only when you need to search the web for current information
- get_weather: Use only when asked about current weather conditions
- database tools: Use only when asked to query specific database information"""
    )
except NotImplementedError:
    print("Warning: Tool binding not supported for this LLM provider.")
    print("This agent requires tool support. Please use Gemini provider.")
    raise


# --- CREATE STRUCTURED OUTPUT AGENT ---

# Create a ReAct agent with structured output
try:
    structured_app = create_react_agent(
        llm,
        tools=all_tools,
        prompt="""You are a helpful AI assistant. You can answer many questions directly using your knowledge.

Only use the available tools when you need current information or data that you cannot provide from your training.
Always try to provide structured responses when possible.

For general knowledge questions, respond directly without using tools.""",
        response_format=AnswerFormat  # This enables structured output
    )
except NotImplementedError:
    print("Warning: Tool binding not supported for this LLM provider.")
    print("This agent requires tool support. Please use Gemini provider.")
    raise