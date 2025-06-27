from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import Response
from typing import List, Dict
import io
import base64

from chatbot import graph

app = FastAPI(title="LangGraph Chatbot API")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    
class MessageHistory(BaseModel):
    messages: List[Dict[str, str]]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the LangGraph chatbot
    """
    try:
        # Invoke the graph with the user message
        result = graph.invoke({"messages": [{"role": "user", "content": request.message}]})
        
        # Extract the assistant's response
        assistant_message = result["messages"][-1].content
        
        return ChatResponse(response=assistant_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/chat/history", response_model=ChatResponse)
async def chat_with_history(request: MessageHistory):
    """
    Chat with the LangGraph chatbot with message history
    """
    try:
        # Invoke the graph with the full message history
        result = graph.invoke({"messages": request.messages})
        
        # Extract the assistant's response
        assistant_message = result["messages"][-1].content
        
        return ChatResponse(response=assistant_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/visualize")
async def visualize_graph():
    """
    Visualize the current LangGraph as a PNG image
    """
    try:
        # Generate the mermaid PNG
        png_data = graph.get_graph().draw_mermaid_png()
        
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
        "message": "LangGraph Chatbot API",
        "endpoints": {
            "POST /chat": "Send a message to the chatbot",
            "POST /chat/history": "Send a conversation with message history",
            "GET /visualize": "Get the graph visualization as PNG",
            "GET /docs": "API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)