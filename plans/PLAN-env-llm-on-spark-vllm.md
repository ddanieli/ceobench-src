# PLAN: Point the environment-side LLMs at the spark vLLM boxes

Status: PROPOSED (2026-07-06)
Scope: fork branch work (`mh-env` lineage) + campaign runtime env. NOT an
upstream-PR candidate by itself, but Phase 2 produces one (per-slot
base_url) and it composes with the observability ISSUEs.

Context for a fresh session: in meta-harness CEO-Bench campaign 1 the
env-side LLMs (social posts = Haiku slot, enterprise negotiation = Sonnet
slot) were silently dead — every Bedrock call 404'd (AWS use-case-form
gating), so customer posts fell back to templates, macro posts were
dropped, and agent posts were judged 0.0 effect. Replacement target: local
vLLM boxes `sparkone:30001` (Gemma-4-31B-it-FP8-Dynamic) and
`sparktwo:30001` (Qwen3.6-27B-FP8). Both were verified 2026-07-06 to serve
Anthropic `/v1/messages` AND OpenAI `/v1/responses` end-to-end with the
real SDKs, including tool calls. Details:
`ISSUE-openai-provider-gaps.md` (this directory).

## Phase 1 — zero-code single-box run (Gemma on sparkone, both slots)

No code changes; config + env only. This is the configuration for the
next campaign's env-LLM smoke.

Config (`src/saas_bench/config.py:677-688` fields, set via the campaign's
run config):

```
social_post_llm_provider = "anthropic"
social_post_llm_model    = "Gemma-4-31B-it-FP8-Dynamic"
enterprise_llm_provider  = "anthropic"
enterprise_llm_model     = "Gemma-4-31B-it-FP8-Dynamic"
```

Environment (steers the bare `Anthropic()` built at
`src/saas_bench/customer_llm.py:131`; no code change needed):

```
ANTHROPIC_BASE_URL=http://sparkone:30001
ANTHROPIC_API_KEY=dummy        # vLLM accepts any key
```

Notes:
- provider="anthropic" (NOT "openai"): the judge
  (`customer_llm.py:~1036`) and customer-reply (`~1160`) paths are
  Anthropic-SDK-only, and `social_post_client` raises ValueError for
  "openai" (`~197`). The anthropic path covers every call site.
- vLLM returns `usage.input_tokens/output_tokens`, so `_log_cost`
  (`customer_llm.py:~225`) should populate `api_costs` rows — one of the
  smoke pass criteria below.
- Verify the agent-side does NOT inherit these env vars if the agent runs
  on subscription auth in the same shell (campaign harness must scope them
  to the simulator process only).

Acceptance (the 14-day agentless smoke, criteria fixed in campaign
planning): zero `LLM failed` stderr lines; `api_costs` rows present; novel
non-template customer post text; nonzero agent-post judge effects.

- [ ] Add the four config values to the campaign run config.
- [ ] Export the two env vars in the simulator launch wrapper only (not
      the agent environment).
- [ ] Run the 14-day agentless smoke and record the four criteria in the
      campaign NOTES.

## Phase 2 — per-slot base_url (two-box split; upstream-PR candidate)

`_create_anthropic_client` builds ONE bare `Anthropic()` shared by both
slots, so social→sparkone / enterprise→sparktwo cannot be split by env.
Small fork change:

- [ ] Add optional `social_post_llm_base_url` / `enterprise_llm_base_url`
      config fields (default None = SDK/env behavior, fully
      backward-compatible); thread each into its slot's client
      construction in `customer_llm.py`.
- [ ] Cut the upstream PR branch from clean `a8d5ade` (not `mh-env`), per
      the fork workflow.

## Phase 3 — Qwen on sparktwo for an env slot (optional, blocked twice)

Blockers, both verified 2026-07-06:
1. Qwen thinks by default on `/v1/messages`; the first content block is a
   `thinking` block and benchmark code reading `content[0].text` raises
   `AttributeError: 'ThinkingBlock' object has no attribute 'text'`
   (silently swallowed by the judge's except-handler = the same dead-env
   failure mode as campaign 1). Working toggle:
   `extra_body={"chat_template_kwargs": {"enable_thinking": false}}` on
   `.messages.create` (Anthropic-style `thinking: disabled` is ignored).
2. vLLM 0.20.0 on sparktwo is stricter than sparkone's dev build (role
   validation) — irrelevant to benchmark env calls (top-level `system` is
   accepted) but worth aligning anyway for agent-side use.

- [ ] Either patch the `.messages.create` call sites with the
      `extra_body` toggle behind a config flag, or set no-think as the
      server-side default on sparktwo — decide when Phase 3 is actually
      wanted (Phase 1/2 don't need Qwen).

## Non-goals

- Completing the upstream OpenAI provider branch (tracked in
  `ISSUE-openai-provider-gaps.md`).
- Agent-side spark wiring (Claude Code / codex CLIs against the boxes) —
  that lives in meta-harness (`plans/PLAN-mh-codex-parity.md`) and the
  campaign harness, not in the benchmark.
