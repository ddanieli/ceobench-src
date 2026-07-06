# ISSUE: No request/response logging for environment-LLM calls

Status: OPEN. Upstream-PR candidate.
Found: 2026-07-05, meta-harness CEO-Bench campaign 1 (base a8d5ade).

## Observed

After two multi-week runs we needed to audit what the environment LLMs
(social posts / judge / negotiation) were actually asked and what they
answered. Nothing records it:

- `api_costs` (written by `CustomerSimulator._log_cost`,
  `src/saas_bench/customer_llm.py` ~line 225) stores only success metadata
  (day, purpose, token counts, model) — and only on success. In our runs it
  was empty, which was itself the key diagnostic (zero successful calls).
- Failures appear only as unstructured stderr lines, and only on the
  customer-post and macro-post paths (`[sim] social post LLM failed ...`,
  `simulation.py` ~4068/~4113); the judge and reply paths log nothing.
- Successful *outputs* are recoverable indirectly from world-state tables
  (`social_media_posts` content, `agent_social_media_posts.reasoning_by_group`)
  — this is what `llm_replay.py` reads — but the *requests* (rendered
  prompts) are never persisted, and failed calls leave no structured trace.

## Why it matters

1. Post-hoc forensics on a finished run (what did the env LLM see/say?) is
   impossible; we had to reconstruct prompts from templates + world state.
2. The replay cache (`BOSSBENCH_LLM_REPLAY_DB`) only covers calls that
   succeeded and whose outputs land in world tables; a first-class call log
   would make replay complete and deterministic.
3. A run with a broken LLM configuration looks normal until someone queries
   `api_costs` by hand (see companion issue on the silent judge).

## Suggested direction (not researched further)

An `llm_calls` table (or JSONL sidecar): timestamp/day, purpose, model,
provider, success flag, error text on failure, and (optionally, size-gated
or hash-only) the rendered request and raw response. Even metadata+error
rows for failures would have caught our dead-environment case on day 0.
