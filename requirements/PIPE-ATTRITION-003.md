---
id: PIPE-ATTRITION-003
status: baseline
layer: feature
owner: auto
depends_on: [PIPE-INGEST-HR-001]
risk: 3  # an unsupervised score shown to HR as "retention risk" against a named person
---

# Retention-risk scoring - IsolationForest anomaly score per employee

> IsolationForest is an unsupervised model that flags rows unlike the rest of the
> population. No labelled leavers exist here, so it measures unusualness, which the
> dashboard then presents as retention risk.

## WHAT — Contract (normative)
Every line in this section is binding.

- `build_attrition()` produces one risk record per employee: a score, a label, and the three features that drove it.
- The model reads six features: tenure years, comp ratio, performance score, days since review, promotion count and year-to-date training hours.
- `StandardScaler` standardizes those features before fitting, so a large-unit column cannot dominate the result.
- `IsolationForest` runs with `n_estimators=200`, `contamination=0.2` and `random_state=42`, which keeps repeated runs identical.
- Raw anomaly scores are negated, so a higher number means more anomalous.
- Negated scores are then rescaled to the range 0 to 1, against the minimum and maximum of the current cohort.
- When every employee scores identically, the normalized score is zero for all of them, which avoids a divide-by-zero.
- `risk_label` is `high` from 0.66 up, `medium` from 0.40 to below 0.66, and `low` below 0.40.
- `top_signals` lists the three features with the largest absolute standardized value for that employee, each with its signed z-score rounded to two decimals.
- Records are sorted by `emp_id`, and `summary` carries the per-label counts plus the model name, feature list and seed.
- `main()` writes `data/ai_attrition.json` with `sort_keys=True`.

## WHAT — Verify intent (open questions for the human)
- The score is rescaled within the current cohort, so one employee always scores 1.0 and every score shifts when a colleague joins or leaves. Is a cohort-relative score intended, or should the label thresholds sit on an absolute scale?
- `contamination=0.2` tells the model that a fifth of staff are anomalies. Is that an HR-validated prior or an untuned default?
- `top_signals` ranks by absolute magnitude, so an unusually high value and an unusually low one look identical to the HR reader. Should the direction be spelled out?

## HOW — Acceptance (= tests)
- AC-1: Given the sample cohort, when `build_attrition()` runs in two separate processes, then every employee receives the same `risk_score` in both.
- AC-2: Given an employee scoring exactly 0.66, when the label is assigned, then `risk_label` is `high`.
- AC-3: Given an employee scoring 0.399, when the label is assigned, then `risk_label` is `low`.
- AC-4: Given any output record, when `top_signals` is read, then it holds exactly three entries, each naming a feature from `FEATURE_COLS`.
- AC-5: Given the output payload, when the summary is checked, then the three label counts sum to `n_employees`.

## WHERE — Current implementation
- `scripts/score_attrition_risk.py`

## Notes & limitations
- No labelled outcome data exists, so the model is never evaluated for accuracy, only for stability. The score is a triage prompt, not a prediction.
