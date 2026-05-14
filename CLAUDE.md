# CLAUDE.md

Context for Claude (or any AI coding assistant) working on this repo.

## What this project is

A self-contained HR analytics dashboard backed by a small Python pipeline (pandas + scikit-learn). It demonstrates a reproducible data flow from CSV inputs through ML scoring and email-automation, ending in a single static HTML that opens via double-click.

Two audiences are explicitly designed for:

1. **A non-technical HR practitioner** who opens `dashboard_demo.html` to read the report
2. **A developer** reading the source to understand the pipeline structure

When in doubt, HR operability wins on the dashboard surface; engineering clarity wins on the source-code surface.

## How to run

```
python scripts/build_people_analytics.py   # rebuilds data/*.json and data/time_off.csv
```

Then double-click `dashboard_demo.html`. No server, no bundler, no build step beyond the Python pipeline.

On Windows: `run_people_pipeline.bat` wraps both steps.

## Architecture quick map

```
sample_data/*.csv  →  scripts/*.py  →  data/*.json + data/time_off.csv  →  dashboard_demo.html
                                                                          (data inlined as JS constants)
                                       scripts/mcp_server.py             →  MCP server stub
                                                                             (exposes 6 resources + 7 tools)
```

- **`dashboard_demo.html`** is intentionally **self-contained**. All data is hard-coded into the JS constants at the top of the `<script>` block. The Python pipeline maintains the CSVs and JSON artifacts in `data/`, but the dashboard does *not* fetch them at runtime. This is the "double-click works" requirement.
- **`arhitectura.html`** is a bilingual (RO/EN) explainer page showing the full automated workflow — pipeline diagram, automation stages, MCP layer, and output nodes. It is a standalone file; it does not share JS or CSS with the dashboard.
- The Python pipeline is still real and runs end-to-end. It exists for the engineering signal and so the demo can be updated by editing CSVs and re-running the orchestrator (which currently regenerates the JSON artifacts — wiring those back into the HTML is a future step).

## Conventions

- **No frameworks.** Vanilla HTML/CSS/JS. Adding React/Vue/anything with a build step defeats the "double-click works" property.
- **No ES modules in `dashboard_demo.html`.** Chrome blocks ES-module loading under `file://`. Everything is one classic `<script>` block at the bottom of `<body>`.
- **No `fetch()` for local files in the dashboard.** Same reason as above.
- **No external JS dependencies.** Google Fonts are the only external resource, with mono-font fallbacks.

### Internationalization

`window.LANG` ∈ `{en, ro}`, persisted to `localStorage`. Default is `en`. The toggle button is in the top-right corner.

Translations live in a single `I18N` object at the top of the `<script>` block.

⚠️ **`data-i18n` attribute must NEVER be applied to an element with id'd children.** `applyI18n()` sets `textContent` on every `[data-i18n]` element, which destroys all child nodes. If you have `<div data-i18n="key"><span id="counter">...</span></div>`, the span is wiped, and any later `getElementById("counter")` returns null → crash.

The fix is always to wrap only the translatable text in its own `<span data-i18n="...">`, leaving sibling spans untouched:

```html
<!-- WRONG: applyI18n will delete the meta span -->
<div class="section-head" data-i18n="sec.people">People <span id="counter">·  50</span></div>

<!-- CORRECT -->
<div class="section-head"><span data-i18n="sec.people">People</span> <span id="counter">·  50</span></div>
```

### Theme

`data-theme` on `<html>` ∈ `{light, dark}`, persisted to `localStorage`. Default is `light`. Theme drives a single set of CSS custom properties (`--bg-0`, `--ink-1`, `--gold`, etc.) — components reference the variables, not concrete colors.

### Determinism

- Every sklearn estimator must set `random_state=42` explicitly.
- Every `json.dump` must use `sort_keys=True`.
- `ingest_emails.py` keys ingest rows by a sha1 of the message-id so re-runs never duplicate.

Acceptance test: `python scripts/build_people_analytics.py` twice from a clean state → `diff -r data/ <previous>` must exit 0.

### Windows quirks

- **`.bat` files MUST be written with CRLF line endings.** LF-only confuses `cmd.exe` parser → silent SET failures, garbled output. When writing or editing `run_people_pipeline.bat`, use PowerShell:
  ```powershell
  [System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::ASCII)
  ```
  with `$content` joined by `"`r`n"`. The harness `Write` tool emits LF-only by default.
- Avoid `—` (em dash) and `→` (arrow) in `.bat` echo strings, even with `chcp 65001`. Stick to ASCII (`-`, `->`).

## Common tasks

### Add a new term to the Legend tab

1. Add EN + RO translations in `I18N.en` and `I18N.ro` with keys `lg.t.<id>`, `lg.d.<id>`, `lg.w.<id>` (term / definition / where it appears).
2. Add `<id>` to the appropriate topic group in `renderLegend()`.

### Add a new drill-down

The drawer is a global `openDrawer(title, sub, html)` helper. Build the HTML body using the existing `dw-section`, `dw-item`, `dw-kv` classes. Wire click handlers in the relevant render function.

### Change KPI data

Edit `sample_data/*.csv`, then run `python scripts/build_people_analytics.py`. **Note:** the dashboard's hard-coded JS constants are *not* currently auto-regenerated from the CSVs — this is a future bundler step. For now, change both the CSV (for the Python pipeline) and the inline JS constants (for the dashboard) when updating data.

### Add a translation key

In the `I18N` object: add the key to both `en` and `ro` blocks. Then either:
- Add `data-i18n="<key>"` to a static HTML element (only on a leaf element with no id'd children — see warning above), or
- Call `t("<key>")` from a JS render function.

## What NOT to do

- ❌ Don't add `<script type="module">` or `import` statements — breaks `file://`.
- ❌ Don't add `fetch()` for `./data/*.json` — breaks `file://`.
- ❌ Don't put `data-i18n` on a parent that has id'd children.
- ❌ Don't write `.bat` with LF endings or non-ASCII characters in echo statements.
- ❌ Don't introduce ML models that need API keys at runtime. sklearn-only, deterministic.
- ❌ Don't expose proprietary data from sibling projects. Sample data is HR-themed mock; do not introduce real employee data.
- ❌ Don't add tooling that requires a build step (webpack, Vite, Tailwind, etc.). The "double-click works" property is load-bearing.

## Useful patterns

### File map ↔ tab map (dashboard_demo.html)

| Tab id | DOM section id | Render function | Mocked data const |
|---|---|---|---|
| `overview` | `view-overview` | `renderKpiRow`, `renderGauge`, `renderRiskDist`, `renderBenchDist`, `renderTeamBars`, `renderEmpTable` | `EMPLOYEES`, `TEAMS`, `TOPLINE`, `AI_ATTRITION`, `BENCH_BY_EMP` |
| `employees` | `view-employees` | `renderEmpTable(..., full=true)` | `EMPLOYEES` |
| `teams` | `view-teams` | `renderTeamGrid`, `renderTeamBars` | `TEAMS` |
| `inbox` | `view-inbox` | `renderInbox` | `INTAKE`, `MISSING_LOGS` |
| `legend` | `view-legend` | `renderLegend` | derived from `I18N` |

### Sidebar (always visible)

Renders `Snapshot` (top-line stats), a full-month **Outlook calendar** widget, and `Suggestions` (3 AI-insight cards). All hard-coded; not part of any render function.

The calendar widget is driven by three JS constants:
- `CALENDAR_DAYS` — 14-day window with `iso_date`, `intensity`, `primary_category`
- `CALENDAR_EVENTS_BY_DAY` — per-date event list (title, category, organizer, attendees)
- `MEETINGS_BY_EMP` — per-employee meeting list `{when, title, organizer}`
- `MEETINGS_BY_DATE` — **derived at runtime** from `MEETINGS_BY_EMP`; deduplicates meetings by `when+title` key so the same meeting doesn't appear multiple times when multiple attendees share it

Calendar color logic: teal (`rgba(13,125,114,α)`) if any event has `category:"training"`, otherwise gold (`rgba(160,111,28,α)`) with alpha driven by total event+meeting count. A numeric badge below the day number shows the total count. `renderCalendar()` must be called from `applyI18n()` so day-of-week headers re-render on language switch.

## Pipeline + dashboard handshake

The Python pipeline writes the canonical `data/*.json` + `data/time_off.csv` artifacts (deterministic, idempotent). The dashboard ships with a snapshot of the same shape inlined as JS constants, so it works offline / under `file://`. A bundling step that synchronises the two on every build is a small future addition; preserve the "double-click works" property by inlining everything, not by switching to `fetch()`.

## Implementation notes worth re-reading

A few non-obvious gotchas surfaced while building this. Documented so future changes don't reintroduce them:

- **`.bat` files require CRLF line endings.** LF-only confuses `cmd.exe`'s parser and the `set` commands silently fail. When generating or editing `run_people_pipeline.bat`, write via PowerShell with explicit `"`r`n"` joins.
- **`data-i18n` on a parent element wipes id'd children.** `applyI18n()` sets `textContent` on every `[data-i18n]` node, which destroys child elements. Always put `data-i18n` on a leaf `<span>`, not on the parent that also hosts an id'd counter.
- **The dashboard is intentionally single-file.** No ES modules, no `fetch()` of local JSON, no build step. The "double-click works" property is load-bearing for the demo's use case.
- **Determinism is acceptance-tested.** Run `python scripts/build_people_analytics.py` twice from a clean state and `diff -r data/ <previous>` must exit 0.
