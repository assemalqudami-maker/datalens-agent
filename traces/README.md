# Submission traces

These three files are preserved from the successful live Gemini evaluation run on 2026-11-03:

* `success_1.jsonl` — successful evidence-based CSV analysis.
* `near_failure_recovery.jsonl` — a real invalid-column tool error followed by recovery to the correct `revenue` column.
* `explicit_failure.jsonl` — an honest failed task because the dataset contains no cost data required for exact profit.

The evaluation also ran three hostile-input scenarios and all assertions passed. The complete 10-case evidence remains available in the GitHub Actions `live-evidence` artifact for run `41554421307`.

These are real provider traces from Gemini `gemini-3.5-flash-lite`; they are not scripted-model substitutes. The fixture CSV data is synthetic. Runtime traces from users' private datasets belong in their private workspace, not this public folder.
