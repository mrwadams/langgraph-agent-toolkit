import os
from datetime import datetime
from typing import TypedDict, Annotated
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Create Google GenAI client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- 1. DEFINE ALL YOUR TOOLS ---

# Custom Google Search Tool using Gemini's native search
@tool
def google_search(query: str) -> str:
    """
    Search the web using Google Search.
    Use this tool to find current information, news, or answers to topical questions.
    """
    try:
        # Create a search-focused prompt
        search_prompt = f"Please search for information about: {query}. Provide a comprehensive summary of the most relevant and current information you find."
        
        # Use Google GenAI client with search tool
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=search_prompt,
            config={'tools': [{'google_search': {}}]}
        )
        
        return response.text
    except Exception as e:
        return f"Search failed: {str(e)}"

# Custom Weather Tool
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

# --- 2. SETUP LLM AND BIND ALL TOOLS ---

# Create a single list of all available tools
all_tools = [google_search, get_weather]

# Initialize the main Gemini model (without search for general conversation)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Bind the consolidated list of tools to the LLM
llm_with_tools = llm.bind_tools(all_tools)


# --- 3. DEFINE LANGGRAPH STATE AND NODES ---

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# The ToolNode is designed to handle a list of tools
tool_node = ToolNode(all_tools)

def call_model(state: AgentState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    if state['messages'][-1].tool_calls:
        return "call_tool"
    else:
        return END

# --- 4. BUILD AND COMPILE THE GRAPH ---

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("call_tool", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("call_tool", "agent")

app = workflow.compile()