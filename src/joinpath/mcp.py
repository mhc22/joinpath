"""Minimal stdio MCP server: one tool, plan_sql_subgraph."""

from __future__ import annotations

import json
import sys
from typing import Any

from .plan import plan_question
from .schema import Schema

TOOLS = [
    {
        "name": "plan_sql_subgraph",
        "description": (
            "Given a natural-language data question and a schema, return the tables, "
            "join path, and hinted columns the SQL agent may use. Call this BEFORE writing SQL."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "schema": {"type": "object", "description": "Schema JSON with tables and foreign_keys"},
            },
            "required": ["question", "schema"],
        },
    }
]


def _handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    req_id = message.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "joinpath", "version": "0.1.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") != "plan_sql_subgraph":
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "unknown tool"}}
        args = params.get("arguments") or {}
        schema = Schema.from_dict(args["schema"])
        plan = plan_question(args.get("question") or "", schema)
        text = json.dumps(
            {"plan": plan.to_dict(), "prompt": plan.compact_prompt()},
            ensure_ascii=False,
            indent=2,
        )
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": text}], "isError": not plan.tables},
        }
    if req_id is not None:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"unsupported: {method}"}}
    return None


def serve() -> None:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            continue
        reply = _handle(message)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve()
