#!/usr/bin/env python3
"""
HITL CLI client for LangGraph Chatbot with human approval workflows
"""
import requests
import json
import argparse
import sys
import re
import time
from typing import List, Dict, Optional

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.spinner import Spinner
    from rich.live import Live
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

DEFAULT_BASE_URL = "http://localhost:8001"

class HITLChatbotClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.console = Console() if RICH_AVAILABLE else None
        self.thread_id = None
        self.pending_approval = None

    def test_connection(self) -> bool:
        """Test if the HITL API server is running"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def chat(self, message: str) -> tuple[str, list, bool, Optional[dict]]:
        """Send a message and handle potential interrupts"""
        try:
            spinner_text = "Thinking..."
            request_data = {"message": message}
            if self.thread_id:
                request_data["thread_id"] = self.thread_id

            if self.console and RICH_AVAILABLE:
                with Live(Spinner("dots", text=spinner_text), console=self.console, refresh_per_second=10):
                    response = requests.post(
                        f"{self.base_url}/chat",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    data = response.json()
            else:
                print(f"{spinner_text}", end="", flush=True)
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                print("\r" + " " * len(spinner_text) + "\r", end="", flush=True)

            # Update thread_id
            if "thread_id" in data:
                self.thread_id = data["thread_id"]

            return (
                data["response"], 
                data.get("tools_used", []), 
                data.get("interrupted", False),
                data.get("interrupt_data")
            )
        except requests.RequestException as e:
            return f"Error: {e}", [], False, None

    def handle_approval(self, interrupt_data: dict) -> tuple[str, list]:
        """Handle human approval for tool calls"""
        if self.console and RICH_AVAILABLE:
            # Display approval request with Rich styling
            tool_name = interrupt_data.get("tool_name", "unknown")
            tool_args = interrupt_data.get("tool_args", {})
            message = interrupt_data.get("message", "")

            panel_content = f"""
[bold yellow]🔍 Tool Approval Required[/bold yellow]

[bold]Tool:[/bold] {tool_name}
[bold]Arguments:[/bold] {json.dumps(tool_args, indent=2)}

[dim]{message}[/dim]
"""
            self.console.print(Panel(panel_content, title="Human-in-the-Loop", border_style="yellow"))

            # Get user decision
            choices = ["approve", "reject", "edit"]
            action = Prompt.ask(
                "\n[bold]Choose action[/bold]",
                choices=choices,
                default="approve"
            )

            edited_args = None
            if action == "edit":
                self.console.print("\n[bold cyan]Edit tool arguments:[/bold cyan]")
                for key, value in tool_args.items():
                    new_value = Prompt.ask(f"  {key}", default=str(value))
                    if new_value != str(value):
                        if edited_args is None:
                            edited_args = tool_args.copy()
                        edited_args[key] = new_value

        else:
            # Fallback for plain text
            print("\n" + "="*50)
            print("🔍 TOOL APPROVAL REQUIRED")
            print("="*50)
            print(f"Tool: {interrupt_data.get('tool_name', 'unknown')}")
            print(f"Arguments: {json.dumps(interrupt_data.get('tool_args', {}), indent=2)}")
            print(f"\n{interrupt_data.get('message', '')}")
            print("\nOptions: approve, reject, edit")
            
            while True:
                action = input("\nChoose action (approve/reject/edit): ").strip().lower()
                if action in ["approve", "reject", "edit"]:
                    break
                print("Please choose 'approve', 'reject', or 'edit'")

            edited_args = None
            if action == "edit":
                print("\nEdit tool arguments:")
                tool_args = interrupt_data.get("tool_args", {})
                for key, value in tool_args.items():
                    new_value = input(f"  {key} (current: {value}): ").strip()
                    if new_value and new_value != str(value):
                        if edited_args is None:
                            edited_args = tool_args.copy()
                        edited_args[key] = new_value

        # Send approval decision
        try:
            approval_data = {"action": action, "thread_id": self.thread_id}
            if edited_args:
                approval_data["edited_args"] = edited_args

            if self.console and RICH_AVAILABLE:
                with Live(Spinner("dots", text="Processing approval..."), console=self.console):
                    response = requests.post(
                        f"{self.base_url}/approve",
                        json=approval_data,
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    data = response.json()
            else:
                print("Processing approval...", end="", flush=True)
                response = requests.post(
                    f"{self.base_url}/approve",
                    json=approval_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                print("\r" + " " * 20 + "\r", end="", flush=True)

            # Check if there's another interrupt
            if data.get("interrupted"):
                if self.console and RICH_AVAILABLE:
                    self.console.print("\n[yellow]⚠️  Another approval required...[/yellow]")
                else:
                    print("\n⚠️  Another approval required...")
                return self.handle_approval(data["interrupt_data"])

            return data["response"], data.get("tools_used", [])

        except requests.RequestException as e:
            return f"Error processing approval: {e}", []

    def interactive_chat(self):
        """Start an interactive HITL chat session"""
        if self.console and RICH_AVAILABLE:
            self.console.print("🤖 LangGraph HITL Chatbot CLI Client", style="bold blue")
            self.console.print("Type 'exit' or 'quit' to end the session")
            self.console.print("\n[bold]Commands:[/bold]")
            self.console.print("  /new     - Start a new conversation thread")
            self.console.print("  /thread  - Show current thread ID")
            self.console.print("  /help    - Show this help message")
            self.console.print("\n[bold yellow]Note:[/bold yellow] Tool calls require human approval")
            self.console.print("-" * 60)
        else:
            print("🤖 LangGraph HITL Chatbot CLI Client")
            print("Type 'exit' or 'quit' to end the session")
            print("\nCommands:")
            print("  /new     - Start a new conversation thread")
            print("  /thread  - Show current thread ID")
            print("  /help    - Show this help message")
            print("\nNote: Tool calls require human approval")
            print("-" * 60)

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break

                # Handle slash commands
                if user_input.startswith('/'):
                    command = user_input.lower().strip()

                    if command == '/new':
                        self.thread_id = None
                        if self.console and RICH_AVAILABLE:
                            self.console.print("\n🔄 Started new conversation thread", style="bold green")
                            self.console.print("-" * 50)
                        else:
                            print("\n🔄 Started new conversation thread")
                            print("-" * 50)
                        continue

                    elif command == '/thread':
                        if self.thread_id:
                            if self.console and RICH_AVAILABLE:
                                self.console.print(f"\n📍 Current thread ID: {self.thread_id}", style="cyan")
                            else:
                                print(f"\n📍 Current thread ID: {self.thread_id}")
                        else:
                            if self.console and RICH_AVAILABLE:
                                self.console.print("\n❌ No active thread. Send a message to start one.", style="yellow")
                            else:
                                print("\n❌ No active thread. Send a message to start one.")
                        continue

                    elif command == '/help':
                        if self.console and RICH_AVAILABLE:
                            self.console.print("\n[bold]Available commands:[/bold]")
                            self.console.print("  /new     - Start a new conversation thread")
                            self.console.print("  /thread  - Show current thread ID")
                            self.console.print("  /help    - Show this help message")
                            self.console.print("\nType 'exit' or 'quit' to end the session")
                        else:
                            print("\nAvailable commands:")
                            print("  /new     - Start a new conversation thread")
                            print("  /thread  - Show current thread ID")
                            print("  /help    - Show this help message")
                            print("\nType 'exit' or 'quit' to end the session")
                        continue

                    else:
                        if self.console and RICH_AVAILABLE:
                            self.console.print(f"\n❌ Unknown command: {command}", style="red")
                            self.console.print("Type /help for available commands", style="dim")
                        else:
                            print(f"\n❌ Unknown command: {command}")
                            print("Type /help for available commands")
                        continue

                if not user_input:
                    continue

                # Send message and handle response
                response, tools_used, interrupted, interrupt_data = self.chat(user_input)

                if interrupted and interrupt_data:
                    # Handle human approval
                    response, tools_used = self.handle_approval(interrupt_data)

                # Display final response
                if self.console and RICH_AVAILABLE:
                    if tools_used:
                        tool_list = ", ".join(tools_used)
                        self.console.print(f"\n[Tools: {tool_list}]", style="bold green")

                    print("Bot: ", end="")
                    try:
                        markdown = Markdown(response)
                        self.console.print(markdown)
                    except:
                        print(response)
                else:
                    if tools_used:
                        tool_list = ", ".join(tools_used)
                        print(f"\n[Tools: {tool_list}]")
                    print(f"Bot: {response}")

                # Show thread ID after first exchange
                if self.thread_id and self.console and RICH_AVAILABLE:
                    self.console.print(f"\n[dim]Thread ID: {self.thread_id[:8]}...[/dim]", style="dim")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="HITL CLI client for LangGraph Chatbot API")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Base URL of the HITL API server")
    parser.add_argument("--message", "-m", help="Send a single message")
    parser.add_argument("--test", "-t", action="store_true", help="Test API connection")

    args = parser.parse_args()

    client = HITLChatbotClient(args.url)

    # Test connection first
    if not client.test_connection():
        print(f"❌ Cannot connect to HITL API server at {args.url}")
        print("Make sure the HITL server is running with: python3 server_hitl.py")
        sys.exit(1)

    if args.test:
        print(f"✅ HITL API server is running at {args.url}")
        return

    if args.message:
        print(f"You: {args.message}")
        response, tools_used, interrupted, interrupt_data = client.chat(args.message)
        
        if interrupted and interrupt_data:
            response, tools_used = client.handle_approval(interrupt_data)
        
        if tools_used:
            tool_list = ", ".join(tools_used)
            print(f"[Tools: {tool_list}]")
        print(f"Bot: {response}")
    else:
        # Default to interactive mode
        client.interactive_chat()

if __name__ == "__main__":
    main()