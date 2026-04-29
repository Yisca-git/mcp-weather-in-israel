import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any
import json

from groq import Groq
from client import MCPClient
from dotenv import load_dotenv

load_dotenv()


class ChatHost:
    def __init__(self):
        self.mcp_clients: list[MCPClient] = [
            MCPClient("./weather_USA.py"),
            MCPClient("./weather_Israel.py"),
        ]
        self.tool_clients: dict[str, tuple[MCPClient, str]] = {}
        self.clients_connected = False
        self.exit_stack = AsyncExitStack()
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def connect_mcp_clients(self):
        """Connect all configured MCP clients once."""
        if self.clients_connected:
            return

        for client in self.mcp_clients:
            if client.session is None:
                await client.connect_to_server()

        if not self.mcp_clients:
            raise RuntimeError("No MCP clients are connected")

        self.clients_connected = True

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Collect tools from all MCP clients and map them back to their owner."""
        await self.connect_mcp_clients()
        self.tool_clients = {}
        available_tools: list[dict[str, Any]] = []

        for client in self.mcp_clients:
            if client.session is None:
                print(f"Warning: MCP client {client.client_name} is not connected, skipping")
                continue

            try:
                response = await client.session.list_tools()
                for tool in response.tools:
                    exposed_name = f"{client.client_name}__{tool.name}"
                    if exposed_name in self.tool_clients:
                        raise RuntimeError(f"Duplicate tool name detected: {exposed_name}")

                    self.tool_clients[exposed_name] = (client, tool.name)
                    available_tools.append(
                        {
                            "name": exposed_name,
                            "description": f"[{client.client_name}] {tool.description}",
                            "input_schema": tool.inputSchema,
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to get tools from {client.client_name}: {str(e)}")
                continue

        if not available_tools:
            raise RuntimeError("No tools available from any MCP client")

        return available_tools

    async def process_query(self, query: str) -> str:
        """Process a query using Groq and available tools"""
        try:
            available_tools = await self.get_available_tools()
            final_text = []

            groq_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"],
                    },
                }
                for t in available_tools
            ]

            messages = [
                {"role": "system", "content": "You are a helpful weather assistant. When asked about Israeli cities, always use English city names (e.g., 'Tel Aviv', 'Jerusalem', 'Haifa'). The tools will automatically translate them to Hebrew."},
                {"role": "user", "content": query}
            ]

            while True:
                response = self.groq.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    tools=groq_tools,
                    tool_choice="auto",
                )

                message = response.choices[0].message
                messages.append(message)

                if message.content:
                    final_text.append(message.content)

                if not message.tool_calls:
                    break

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    if tool_name not in self.tool_clients:
                        raise RuntimeError(f"Unknown tool requested by model: {tool_name}")

                    client, original_tool_name = self.tool_clients[tool_name]
                    result = await client.session.call_tool(original_tool_name, tool_args)

                    result_text = " ".join(c.text for c in result.content if hasattr(c, "text"))
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    })

            return "\n".join(final_text)
        except Exception as e:
            return f"Error processing query: {str(e)}\n\nPlease try rephrasing your question."

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nchat_loop Error: {str(e)}")
                print("\nTip: Try rephrasing your question or ask again.")

    async def cleanup(self):
        """Clean up resources"""
        for client in reversed(self.mcp_clients):
            await client.cleanup()
        await self.exit_stack.aclose()


async def main():
    host = ChatHost()
    try:
        await host.chat_loop()
    finally:
        await host.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
