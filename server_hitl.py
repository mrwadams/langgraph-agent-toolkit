"""
FastAPI server for testing the HITL prebuilt ReAct agent
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import Response, StreamingResponse
from typing import List, Dict, Optional, Any
import json
import uuid
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from agents.prebuilt_react_hitl import app as hitl_graph


app = FastAPI(title="LangGraph HITL Chatbot API")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    tools_used: List[str] = []
    thread_id: Optional[str] = None
    interrupted: bool = False
    interrupt_data: Optional[Dict[str, Any]] = None

class HumanApprovalRequest(BaseModel):
    action: str  # "approve", "reject", or "edit"
    edited_args: Optional[Dict[str, Any]] = None
    thread_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the HITL LangGraph chatbot
    """
    try:
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the graph with the user message and config
        result = hitl_graph.invoke(
            {"messages": [{"role": "user", "content": request.message}]},
            config=config
        )
        
        # Check if execution was interrupted
        if "__interrupt__" in result:
            interrupt_info = result["__interrupt__"][0]
            return ChatResponse(
                response="Execution paused for human approval",
                tools_used=[],
                thread_id=thread_id,
                interrupted=True,
                interrupt_data=interrupt_info.value
            )
        
        # Extract the assistant's response
        assistant_message = result["messages"][-1].content
        
        # Extract tools used from all messages
        tools_used = []
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', '')
                    if tool_name == 'google_search':
                        tools_used.append('Google Search')
                    elif tool_name == 'get_weather':
                        tools_used.append('Get Weather')
        
        return ChatResponse(
            response=assistant_message, 
            tools_used=list(set(tools_used)),
            thread_id=thread_id,
            interrupted=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/approve", response_model=ChatResponse)
async def approve_tool_call(request: HumanApprovalRequest):
    """
    Approve, reject, or edit a tool call and resume execution
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Prepare resume data based on action
        resume_data = {
            "action": request.action
        }
        if request.action == "edit" and request.edited_args:
            resume_data["edited_args"] = request.edited_args
        
        # Resume execution with human decision
        from langgraph.types import Command
        result = hitl_graph.invoke(Command(resume=resume_data), config=config)
        
        # Check if execution was interrupted again
        if "__interrupt__" in result:
            interrupt_info = result["__interrupt__"][0]
            return ChatResponse(
                response="Execution paused for human approval",
                tools_used=[],
                thread_id=request.thread_id,
                interrupted=True,
                interrupt_data=interrupt_info.value
            )
        
        # Extract the assistant's response
        assistant_message = result["messages"][-1].content
        
        # Extract tools used
        tools_used = []
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', '')
                    if tool_name == 'google_search':
                        tools_used.append('Google Search')
                    elif tool_name == 'get_weather':
                        tools_used.append('Get Weather')
        
        return ChatResponse(
            response=assistant_message,
            tools_used=list(set(tools_used)),
            thread_id=request.thread_id,
            interrupted=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing approval: {str(e)}")

@app.get("/visualize")
async def visualize_graph():
    """
    Visualize the current HITL LangGraph as a PNG image
    """
    try:
        # Generate the mermaid PNG
        png_data = hitl_graph.get_graph().draw_mermaid_png()
        
        # Return the PNG image
        return Response(content=png_data, media_type="image/png")
    except Exception as e:
        # Fallback if visualization fails
        raise HTTPException(status_code=500, detail=f"Error generating graph visualization: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "LangGraph HITL Chatbot API",
        "endpoints": {
            "POST /chat": "Send a message to the chatbot",
            "POST /approve": "Approve, reject, or edit a tool call",
            "GET /visualize": "Get the graph visualization as PNG",
            "GET /docs": "API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)