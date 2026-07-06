# ISSUE: Macro-economy posts are skipped entirely on LLM failure (customer posts get a template fallback; macro posts get nothing)

Status: OPEN. Minor. Possible upstream PR alongside the logging fixes.
Found: 2026-07-05, meta-harness CEO-Bench campaign 1 (base a8d5ade).

## Observed

In `src/saas_bench/simulation.py`, the unified post-generation results loop
handles failures asymmetrically:

- Regular customer posts: on failure, content falls back to
  `generate_template_post(...)` (~line 4322) — sentiment, virality, and
  reputation mechanics still run, so the world keeps its social signal
  (with canned text).
- Macro posts: `if not result['success'] or not result['text']: continue`
  (~line 4349) — the post is dropped entirely, with only a stderr line
  (`[sim] macro post LLM failed`, ~4113).

In our two runs (where all Bedrock calls failed — see companion issues),
this meant 23 and 15 macro posts respectively never entered the world:
zero macro-economy signal in the social feed for the entire runs, while
customer posts continued via templates.

## Why it matters

The macro posts carry the PMI/economy narrative into the social feed
(sentiment/likes/shares derived from PMI thresholds directly below the skip,
~4352+). Under LLM failure the world silently loses one information channel
while keeping another, changing the environment's information structure in
a way no one signed up for and nothing reports.

## Suggested direction (not researched further)

Smallest fix: a template fallback for macro posts symmetric with customer
posts (the sentiment/likes/shares are already computed from PMI, only the
text is missing — a canned "economy looks strong/soft" pool would do).
Alternatively, count and surface dropped macro posts in the dashboard so
the degradation is at least visible.
