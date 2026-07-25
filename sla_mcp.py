import os
import sys
import json
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

llm_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

SLA_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_sla_deadline",
        "description": "Compute a support ticket's SLA deadline and whether it's already breached, given its urgency and creation time",
        "parameters": {
            "type": "object",
            "properties": {
                "urgency": {"type": "string", "description": "One of Critical, High, Medium, Low"},
                "created_at": {"type": "string", "description": "ISO 8601 timestamp of when the ticket was created"}
            },
            "required": ["urgency", "created_at"]
        }
    }
}

# Single local consumer, no networking/auth needed — stdio transport is the
# natural fit here (unlike github_mcp.py/slack_mcp.py, which ended up on HTTP
# because that's what those remote/installed servers actually support).
server_params = StdioServerParameters(
    command=sys.executable,
    args=["sla_mcp_server.py"],
)


async def list_sla_tools():
    """Connect to the custom SLA MCP server (spawned as a subprocess over stdio) and list its tools."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            return tools.tools


async def check_deadline(urgency: str, created_at: str):
    """End-to-end test: call the check_sla_deadline tool."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "check_sla_deadline",
                arguments={"urgency": urgency, "created_at": created_at}
            )
            return result


async def ask_claude_to_check_sla(user_message: str):
    """Let Claude decide whether/how to call check_sla_deadline, then execute it via the MCP session."""
    messages = [{"role": "user", "content": user_message}]

    response = llm_client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=messages,
        tools=[SLA_TOOL_SCHEMA],
        max_tokens=500,
    )
    reply = response.choices[0].message

    if not reply.tool_calls:
        print("Claude answered without calling the tool:", reply.content)
        return reply.content

    tool_call = reply.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    print(f"Claude decided to call: {tool_call.function.name}({args})")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_call.function.name, arguments=args)
            tool_output = result.content[0].text
            print(f"MCP tool result: {tool_output}")

    messages.append(reply)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": tool_output
    })

    final = llm_client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=messages,
        tools=[SLA_TOOL_SCHEMA],
        max_tokens=500,
    )
    answer = final.choices[0].message.content
    print(f"\nClaude's final answer: {answer}")
    return answer


if __name__ == "__main__":
    print("--- Listing available SLA MCP tools ---\n")
    asyncio.run(list_sla_tools())

    print("\n--- Breached case: Critical ticket created 2 hours ago ---\n")
    breached_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    result = asyncio.run(check_deadline("Critical", breached_time))
    print(result)

    print("\n--- Not breached case: Low urgency ticket created 1 hour ago ---\n")
    fresh_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    result2 = asyncio.run(check_deadline("Low", fresh_time))
    print(result2)

    print("\n--- Step 11 confirmation: Claude decides to call the tool ---\n")
    two_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    asyncio.run(ask_claude_to_check_sla(
        f"A Critical-urgency ticket was created at {two_hours_ago}. Is it past its SLA deadline?"
    ))
