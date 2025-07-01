from typing import TypedDict, Annotated
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Import tools from tools module
from tools import all_tools
# Import LLM factory
from llm_factory import get_llm

load_dotenv()

# --- SETUP LLM AND BIND ALL TOOLS AND MEMORY ---

# Initialize the LLM (will use Gemini unless USE_CUSTOM_LLM=true)
llm = get_llm()

# Bind the consolidated list of tools to the LLM
llm_with_tools = llm.bind_tools(all_tools)

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

app = workflow.compile(checkpointer=memory)