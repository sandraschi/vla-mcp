"""Dual transport: stdio (agents) and HTTP streamable (fleet)."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

TransportType = Literal["stdio", "http", "sse"]

ENV_TRANSPORT = "MCP_TRANSPORT"
ENV_HOST = "MCP_HOST"
ENV_PORT = "MCP_PORT"
ENV_PATH = "MCP_PATH"


def get_transport_config() -> dict:
    return {
        "transport": os.getenv(ENV_TRANSPORT, "stdio").lower(),
        "host": os.getenv(ENV_HOST, "127.0.0.1"),
        "port": int(os.getenv(ENV_PORT, os.getenv("VLA_API_PORT", "11024"))),
        "path": os.getenv(ENV_PATH, "/mcp"),
    }


def create_argument_parser(server_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{server_name} - FastMCP 3.2")
    parser.add_argument("--stdio", action="store_true", help="Force stdio transport")
    parser.add_argument("--http", action="store_true", help="HTTP streamable transport")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--path", default=None)
    return parser


def _resolve(args: argparse.Namespace) -> dict:
    cfg = get_transport_config()
    transport: TransportType = "stdio"
    if getattr(args, "http", False):
        transport = "http"
    elif getattr(args, "stdio", False):
        transport = "stdio"
    else:
        t = cfg["transport"]
        if t in ("http", "sse", "stdio"):
            transport = t  # type: ignore[assignment]
    return {
        "transport": transport,
        "host": args.host or cfg["host"],
        "port": args.port or cfg["port"],
        "path": args.path or cfg["path"],
    }


async def run_server_async(mcp: FastMCP, server_name: str) -> None:
    parser = create_argument_parser(server_name)
    args = parser.parse_args()
    conf = _resolve(args)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Starting %s transport=%s", server_name, conf["transport"])
    if conf["transport"] == "stdio":
        await mcp.run_stdio_async()
        return
    if conf["transport"] == "http":
        await mcp.run_http_async(host=conf["host"], port=conf["port"], path=conf["path"])
        return
    await mcp.run_sse_async(host=conf["host"], port=conf["port"])


def run_server(mcp: FastMCP, server_name: str) -> None:
    asyncio.run(run_server_async(mcp, server_name))
