"""Model Context Protocol (MCP) server stub — exposes dashboard data to LLMs.

This file is a documentation stub demonstrating how the People Analytics
dashboard data layer would surface as MCP resources, so a connected
LLM client (Claude Desktop, an in-house assistant, an agent runtime,
etc.) can query the JSON artifacts directly with the right schema —
without re-implementing the data pipeline.

It is NOT wired into the demo pipeline. Run it manually:

    pip install mcp
    python scripts/mcp_server.py

then point an MCP client at the resulting stdio server.

Reference: https://modelcontextprotocol.io
"""
from __future__ import annotations

import json
from pathlib import Path

# from mcp.server import Server                      # uncomment when mcp is installed
# from mcp.server.stdio import stdio_server          #
# from mcp.types import Resource, TextContent, Tool  #

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


# ───────────────────────────────────────────────────────────────────────
# Resources — what the LLM can read
# ───────────────────────────────────────────────────────────────────────

RESOURCES = [
    {
        "uri": "hr://employees",
        "name": "Employee directory",
        "mime_type": "application/json",
        "description": "50 employees with role, team, tenure, comp ratio, performance score.",
        "path": "data/employees.json",
    },
    {
        "uri": "hr://attrition",
        "name": "Retention-risk scores",
        "mime_type": "application/json",
        "description": "IsolationForest anomaly score [0..1] per employee, with top contributing features.",
        "path": "data/ai_attrition.json",
    },
    {
        "uri": "hr://teams",
        "name": "Team roster + health cluster",
        "mime_type": "application/json",
        "description": "Per-team metrics + KMeans cluster assignment (thriving / steady / at_risk).",
        "path": "data/ai_recommendations.json",
    },
    {
        "uri": "hr://compliance",
        "name": "Certification compliance",
        "mime_type": "application/json",
        "description": "Cert expiry + labor-law overtime flag per employee.",
        "path": "data/compliance.json",
    },
    {
        "uri": "hr://calendar",
        "name": "Outlook calendar window",
        "mime_type": "application/json",
        "description": "14-day window of HR-relevant calendar events synced from Microsoft Graph.",
        "path": "data/calendar.json",
    },
    {
        "uri": "hr://inbox",
        "name": "Email-intake CSV",
        "mime_type": "text/csv",
        "description": "Parsed leave requests appended from the email inbox automation.",
        "path": "data/time_off.csv",
    },
]


# ───────────────────────────────────────────────────────────────────────
# Tools — what the LLM can invoke
# ───────────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "hr.who_is_at_risk",
        "description": (
            "Return employees with retention-risk above a threshold. "
            "Use when the user asks about flight risk, attrition, or "
            "who to schedule a 1:1 with."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold": {"type": "number", "default": 0.65, "minimum": 0, "maximum": 1},
                "team_id": {"type": "string", "description": "Optional team filter (e.g. T01)."},
            },
        },
    },
    {
        "name": "hr.team_health",
        "description": "Return team-level health cluster + recommended actions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string"},
            },
            "required": ["team_id"],
        },
    },
    {
        "name": "hr.compliance_gaps",
        "description": (
            "Return employees whose certifications are expired or expiring "
            "within N days. Use for any 'who needs renewal' question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "within_days": {"type": "integer", "default": 30},
                "cert_type": {
                    "type": "string",
                    "enum": ["medical", "safety", "first_aid", "management", "any"],
                    "default": "any",
                },
            },
        },
    },
    {
        "name": "hr.upcoming_calendar",
        "description": "Return calendar events in the next N days, optionally filtered by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 14, "maximum": 30},
                "category": {
                    "type": "string",
                    "enum": ["all_hands", "training", "review", "leave", "onboarding", "interview"],
                },
            },
        },
    },
]


# ───────────────────────────────────────────────────────────────────────
# Resource + tool implementations
# ───────────────────────────────────────────────────────────────────────

def read_resource(uri: str) -> str:
    """Resolve an `hr://...` URI to the on-disk artifact."""
    for r in RESOURCES:
        if r["uri"] == uri:
            return (ROOT / r["path"]).read_text(encoding="utf-8")
    raise KeyError(f"Unknown resource URI: {uri}")


def tool_who_is_at_risk(*, threshold: float = 0.65, team_id: str | None = None) -> list[dict]:
    data = json.loads(read_resource("hr://attrition"))
    rows = [r for r in data["records"] if r["risk_score"] >= threshold]
    if team_id:
        rows = [r for r in rows if r["team_id"] == team_id]
    return sorted(rows, key=lambda r: -r["risk_score"])


def tool_team_health(*, team_id: str) -> dict:
    data = json.loads(read_resource("hr://teams"))
    for r in data["records"]:
        if r["team_id"] == team_id:
            return r
    raise KeyError(f"Unknown team_id: {team_id}")


def tool_compliance_gaps(*, within_days: int = 30, cert_type: str = "any") -> list[dict]:
    data = json.loads(read_resource("hr://compliance"))
    out: list[dict] = []
    for r in data["records"]:
        for c in r["certifications"]:
            d = c.get("days_until_expiry")
            if d is None:
                continue
            if d > within_days:
                continue
            if cert_type != "any" and cert_type.lower() not in c["kind"].lower():
                continue
            out.append({"emp_id": r["emp_id"], "name": r["full_name"], **c})
    return sorted(out, key=lambda r: r["days_until_expiry"])


def tool_upcoming_calendar(*, days: int = 14, category: str | None = None) -> list[dict]:
    data = json.loads(read_resource("hr://calendar"))
    out: list[dict] = []
    for day in data["days"][:days]:
        for ev in day["events"]:
            if category and ev["category"] != category:
                continue
            out.append({"date": day["iso_date"], **ev})
    return out


# ───────────────────────────────────────────────────────────────────────
# Server entry point (sketch)
# ───────────────────────────────────────────────────────────────────────

def main() -> None:
    """Sketch of the stdio MCP server. Uncomment + adapt when wiring real MCP.

    The shape below matches the official MCP Python SDK pattern.
    """
    print("[mcp_server] Documentation stub — not wired into the demo pipeline.")
    print(f"[mcp_server] Resources exposed: {len(RESOURCES)}")
    print(f"[mcp_server] Tools exposed:     {len(TOOLS)}")
    print("[mcp_server] To enable: pip install mcp, then uncomment the SDK imports + wire to stdio_server().")

    # Reference flow once the SDK is wired:
    #
    # server = Server("hr-dashboard")
    #
    # @server.list_resources()
    # async def list_resources() -> list[Resource]:
    #     return [Resource(**r) for r in RESOURCES]
    #
    # @server.read_resource()
    # async def read(uri: str) -> str:
    #     return read_resource(uri)
    #
    # @server.list_tools()
    # async def list_tools() -> list[Tool]:
    #     return [Tool(**t) for t in TOOLS]
    #
    # @server.call_tool()
    # async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    #     dispatch = {
    #         "hr.who_is_at_risk":    tool_who_is_at_risk,
    #         "hr.team_health":       tool_team_health,
    #         "hr.compliance_gaps":   tool_compliance_gaps,
    #         "hr.upcoming_calendar": tool_upcoming_calendar,
    #     }
    #     result = dispatch[name](**arguments)
    #     return [TextContent(type="text", text=json.dumps(result, indent=2))]
    #
    # async with stdio_server() as (read_stream, write_stream):
    #     await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
