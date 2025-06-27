#!/usr/bin/env python3
"""
Lightweight CLI client for testing LangGraph Chatbot API endpoints
"""
import requests
import json
import argparse
import sys
import re
import time
from typing import List, Dict

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.spinner import Spinner
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

DEFAULT_BASE_URL = "http://localhost:8000"

class ChatbotClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, streaming: bool = True):
        self.base_url = base_url.rstrip('/')
        self.console = Console() if RICH_AVAILABLE else None
        self.streaming = streaming
    
    def test_connection(self) -> bool:
        """Test if the API server is running"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def chat(self, message: str) -> tuple[str, list]:
        """Send a single message to the chatbot"""
        if self.streaming:
            return self.chat_streaming(message)
        else:
            try:
                # Show thinking spinner for non-streaming too
                spinner_text = "Thinking..."
                if self.console and RICH_AVAILABLE:
                    with Live(Spinner("dots", text=spinner_text), console=self.console, refresh_per_second=10):
                        response = requests.post(
                            f"{self.base_url}/chat",
                            json={"message": message},
                            headers={"Content-Type": "application/json"}
                        )
                        response.raise_for_status()
                        data = response.json()
                else:
                    print(f"{spinner_text}", end="", flush=True)
                    response = requests.post(
                        f"{self.base_url}/chat",
                        json={"message": message},
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    data = response.json()
                    print("\r" + " " * len(spinner_text) + "\r", end="", flush=True)  # Clear spinner
                
                return data["response"], data.get("tools_used", [])
            except requests.RequestException as e:
                return f"Error: {e}", []
    
    def chat_streaming(self, message: str) -> tuple[str, list]:
        """Send a message and handle streaming response"""
        try:
            # Show thinking spinner
            spinner_text = "Thinking..."
            if self.console and RICH_AVAILABLE:
                with Live(Spinner("dots", text=spinner_text), console=self.console, refresh_per_second=10) as live:
                    response = requests.post(
                        f"{self.base_url}/chat/stream",
                        json={"message": message},
                        headers={"Content-Type": "application/json"},
                        stream=True
                    )
                    response.raise_for_status()
                    
                    # Clear the spinner and start processing response
                    live.stop()
            else:
                print(f"{spinner_text}", end="", flush=True)
                response = requests.post(
                    f"{self.base_url}/chat/stream",
                    json={"message": message},
                    headers={"Content-Type": "application/json"},
                    stream=True
                )
                response.raise_for_status()
                print("\r" + " " * len(spinner_text) + "\r", end="", flush=True)  # Clear spinner
            
            tools_used = []
            content_parts = []
            first_content = True
            
            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            
                            if data.get("type") == "tools":
                                tools_used = data.get("tools", [])
                                # Display tool indicator in green if Rich is available
                                if tools_used:
                                    if self.console and RICH_AVAILABLE:
                                        tool_list = ", ".join(tools_used)
                                        self.console.print(f"[Tools: {tool_list}]", style="bold green")
                                        print()  # Add newline
                                    else:
                                        tool_list = ", ".join(tools_used)
                                        print(f"[Tools: {tool_list}]")
                            
                            elif data.get("type") == "content":
                                if first_content:
                                    print("Bot: ", end="", flush=True)
                                    first_content = False
                                
                                chunk = data.get("content", "")
                                content_parts.append(chunk)
                                print(chunk, end="", flush=True)
                                time.sleep(0.05)  # Small delay for streaming effect
                            
                            elif data.get("type") == "end":
                                print()  # Final newline
                                break
                                
                        except json.JSONDecodeError:
                            continue
            
            full_response = "".join(content_parts)
            return full_response, tools_used
            
        except requests.RequestException as e:
            return f"Error: {e}", []
    
    def _display_response(self, formatted_response):
        """Helper method to display formatted responses"""
        if isinstance(formatted_response, tuple) and formatted_response[0] == "rich_with_tools":
            # Special handling for Rich with tools
            _, clean_text, used_tools = formatted_response
            print("Bot: ", end="")
            # Print green tool indicator
            tool_list = ", ".join(used_tools)
            self.console.print(f"[Tools: {tool_list}]", style="bold green")
            print()  # Add newline
            # Print markdown response
            try:
                markdown = Markdown(clean_text)
                self.console.print(markdown)
            except:
                print(clean_text)
        elif self.console and RICH_AVAILABLE and isinstance(formatted_response, Markdown):
            print("Bot: ", end="")
            self.console.print(formatted_response)
        else:
            print(f"Bot: {formatted_response}")
    
    def _format_response(self, response_text: str, tools_used: list = None) -> str:
        """Format the response with tool indicators and markdown"""
        # Clean up debug output
        cleaned_text = re.sub(r'DEBUG: [^\n]*\n', '', response_text).strip()
        
        # Handle tool indicators with Rich styling if available
        if tools_used and self.console and RICH_AVAILABLE:
            # Return a tuple for special handling in display
            return ("rich_with_tools", cleaned_text, tools_used)
        elif tools_used:
            # Fallback for plain text
            tool_list = ", ".join(tools_used)
            tool_indicators = f"[Tools: {tool_list}]\n\n"
            return tool_indicators + cleaned_text
        else:
            # No tools, render as markdown if Rich is available
            if self.console and RICH_AVAILABLE:
                try:
                    markdown = Markdown(cleaned_text)
                    return markdown
                except:
                    return cleaned_text
            else:
                return cleaned_text
    
    def chat_with_history(self, messages: List[Dict[str, str]]) -> tuple[str, list]:
        """Send conversation with message history"""
        try:
            # Show thinking spinner
            spinner_text = "Thinking..."
            if self.console and RICH_AVAILABLE:
                with Live(Spinner("dots", text=spinner_text), console=self.console, refresh_per_second=10):
                    response = requests.post(
                        f"{self.base_url}/chat/history",
                        json={"messages": messages},
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    data = response.json()
            else:
                print(f"{spinner_text}", end="", flush=True)
                response = requests.post(
                    f"{self.base_url}/chat/history",
                    json={"messages": messages},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                print("\r" + " " * len(spinner_text) + "\r", end="", flush=True)  # Clear spinner
            
            return data["response"], data.get("tools_used", [])
        except requests.RequestException as e:
            return f"Error: {e}", []
    
    def interactive_chat(self):
        """Start an interactive chat session"""
        if self.console and RICH_AVAILABLE:
            self.console.print("🤖 LangGraph Chatbot CLI Client", style="bold blue")
            self.console.print("Type 'exit' or 'quit' to end the session")
            self.console.print("-" * 50)
        else:
            print("🤖 LangGraph Chatbot CLI Client")
            print("Type 'exit' or 'quit' to end the session")
            print("-" * 50)
        
        conversation_history = []
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Add user message to history
                conversation_history.append({"role": "user", "content": user_input})
                
                # Get response using history
                if len(conversation_history) == 1:
                    # First message, use simple chat endpoint
                    if self.streaming:
                        response, tools_used = self.chat(user_input)
                        # Streaming already handled the display
                    else:
                        response, tools_used = self.chat(user_input)
                        # Format and display the response
                        formatted_response = self._format_response(response, tools_used)
                        self._display_response(formatted_response)
                else:
                    # Use history endpoint for context (no streaming for history yet)
                    response, tools_used = self.chat_with_history(conversation_history)
                    formatted_response = self._format_response(response, tools_used)
                    self._display_response(formatted_response)
                
                # Add bot response to history (original unformatted response)
                conversation_history.append({"role": "assistant", "content": response})
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLI client for LangGraph Chatbot API")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Base URL of the API server")
    parser.add_argument("--message", "-m", help="Send a single message")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive chat session")
    parser.add_argument("--test", "-t", action="store_true", help="Test API connection")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    
    args = parser.parse_args()
    
    client = ChatbotClient(args.url, streaming=not args.no_stream)
    
    # Test connection first
    if not client.test_connection():
        print(f"❌ Cannot connect to API server at {args.url}")
        print("Make sure the server is running with: python3 server.py")
        sys.exit(1)
    
    if args.test:
        print(f"✅ API server is running at {args.url}")
        return
    
    if args.message:
        print(f"You: {args.message}")
        response, tools_used = client.chat(args.message)
        
        if not client.streaming:
            # Only format and display if not streaming (streaming handles its own display)
            formatted_response = client._format_response(response, tools_used)
            client._display_response(formatted_response)
    elif args.interactive:
        client.interactive_chat()
    else:
        # Default to interactive mode
        client.interactive_chat()

if __name__ == "__main__":
    main()