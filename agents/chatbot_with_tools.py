from typing import TypedDict, Annotated
from dotenv import load_dotenv

# Import tools from tools module
from tools import all_tools
# Import LLM provider
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()

# --- SETUP LLM AND BIND ALL TOOLS ---

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Bind the consolidated list of tools to the LLM
llm_with_tools = llm.bind_tools(all_tools)


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

app = workflow.compile()