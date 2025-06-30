from typing import Optional
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv

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

# Create the basic ReAct agent with tools
# Using LangChain ChatGoogleGenerativeAI for compatibility
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

app = create_react_agent(
    llm,
    tools=all_tools,
    prompt="""You are a helpful AI assistant. Use the available tools to help answer questions.
    When appropriate, structure your response using the provided format."""
)


# --- CREATE STRUCTURED OUTPUT AGENT ---

# Create a ReAct agent with structured output
structured_app = create_react_agent(
    llm,
    tools=all_tools,
    prompt="""You are a helpful AI assistant. Use the available tools to help answer questions.
    Always try to provide structured responses when possible.""",
    response_format=AnswerFormat  # This enables structured output
)