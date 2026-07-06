# ISSUE: next-week advances past the session's declared total_days

Status: OPEN. Upstream-PR candidate.
Found: 2026-07-06, meta-harness ceo-bench-lab run lab-smoke_c3bf1d63
(Gemma-4-31B agent, base a8d5ade + env-override commit 7913974).

## Observed

A session created with `new-session --days 50` kept accepting
`POST /next-week` past day 50 — the run reached day 63 (and would have
continued indefinitely; it was stopped externally). `game-status` showed
`timed_out: false` throughout.

`total_days` is stored in session.json and BenchmarkConfig, and harnesses
use it as their loop bound — but the engine itself does not enforce it as
a hard stop on `next-week`.

## Why it matters

Any harness whose day limit is enforced only between agent sessions (the
natural design: check game-status after each session) cannot bound a run
when the agent advances multiple weeks inside one session. Weaker models
do exactly this: our Gemma CEO ignored the "advance one week then end the
session" instruction and advanced 9 weeks in a single session, sailing
through the day-50 limit. Benchmark comparability suffers: "a 50-day run"
is not actually guaranteed to be 50 days.

## Suggested direction (not researched further)

`next-week` (server-side) should refuse to advance once
`day >= total_days` — return a terminal status the client CLI surfaces
(e.g. "simulation complete"), and/or set `timed_out`/a `completed` flag in
game-status. Enforcing in the engine keeps the guarantee independent of
agent compliance and harness polling cadence.
