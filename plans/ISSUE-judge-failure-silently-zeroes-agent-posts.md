# ISSUE: Agent social-post judging swallows LLM failures silently — posts score 0.0 with no log line

Status: OPEN. Upstream-PR candidate (high value).
Found: 2026-07-05, meta-harness CEO-Bench campaign 1 (base a8d5ade).

## Observed

In two independent multi-week runs (49 and 42 sim days), **every agent
social-media post was scored `effect_by_group = 0.0` for every group**
(7 posts in one run, 6 in the other; verified in `agent_social_media_posts` —
all `effect_by_group` JSON values 0.0, `reasoning_by_group` empty), and
**nothing was written to stderr or any log** to indicate the judge had
failed. The runs' operator only discovered it weeks later by querying the
DB directly.

Root cause in our case: every Bedrock call failed with a 404 (Anthropic
use-case-form account gating). The customer-post and macro-post paths at
least print `[sim] ... LLM failed ...` to stderr on failure; the judge path
prints nothing.

## Where

`src/saas_bench/simulation.py`, in `_process_agent_social_posts` — the
judge fan-out collects futures and handles failure as:

```python
except Exception:
    effect_by_group[gid] = 0.0
```

(~line 4626 at a8d5ade). No stderr line, no counter, no dashboard signal.
Views are still computed from the zeroed effects, so the post looks
"processed" from the agent's perspective.

## Why it matters

The agent's social-post lever is silently dead for the whole run. An agent
(or a human evaluating one) cannot distinguish "my posts have no effect in
this world" from "the environment's judge is broken" — which corrupts any
benchmark conclusion touching the marketing/reputation channel.

## Reproduce

Run the simulator with `social_post_llm_provider` pointing at any
credential/model that errors (e.g. a Bedrock account that has not submitted
the Anthropic use-case form), have the agent `post_social`, advance a week,
and inspect `agent_social_media_posts.effect_by_group` — all zeros, no
error output anywhere.

## Suggested direction (not researched further)

Match the customer-post path's behavior at minimum: print
`[sim] agent post judge LLM failed for group {gid}: {e}` to stderr. Better:
count failures and surface a `llm_failures` field in the weekly dashboard
so a dead environment LLM is visible on day 0.
