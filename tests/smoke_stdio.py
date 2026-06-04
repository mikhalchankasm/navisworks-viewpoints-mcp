"""Ручной smoke-тест: поднять сервер по stdio и вызвать get_config через MCP-клиент."""
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", ".", "navisworks-viewpoints-mcp"],
        env={"NAVISWORKS_MASTER": "X:/nope/master.xml", "PYTHONIOENCODING": "utf-8"},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            res = await session.call_tool("get_config", {})
            print("get_config ->", res.content[0].text[:200])


if __name__ == "__main__":
    asyncio.run(main())
