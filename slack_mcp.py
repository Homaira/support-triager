import os
import sys
import asyncio
import subprocess
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_API_TOKEN")
SLACK_MCP_URL = "http://127.0.0.1:8000/mcp"


def start_slack_server() -> subprocess.Popen:
    """Launch the installed slack-mcp-server package (HTTP transport, port 8000)."""
    env = os.environ.copy()
    # get_slack_client() in the installed package only reliably picks up the
    # token via this env var in-process — passing it as an Authorization
    # header didn't reach get_http_headers() in this FastMCP version.
    env["SLACK_MCP_XOXP_TOKEN"] = SLACK_TOKEN
    # conversations_add_message refuses to post unless this is set — a
    # built-in safety gate in the server, not something the client can bypass.
    env["SLACK_MCP_ADD_MESSAGE_TOOL"] = "1"
    return subprocess.Popen([sys.executable, "-m", "slack_mcp_server"], env=env)


async def wait_for_server(url: str, attempts: int = 30, delay: float = 0.5):
    """Retry the MCP handshake until the subprocess's HTTP server is accepting connections."""
    last_error = None
    for _ in range(attempts):
        try:
            async with streamablehttp_client(url=url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return
        except Exception as e:
            last_error = e
            await asyncio.sleep(delay)
    raise RuntimeError(f"slack-mcp-server never came up on {url}: {last_error}")


async def list_slack_tools():
    """Connect to the local Slack MCP server (spawned as a subprocess) and list its tools."""
    async with streamablehttp_client(url=SLACK_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            return tools.tools


async def send_test_message(channel_id: str, text: str):
    """End-to-end test: post a real message to a Slack channel via the MCP server."""
    async with streamablehttp_client(url=SLACK_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "conversations_add_message",
                arguments={"channel_id": channel_id, "payload": text}
            )
            return result


if __name__ == "__main__":
    server_process = start_slack_server()
    try:
        asyncio.run(wait_for_server(SLACK_MCP_URL))

        print("--- Listing available Slack MCP tools ---\n")
        asyncio.run(list_slack_tools())

        print("\n--- Sending a test message ---\n")
        result = asyncio.run(send_test_message(
            channel_id="C0BKP7V0EGM",
            text="Test message from support-triager MCP integration (Step 10)."
        ))
        print(result)
    finally:
        server_process.terminate()
        server_process.wait(timeout=5)
