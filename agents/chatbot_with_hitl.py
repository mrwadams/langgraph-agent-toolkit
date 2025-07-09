from typing import TypedDict, Annotated
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
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

# --- SETUP LLM AND BIND ALL TOOLS AND MEMORY ---

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Bind the consolidated list of tools to the LLM
try:
    llm_with_tools = llm.bind_tools(all_tools)
except NotImplementedError:
    print("Warning: Tool binding not supported for this LLM provider.")
    print("This agent requires tool support. Please use an alternative provider.")
    raise

# Create a memory saver
memory = MemorySaver()


# --- DEFINE LANGGRAPH STATE AND NODES ---

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

# --- BUILD AND COMPILE THE GRAPH ---

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("call_tool", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("call_tool", "agent")

# Compile with checkpointer to support interrupts
app = workflow.compile(checkpointer=memory)