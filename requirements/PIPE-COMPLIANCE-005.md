---
id: PIPE-COMPLIANCE-005
status: baseline
layer: feature
owner: auto
depends_on: [PIPE-INGEST-HR-001]
risk: 3  # drives a labor-law compliance claim; a wrong "compliant" is the costly direction
---

# Certification compliance and overtime exposure

> Tracks four certifications that Romanian labor law makes mandatory for most roles,
> and flags sustained overtime. Pure function of the CSV input and `REFERENCE_TODAY`.

## WHAT — Contract (normative)
Every line in this section is binding.

- `build_compliance()` reports certification expiry and overtime exposure for every employee.
- `build_compliance()` tracks four certifications: periodic medical check, occupational safety, first aid and management training.
- `_days_until()` returns whole days from `REFERENCE_TODAY` to the expiry date, or null when the employee has no date for that certification.
- `_cert_status()` returns `not_required` for a missing date, `expired` below zero days, `expiring` from zero through `WARN_DAYS` (60), and `valid` beyond that.
- `overall_cert_status` takes the worst status across the four certifications, where `expired` outranks `expiring` and a `not_required` certification never worsens it.
- `overtime_flag` is true when `hours_worked_ytd` reaches `OVERTIME_THRESHOLD_HOURS` (1800), the point at which sustained overtime becomes a labor-law and burnout risk.
- Records are sorted expired first, then expiring, then valid, and by `emp_id` within each group, so the HR reader meets the urgent rows first.
- `summary` reports the reference date, both thresholds, and counts of expired, expiring, compliant, overtime and missing-first-aid employees.
- `main()` writes `data/compliance.json` with `sort_keys=True`.

## WHAT — Verify intent (open questions for the human)
- `n_missing_first_aid` counts employees whose first-aid status is `not_required`, which means the expiry cell was blank. Does a blank cell mean "certification missing" or "role does not need one"? The two readings give different numbers, and the summary label asserts the first.
- Management training is documented as mandatory for leads and managers only, but the code applies one rule to everyone and infers exemption from a blank date. Should role drive the requirement explicitly?
- The overtime comparison is inclusive, so exactly 1800 hours flags. Is the boundary deliberate?

## HOW — Acceptance (= tests)
- AC-1: Given an employee whose medical check expired one day before `REFERENCE_TODAY`, when `build_compliance()` runs, then that certification is `expired` and `overall_cert_status` is `expired`.
- AC-2: Given an employee whose only dated certification expires in exactly 60 days, when the status is computed, then it is `expiring`.
- AC-3: Given an employee whose only dated certification expires in 61 days, when the status is computed, then it is `valid`.
- AC-4: Given an employee with a blank first-aid expiry, when the status is computed, then it is `not_required` and `overall_cert_status` is unchanged by it.
- AC-5: Given an employee with `hours_worked_ytd` of exactly 1800, when the flag is computed, then `overtime_flag` is true.

## WHERE — Current implementation
- `scripts/check_compliance.py`

## Notes & limitations
- Expiry dates are parsed with `errors="coerce"`, so a malformed date becomes blank and is reported as `not_required` rather than as a data error.
