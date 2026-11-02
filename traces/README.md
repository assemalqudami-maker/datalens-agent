# Submission traces

The required final files are:

* `success_1.jsonl`
* `near_failure_recovery.jsonl`
* `explicit_failure.jsonl`

They must come from actual live-agent execution. No success or recovery trace is fabricated in this repository. Initial setup lacked `GEMINI_API_KEY`, so the captured `configuration_failure.jsonl` records that real blocker (zero provider calls); it is not a substitute for the three full submission scenarios.

After adding the secret, run **GitHub Actions → Live Gemini evaluation**, review the `live-evidence` artifact, and copy the three verified traces here without editing out errors. The fixture data is explicitly synthetic. Runtime traces from users' private datasets belong in their workspace, not this public folder.
