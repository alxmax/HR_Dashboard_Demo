---
id: MCP-SERVER-009
status: baseline
layer: feature
owner: auto
depends_on: [PIPE-ORCHESTRATOR-008]
risk: 1  # not wired into the pipeline; failure is invisible to the demo
---

# MCP server stub - pipeline artifacts exposed to an LLM client

> The Model Context Protocol (MCP) is a standard by which an LLM client reads
> resources and calls tools from an external server. This module declares that
> surface and implements the query functions, but starts no server.

## WHAT — Contract (normative)
Every line in this section is binding.

- The module declares how the pipeline artifacts would be exposed over MCP, and implements working read and query functions against them.
- The module is a stub. `main()` prints the resource and tool counts, then returns.
- No pipeline stage imports this module, so nothing in the demo depends on it.
- `RESOURCES` declares six read-only artifacts under `hr://` URIs, each carrying a name, MIME type, description and repo-relative path.
- `TOOLS` declares four callable tools with JSON-Schema input definitions: `hr.who_is_at_risk`, `hr.team_health`, `hr.compliance_gaps` and `hr.upcoming_calendar`.
- `read_resource()` resolves an `hr://` URI to its file and returns the text, and raises `KeyError` for an unknown URI.
- `tool_who_is_at_risk()` returns employees at or above a risk threshold, defaulting to 0.65, optionally filtered by team, sorted by descending risk.
- `tool_team_health()` returns the single record matching a team id, and raises `KeyError` when the team is unknown.
- `tool_compliance_gaps()` returns certifications expiring within a day window, defaulting to 30 days, skipping certifications with no expiry date, sorted by days remaining.
- `tool_upcoming_calendar()` flattens the first N days of the calendar window into a flat event list, optionally filtered by category.
- Every tool reads the JSON artifacts the pipeline wrote and recomputes no metric, so an LLM client sees the same numbers as the dashboard.

## WHAT — Verify intent (open questions for the human)
- `CLAUDE.md` and the README describe this server as exposing six resources and seven tools. The code declares six resources and four tools. Which count is intended, and are three tools missing or is the prose wrong?
- `tool_compliance_gaps()` filters `cert_type` by case-insensitive substring against the human-readable certification label. Should it key off a stable identifier instead, so renaming a label does not change results?
- `tool_compliance_gaps()` also returns already-expired certifications, which have negative day counts. Is that intended for a question phrased as "expiring within N days"?
- No tool checks that its artifact exists, so a missing `data/*.json` surfaces as `FileNotFoundError`. Should the stub degrade more gracefully, given an LLM client is the caller?

## HOW — Acceptance (= tests)
- AC-1: Given `data/ai_attrition.json` exists, when `tool_who_is_at_risk()` runs with a threshold of 0.65, then every returned record scores at least 0.65 and results descend by score.
- AC-2: Given an unknown URI, when `read_resource()` is called, then it raises `KeyError`.
- AC-3: Given an unknown team id, when `tool_team_health()` is called, then it raises `KeyError`.
- AC-4: Given a certification with no expiry date, when `tool_compliance_gaps()` runs, then that certification is absent from the result.
- AC-5: Given `python scripts/mcp_server.py` runs, when it completes, then it exits zero and starts no server.

## WHERE — Current implementation
- `scripts/mcp_server.py`

## Notes & limitations
- The MCP SDK imports and the server wiring are commented out, so `pip install mcp` alone does not activate the server. The commented block is the intended shape, not a tested path.
