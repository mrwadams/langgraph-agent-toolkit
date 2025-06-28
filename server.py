from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import Response, StreamingResponse
from typing import List, Dict, Optional
import json
import io
import uuid
from PIL import Image, ImageDraw, ImageFont

from agents.chatbot_with_memory import app as graph, all_tools

app = FastAPI(title="LangGraph Chatbot API")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    tools_used: List[str] = []
    thread_id: Optional[str] = None
    
class MessageHistory(BaseModel):
    messages: List[Dict[str, str]]
    thread_id: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the LangGraph chatbot
    """
    try:
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the graph with the user message and config
        result = graph.invoke(
            {"messages": [{"role": "user", "content": request.message}]},
            config=config
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
            thread_id=thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat with the LangGraph chatbot with streaming response
    """
    try:
        def generate():
            # Generate thread_id if not provided
            import uuid
            thread_id = request.thread_id or str(uuid.uuid4())
            
            # Create config with thread_id for memory
            config = {"configurable": {"thread_id": thread_id}}
            
            # Send thread_id first
            thread_data = {"type": "thread", "thread_id": thread_id}
            yield f"data: {json.dumps(thread_data)}\n\n"
            
            # Invoke the graph with the user message and config
            result = graph.invoke(
                {"messages": [{"role": "user", "content": request.message}]},
                config=config
            )
            
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
            
            # Send tools info if any tools were used
            if tools_used:
                tools_data = {"type": "tools", "tools": list(set(tools_used))}
                yield f"data: {json.dumps(tools_data)}\n\n"
            
            # Extract the assistant's response and stream it
            assistant_message = result["messages"][-1].content
            
            # Split response into chunks for streaming effect
            words = assistant_message.split()
            chunk_size = 3  # Send 3 words at a time
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                if i + chunk_size < len(words):
                    chunk += " "
                
                chunk_data = {"type": "content", "content": chunk}
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Send end marker
            end_data = {"type": "end"}
            yield f"data: {json.dumps(end_data)}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/chat/history", response_model=ChatResponse)
async def chat_with_history(request: MessageHistory):
    """
    Chat with the LangGraph chatbot with message history
    """
    try:
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the graph with the full message history and config
        result = graph.invoke({"messages": request.messages}, config=config)
        
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
            thread_id=thread_id
        )
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

@app.get("/visualize/enhanced")
async def visualize_enhanced_graph():
    """
    Visualize the LangGraph with additional tool information
    """
    try:
        # Get the graph object to dynamically build visualization
        graph_obj = graph.get_graph()
        
        # Extract nodes dynamically
        graph_nodes = {}
        if hasattr(graph_obj, 'nodes'):
            for node in graph_obj.nodes:
                graph_nodes[str(node)] = node
        elif hasattr(graph_obj, '_nodes'):
            for node in graph_obj._nodes:
                graph_nodes[str(node)] = node
        else:
            # Fallback - try to get from the original mermaid
            try:
                original_mermaid = graph_obj.draw_mermaid()
                # Parse nodes from mermaid (basic extraction)
                import re
                node_pattern = r'(\w+)\["?([^"\]]+)"?\]'
                matches = re.findall(node_pattern, original_mermaid)
                for node_id, label in matches:
                    graph_nodes[node_id] = {"label": label}
            except:
                # Ultimate fallback
                graph_nodes = {"__start__": {}, "agent": {}, "call_tool": {}, "__end__": {}}
        
        # Create a dynamic image representation
        img_width = 800
        # Dynamic height based on number of tools - reduced since we removed "How it works"
        base_height = 350
        tool_height = len(all_tools) * 50
        img_height = max(500, base_height + tool_height)
        
        img = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 14)
            title_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw title
        title = "LangGraph Chatbot with Tools"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((img_width - title_width) // 2, 20), title, fill='black', font=title_font)
        
        # Dynamic node positioning - increased left margin to prevent cutoff
        left_margin = 100
        node_width = 120
        node_height = 40
        
        # Map node types to colors and labels
        node_config = {
            "__start__": ("START", "#e1f5fe", "#01579b"),
            "__end__": ("END", "#e1f5fe", "#01579b"),
            "agent": ("Agent", "#f3e5f5", "#4a148c"),
            "call_tool": ("Tools", "#e8f5e8", "#1b5e20"),
        }
        
        # Calculate vertical positions based on number of nodes
        num_nodes = len(graph_nodes)
        vertical_spacing = min(120, (img_height - 150) // max(num_nodes - 1, 1))
        start_y = 100
        
        # Store node positions for drawing edges
        node_positions = {}
        y_pos = start_y
        
        # Draw nodes dynamically
        for idx, (node_id, node_data) in enumerate(graph_nodes.items()):
            # Get node configuration
            if node_id in node_config:
                label, fill_color, border_color = node_config[node_id]
                display_text = label
            else:
                # Default for unknown nodes
                label = node_id
                fill_color = "#f0f0f0"
                border_color = "#666666"
                display_text = label
            
            x = left_margin + 60
            y = y_pos
            
            # Store position
            node_positions[node_id] = (x, y)
            
            # Draw rounded rectangle
            draw.rounded_rectangle(
                [(x - node_width//2, y - node_height//2), 
                 (x + node_width//2, y + node_height//2)], 
                radius=10, 
                fill=fill_color, 
                outline=border_color,
                width=2
            )
            
            # Draw text
            text_bbox = draw.textbbox((0, 0), display_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            draw.text((x - text_width//2, y - text_height//2), display_text, fill='black', font=font)
            
            y_pos += vertical_spacing
        
        # Draw edges dynamically based on known patterns
        arrow_color = "#666666"
        
        # Common edge patterns
        if "__start__" in node_positions and "agent" in node_positions:
            start_pos = node_positions["__start__"]
            agent_pos = node_positions["agent"]
            # Line from bottom of START to top of Agent
            start_y = start_pos[1] + node_height//2
            end_y = agent_pos[1] - node_height//2
            draw.line([(start_pos[0], start_y), 
                      (agent_pos[0], end_y)], 
                      fill=arrow_color, width=2)
            # Arrow head at the edge of Agent box
            draw.polygon([(agent_pos[0], end_y), 
                         (agent_pos[0] - 5, end_y - 10), 
                         (agent_pos[0] + 5, end_y - 10)], 
                         fill=arrow_color)
        
        if "agent" in node_positions and "call_tool" in node_positions:
            agent_pos = node_positions["agent"]
            tool_pos = node_positions["call_tool"]
            # Line from bottom of Agent to top of Tools
            start_y = agent_pos[1] + node_height//2
            end_y = tool_pos[1] - node_height//2
            draw.line([(agent_pos[0], start_y), 
                      (tool_pos[0], end_y)], 
                      fill=arrow_color, width=2)
            # Arrow head at the edge of Tools box
            draw.polygon([(tool_pos[0], end_y), 
                         (tool_pos[0] - 5, end_y - 10), 
                         (tool_pos[0] + 5, end_y - 10)], 
                         fill=arrow_color)
            draw.text((agent_pos[0] + 10, (agent_pos[1] + tool_pos[1])//2), 
                     "tool calls?", fill=arrow_color, font=small_font)
        
        if "call_tool" in node_positions and "agent" in node_positions:
            tool_pos = node_positions["call_tool"]
            agent_pos = node_positions["agent"]
            # Return edge
            draw.line([(tool_pos[0] + node_width//2, tool_pos[1]), 
                      (tool_pos[0] + node_width//2 + 60, tool_pos[1]),
                      (tool_pos[0] + node_width//2 + 60, agent_pos[1]),
                      (agent_pos[0] + node_width//2, agent_pos[1])], 
                      fill=arrow_color, width=2)
            # Arrow head
            draw.polygon([(agent_pos[0] + node_width//2, agent_pos[1]), 
                         (agent_pos[0] + node_width//2 + 10, agent_pos[1] - 5), 
                         (agent_pos[0] + node_width//2 + 10, agent_pos[1] + 5)], 
                         fill=arrow_color)
        
        if "agent" in node_positions and "__end__" in node_positions:
            agent_pos = node_positions["agent"]
            end_pos = node_positions["__end__"]
            # Side edge for no tools - adjusted to stay within bounds and not overlap
            offset = 30  # Reduced offset to prevent cutoff
            # Stop the line at the edge of the END box, not the center
            end_x = end_pos[0] - node_width//2
            draw.line([(agent_pos[0] - node_width//2, agent_pos[1]), 
                      (agent_pos[0] - node_width//2 - offset, agent_pos[1]),
                      (agent_pos[0] - node_width//2 - offset, end_pos[1]),
                      (end_x, end_pos[1])], 
                      fill=arrow_color, width=2)
            # Arrow head at the edge of the box
            draw.polygon([(end_x, end_pos[1]), 
                         (end_x - 10, end_pos[1] - 5), 
                         (end_x - 10, end_pos[1] + 5)], 
                         fill=arrow_color)
            # Position text to ensure it's visible
            text_x = max(10, agent_pos[0] - node_width//2 - offset - 40)
            draw.text((text_x, (agent_pos[1] + end_pos[1])//2), 
                     "no tools", fill=arrow_color, font=small_font)
            
        # Tools section on the right
        right_start = 350
        y_pos = 100
        
        # List tools dynamically
        draw.text((right_start, y_pos), "Available Tools:", fill='black', font=title_font)
        y_pos += 35
        
        # Draw all tools dynamically
        for tool in all_tools:
            # Draw tool box with better spacing
            tool_box_y = y_pos - 5
            box_height = 50
            draw.rounded_rectangle(
                [(right_start - 10, tool_box_y), 
                 (img_width - 30, tool_box_y + box_height)], 
                radius=8, 
                fill="#e8f5e8", 
                outline="#1b5e20",
                width=2
            )
            
            # Extract clean description from docstring
            desc = tool.description.strip() if tool.description else ""
            # Remove extra whitespace and get first meaningful line
            desc_lines = [line.strip() for line in desc.split('\n') if line.strip()]
            
            # Try to get a clean description
            clean_desc = ""
            for line in desc_lines:
                # Skip lines that are just underscores or dashes
                if not all(c in '-_' for c in line):
                    clean_desc = line
                    break
            
            if not clean_desc:
                clean_desc = "No description available"
            
            # Limit length for display
            if len(clean_desc) > 50:
                clean_desc = clean_desc[:47] + "..."
            
            tool_text = f"{tool.name}"
            draw.text((right_start, y_pos), tool_text, fill='#1b5e20', font=font)
            y_pos += 22
            draw.text((right_start + 20, y_pos), clean_desc, fill='#666666', font=small_font)
            y_pos += 38
        
        # Model info - try to extract from the graph/llm configuration
        y_pos += 30
        draw.text((right_start, y_pos), "Model Configuration:", fill='black', font=title_font)
        y_pos += 30
        
        # Try to get model info dynamically
        model_name = "Gemini 2.5 Flash"  # Default
        try:
            # Try to access the LLM model from the graph
            from agents.chatbot_with_memory import llm
            if hasattr(llm, 'model_name'):
                model_name = llm.model_name
            elif hasattr(llm, 'model'):
                model_name = llm.model
        except:
            pass
        
        model_box_y = y_pos - 5
        draw.rounded_rectangle(
            [(right_start - 10, model_box_y), 
             (img_width - 30, model_box_y + 35)], 
            radius=8, 
            fill="#f3e5f5", 
            outline="#4a148c",
            width=2
        )
        draw.text((right_start, y_pos), model_name, fill='#4a148c', font=font)
        
        # Add some spacing at the bottom
        y_pos += 30
            
        # Convert to PNG bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return Response(content=img_bytes.getvalue(), media_type="image/png")
        
    except Exception as e:
        # If something goes wrong, return a simple text representation
        error_msg = f"Error generating enhanced visualization: {str(e)}\n\n"
        error_msg += "Graph Nodes:\n"
        try:
            graph_obj = graph.get_graph()
            if hasattr(graph_obj, 'nodes'):
                error_msg += f"  {list(graph_obj.nodes)}\n"
        except:
            error_msg += "  Unable to retrieve nodes\n"
        
        error_msg += f"\nAvailable Tools ({len(all_tools)}):\n"
        for tool in all_tools:
            error_msg += f"  - {tool.name}\n"
        
        return Response(content=error_msg, media_type="text/plain")

@app.get("/visualize/info")
async def get_graph_info():
    """
    Get structured information about the graph and tools
    """
    try:
        tool_info = []
        for tool in all_tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description or "No description available",
                "args": tool.args if hasattr(tool, 'args') else {}
            })
        
        return {
            "graph_structure": {
                "nodes": ["agent", "call_tool"],
                "entry_point": "agent",
                "conditional_edges": {
                    "agent": {
                        "condition": "should_continue",
                        "options": {
                            "call_tool": "Tool calls present",
                            "__end__": "No tool calls"
                        }
                    }
                },
                "edges": [
                    {"from": "call_tool", "to": "agent", "description": "Return to agent after tool execution"}
                ]
            },
            "tools": tool_info,
            "model": "gemini-2.5-flash",
            "description": "LangGraph chatbot with Google Search and Weather tools"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting graph info: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "LangGraph Chatbot API",
        "endpoints": {
            "POST /chat": "Send a message to the chatbot",
            "POST /chat/stream": "Send a message to the chatbot with streaming response",
            "POST /chat/history": "Send a conversation with message history",
            "GET /visualize": "Get the graph visualization as PNG",
            "GET /visualize/enhanced": "Get enhanced graph visualization with tool info",
            "GET /visualize/info": "Get structured graph and tool information",
            "GET /docs": "API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)