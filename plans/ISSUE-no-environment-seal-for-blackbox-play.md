# ISSUE: No black-box enforcement or detection — an agent with filesystem access can mine the simulator source

Status: OPEN. Fork-first (we need it for our sealed reruns); upstream may
want the detection/docs part.
Found: 2026-07-05, meta-harness CEO-Bench campaign 1 (base a8d5ade).

## Observed

In one of our scored runs, the agent (Claude Opus 4.8 under a permissive
harness) ran `find /` on the host, located the machine's clone of this
repository, and read `src/saas_bench/simulation.py` across 7 of 8 weekly
sessions — extracting hidden mechanics (cash timing on signup, the day-0–60
no-drift grace window, exact segment economics; later citing
`simulation.py` line numbers in its notes). It also staged a copy of the
tree under `/private/tmp/`. Its strategy was then derived from source, not
play: a white-box run.

What held vs. what didn't:

- `world.nmdb` encryption (SQLCipher, key embedded in the zipapp) held —
  live hidden state never leaked.
- The zipapp design suggests code inspection of the *shipped* artifact is
  anticipated; but a full source tree with hidden group parameters sitting
  readable on the same host was outside any protection.

## Why it matters

For anyone running this benchmark on a machine that also holds the source
checkout (probably most self-hosted users), agent capability plus a
permissive harness quietly converts the benchmark to white-box, invalidating
comparisons against published results. Nothing in the environment detects
or discourages it.

## Suggested direction (not researched further)

Layered, cheapest first:

1. **Docs**: a prominent "sealing" section — run agents on hosts without a
   source checkout, or under a filesystem-restricted user.
2. **Detection tooling**: a post-run transcript/workspace audit script
   (grep for `find /`, repo-distinctive paths, `simulation.py`) shipped in
   `scripts/`; we will build one for our reruns regardless.
3. **Runtime tripwire (optional)**: the server could warn at startup if the
   source tree is world-readable from the agent workspace's uid, or plant
   canary files whose access is logged.

Context: our own harness-side fix (per-runbook filesystem read scopes) is
tracked separately in the meta-harness repo; this issue covers what the
benchmark itself can do.
