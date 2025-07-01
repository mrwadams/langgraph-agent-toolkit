from typing import Optional
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path to import llm_providers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import LLM provider
from llm_factory import get_llm

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

# Initialize the LLM using the provider system
llm = get_llm()  # Uses environment variable or defaults to Gemini

# Create the basic ReAct agent with tools
try:
    app = create_react_agent(
        llm,
        tools=all_tools,
        prompt="""You are a helpful AI assistant. Use the available tools to help answer questions.
        When appropriate, structure your response using the provided format."""
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
        prompt="""You are a helpful AI assistant. Use the available tools to help answer questions.
        Always try to provide structured responses when possible.""",
        response_format=AnswerFormat  # This enables structured output
    )
except NotImplementedError:
    print("Warning: Tool binding not supported for this LLM provider.")
    print("This agent requires tool support. Please use Gemini provider.")
    raise