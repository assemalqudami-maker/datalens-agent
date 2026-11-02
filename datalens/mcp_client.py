import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connect(root: Path, scope: str):
    # Deliberately do not inherit provider secrets into the tool process.
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "datalens.mcp_server", "--root", str(root.resolve()), "--scope", scope],
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(Path(__file__).resolve().parent.parent)},
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            yield session


async def call(session, name, args):
    result = await session.call_tool(name, args)
    if result.isError:
        return {"error": " ".join(c.text for c in result.content if c.type == "text")[:2500]}
    if result.structuredContent is not None:
        return result.structuredContent
    text = " ".join(c.text for c in result.content if c.type == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"result": text[:10000]}
