import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any

from google import genai
from google.genai import types
from client import MCPClient
from dotenv import load_dotenv

load_dotenv()


class ChatHost:
    def __init__(self):
        self.mcp_clients: list[MCPClient] = [
            MCPClient("./weather_USA.py"),
            MCPClient("./weather_Israel.py"),  # Israeli MCP with Playwright
        ]
        self.tool_clients: dict[str, tuple[MCPClient, str]] = {}
        self.clients_connected = False
        self.exit_stack = AsyncExitStack()
        self.gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
        """Process a query using Gemini and available tools"""
        available_tools = await self.get_available_tools()
        final_text = []

        # Convert MCP tool schemas to Gemini function declarations
        gemini_tools = [
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["input_schema"] if t["input_schema"].get("properties") else None,
                )
                for t in available_tools
            ])
        ]

        contents = [types.Content(role="user", parts=[types.Part(text=query)])]

        while True:
            response = self.gemini.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(tools=gemini_tools),
            )

            candidate = response.candidates[0].content
            contents.append(candidate)

            saw_tool_use = False
            tool_results = []

            for part in candidate.parts:
                if part.text:
                    final_text.append(part.text)

                if not part.function_call:
                    continue

                saw_tool_use = True
                tool_name = part.function_call.name
                tool_args = dict(part.function_call.args)

                if tool_name not in self.tool_clients:
                    raise RuntimeError(f"Unknown tool requested by model: {tool_name}")

                client, original_tool_name = self.tool_clients[tool_name]
                result = await client.session.call_tool(original_tool_name, tool_args)

                # Extract text from MCP result content
                result_text = " ".join(c.text for c in result.content if hasattr(c, "text"))
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                tool_results.append(types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result_text},
                ))

            if not saw_tool_use:
                break

            contents.append(types.Content(role="user", parts=tool_results))

        return "\n".join(final_text)

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
