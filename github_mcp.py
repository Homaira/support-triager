import os
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"
GITHUB_PAT = os.getenv("GITHUB_PAT")


async def list_github_tools():
    """Connect to GitHub's remote MCP server and list what tools it exposes."""
    async with streamablehttp_client(
        url=GITHUB_MCP_URL,
        headers={"Authorization": f"Bearer {GITHUB_PAT}"}
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            return tools.tools


async def create_github_issue(owner: str, repo: str, title: str, body: str):
    """End-to-end test: create a real issue via the MCP server."""
    async with streamablehttp_client(
        url=GITHUB_MCP_URL,
        headers={"Authorization": f"Bearer {GITHUB_PAT}"}
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "issue_write",
                arguments={
                    "method": "create",
                    "owner": owner,
                    "repo": repo,
                    "title": title,
                    "body": body
                }
            )
            return result

if __name__ == "__main__":
    print("--- Listing available GitHub MCP tools ---\n")
    asyncio.run(list_github_tools())

    print("\n--- Creating a test issue ---\n")
    result = asyncio.run(create_github_issue(
        owner="Homaira",
        repo="support-triager",
        title="Test issue from support-triager MCP integration",
        body="Created via the GitHub MCP server."
    ))
    print(result)