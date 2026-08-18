---
generated: 2026-08-18 10:46
nodes: 9
edges: 12
---

# Requirement Map

## System Map

_Capabilities grouped by area; thick border = bus; arrows = `depends_on`. Edges into the bus/hubs are hidden (the Dependency Map shows area-level coupling)._

```mermaid
graph LR
  subgraph sg_PIPE["PIPE"]
    PIPE_ATTRITION_003["Retention-risk scoring - IsolationForest anomaly score per employee<br><small>PIPE-ATTRITION-003</small>"]
    PIPE_CALENDAR_007["Calendar sync - fourteen-day window of HR-relevant events<br><small>PIPE-CALENDAR-007</small>"]
    PIPE_CLUSTER_004["Team-health clustering - three buckets with a recommended next action<br><small>PIPE-CLUSTER-004</small>"]
    PIPE_COMPLIANCE_005["Certification compliance and overtime exposure<br><small>PIPE-COMPLIANCE-005</small>"]
    PIPE_EMAIL_INTAKE_006["Email intake - inbox messages parsed into time-off rows<br><small>PIPE-EMAIL-INTAKE-006</small>"]
    PIPE_INGEST_HR_001["HR CSV ingest - normalized employee, team and project tables<br><small>PIPE-INGEST-HR-001</small>"]
    PIPE_ORCHESTRATOR_008["Pipeline orchestrator - one command, every artifact, byte-identical on re-run<br><small>PIPE-ORCHESTRATOR-008</small>"]
    PIPE_TEAM_METRICS_002["Team KPI rollup - per-team and org-wide people metrics<br><small>PIPE-TEAM-METRICS-002</small>"]
  end
  subgraph sg_misc["misc"]
    MCP_SERVER_009["MCP server stub - pipeline artifacts exposed to an LLM client<br><small>MCP-SERVER-009</small>"]
  end
  MCP_SERVER_009 --> PIPE_ORCHESTRATOR_008
  PIPE_ORCHESTRATOR_008 --> PIPE_ATTRITION_003
  PIPE_ORCHESTRATOR_008 --> PIPE_CLUSTER_004
  PIPE_ORCHESTRATOR_008 --> PIPE_COMPLIANCE_005
  PIPE_ORCHESTRATOR_008 --> PIPE_EMAIL_INTAKE_006
  PIPE_ORCHESTRATOR_008 --> PIPE_CALENDAR_007
  style PIPE_INGEST_HR_001 stroke-width:3px
  style PIPE_TEAM_METRICS_002 stroke-width:3px
```

## Requirement-to-Code

_Each requirement → its code; arrow label = role (`implements` / `tested-by`). Red = confirmed but no code linked (a gap); grey = baseline/draft, not linked yet (expected)._

```mermaid
graph LR
  MCP_SERVER_009["MCP server stub - pipeline artifacts exposed to an LLM client<br><small>MCP-SERVER-009</small>"]
  f_scripts_mcp_server_py_18["scripts/mcp_server.py:18"]
  MCP_SERVER_009 -->|implements| f_scripts_mcp_server_py_18
  PIPE_ATTRITION_003["Retention-risk scoring - IsolationForest anomaly score per employee<br><small>PIPE-ATTRITION-003</small>"]
  f_scripts_score_attrition_risk_py_10["scripts/score_attrition_risk.py:10"]
  PIPE_ATTRITION_003 -->|implements| f_scripts_score_attrition_risk_py_10
  PIPE_CALENDAR_007["Calendar sync - fourteen-day window of HR-relevant events<br><small>PIPE-CALENDAR-007</small>"]
  f_scripts_sync_calendar_py_17["scripts/sync_calendar.py:17"]
  PIPE_CALENDAR_007 -->|implements| f_scripts_sync_calendar_py_17
  PIPE_CLUSTER_004["Team-health clustering - three buckets with a recommended next action<br><small>PIPE-CLUSTER-004</small>"]
  f_scripts_cluster_team_health_py_7["scripts/cluster_team_health.py:7"]
  PIPE_CLUSTER_004 -->|implements| f_scripts_cluster_team_health_py_7
  PIPE_COMPLIANCE_005["Certification compliance and overtime exposure<br><small>PIPE-COMPLIANCE-005</small>"]
  f_scripts_check_compliance_py_16["scripts/check_compliance.py:16"]
  PIPE_COMPLIANCE_005 -->|implements| f_scripts_check_compliance_py_16
  PIPE_EMAIL_INTAKE_006["Email intake - inbox messages parsed into time-off rows<br><small>PIPE-EMAIL-INTAKE-006</small>"]
  f_scripts_ingest_emails_py_19["scripts/ingest_emails.py:19"]
  PIPE_EMAIL_INTAKE_006 -->|implements| f_scripts_ingest_emails_py_19
  PIPE_INGEST_HR_001["HR CSV ingest - normalized employee, team and project tables<br><small>PIPE-INGEST-HR-001</small>"]
  f_scripts_ingest_hr_py_7["scripts/ingest_hr.py:7"]
  PIPE_INGEST_HR_001 -->|implements| f_scripts_ingest_hr_py_7
  PIPE_ORCHESTRATOR_008["Pipeline orchestrator - one command, every artifact, byte-identical on re-run<br><small>PIPE-ORCHESTRATOR-008</small>"]
  f_scripts_build_people_analytics_py_18["scripts/build_people_analytics.py:18"]
  PIPE_ORCHESTRATOR_008 -->|implements| f_scripts_build_people_analytics_py_18
  PIPE_TEAM_METRICS_002["Team KPI rollup - per-team and org-wide people metrics<br><small>PIPE-TEAM-METRICS-002</small>"]
  f_scripts_compute_team_metrics_py_2["scripts/compute_team_metrics.py:2"]
  PIPE_TEAM_METRICS_002 -->|implements| f_scripts_compute_team_metrics_py_2
```

## Dependency Map

_Area-level coupling: one box per area (N caps), arrow A->B = some capability in A depends on one in B. The System Map has the per-capability detail._

```mermaid
graph LR
  a_PIPE["PIPE<br><small>8 caps</small>"]
  a_misc["misc<br><small>1 caps</small>"]
  a_misc --> a_PIPE
  style a_PIPE stroke-width:3px
```

## Risk & Unknowns

_Requirements needing attention: red = unimplemented (confirmed, no code); orange = unreviewed (promote after review); yellow = untested (implemented but no tested-by — set `test_exempt` to silence), or unverified-intent (open verify-intent question)._

```mermaid
graph LR
  subgraph sg_PIPE["PIPE"]
    PIPE_ATTRITION_003["Retention-risk scoring - IsolationForest anomaly score per employee<br><small>PIPE-ATTRITION-003</small><br>unreviewed, untested, unverified-intent"]
    PIPE_CALENDAR_007["Calendar sync - fourteen-day window of HR-relevant events<br><small>PIPE-CALENDAR-007</small><br>unreviewed, untested, unverified-intent"]
    PIPE_CLUSTER_004["Team-health clustering - three buckets with a recommended next action<br><small>PIPE-CLUSTER-004</small><br>unreviewed, untested, unverified-intent"]
    PIPE_COMPLIANCE_005["Certification compliance and overtime exposure<br><small>PIPE-COMPLIANCE-005</small><br>unreviewed, untested, unverified-intent"]
    PIPE_EMAIL_INTAKE_006["Email intake - inbox messages parsed into time-off rows<br><small>PIPE-EMAIL-INTAKE-006</small><br>unreviewed, untested, unverified-intent"]
    PIPE_INGEST_HR_001["HR CSV ingest - normalized employee, team and project tables<br><small>PIPE-INGEST-HR-001</small><br>unreviewed, untested, unverified-intent"]
    PIPE_ORCHESTRATOR_008["Pipeline orchestrator - one command, every artifact, byte-identical on re-run<br><small>PIPE-ORCHESTRATOR-008</small><br>unreviewed, untested, unverified-intent"]
    PIPE_TEAM_METRICS_002["Team KPI rollup - per-team and org-wide people metrics<br><small>PIPE-TEAM-METRICS-002</small><br>unreviewed, untested, unverified-intent"]
  end
  subgraph sg_misc["misc"]
    MCP_SERVER_009["MCP server stub - pipeline artifacts exposed to an LLM client<br><small>MCP-SERVER-009</small><br>unreviewed, untested, unverified-intent"]
  end
  style MCP_SERVER_009 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_ATTRITION_003 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_CALENDAR_007 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_CLUSTER_004 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_COMPLIANCE_005 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_EMAIL_INTAKE_006 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_INGEST_HR_001 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_ORCHESTRATOR_008 fill:#fff3cd,stroke:#a66,color:#630
  style PIPE_TEAM_METRICS_002 fill:#fff3cd,stroke:#a66,color:#630
```

### Risk Table

| ID | status | members | dependents | risks | recommendation |
| --- | --- | --- | --- | --- | --- |
| MCP-SERVER-009 | baseline | 1 | 0 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-ATTRITION-003 | baseline | 1 | 1 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-CALENDAR-007 | baseline | 1 | 1 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-CLUSTER-004 | baseline | 1 | 1 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-COMPLIANCE-005 | baseline | 1 | 1 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-EMAIL-INTAKE-006 | baseline | 1 | 1 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-INGEST-HR-001 | baseline | 1 | 4 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-ORCHESTRATOR-008 | baseline | 1 | 1 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
| PIPE-TEAM-METRICS-002 | baseline | 1 | 2 | unreviewed, untested, unverified-intent | Draft/baseline, not yet validated: review the contract, wire its `tested-by` tests, then promote to `confirmed`. Until then it is tracked, not enforced. Implemented but no `tested-by` member: write an acceptance test and tag it `# tested-by: <ID>`, or set `test_exempt: <reason>` in the frontmatter to acknowledge it intentionally and silence this signal. Has open `## WHAT — Verify intent` question(s): run `reqmap.py findings`, resolve each in `requirements/_findings.md`, then fold the answer into the Contract or delete the bullet. |
