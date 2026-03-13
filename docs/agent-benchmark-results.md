# SaaS Bench Agent Results

## Overview

This document tracks the performance of AI agents on the SaaS Bench 365-day business simulation benchmark.

**Benchmark Configuration:**
- Starting Cash: $500,000
- Duration: 365 days
- Goal: Maximize final cash
- Scenario: "Breakout AI Product" (default)

**Oracle Baseline:** $1,590,000 (3.18x return)

---

## Summary Comparison

| Agent | Final Cash | Return | Multiple | Outcome |
|-------|------------|--------|----------|---------|
| Oracle (Optimal) | $1,590,000 | +$1,090,000 | 3.18x | Completed |
| **GPT-5.2 Medium** | $616,016 | +$116,016 | **1.23x** | Completed |
| GPT-5.2 High | $464,277 | -$35,723 | 0.93x | Completed |
| GPT-5.2 High #3 | $389,896 | -$110,104 | 0.78x | Completed |
| Claude Sonnet 4 | $146,401 | -$353,599 | 0.29x | Completed |

**Key Findings:**
1. GPT-5.2 Medium outperforms High reasoning effort (+23% vs -7% to -22% return)
2. Claude Sonnet 4 significantly underperforms Codex GPT-5.2 (0.29x vs 0.78-1.23x)

---

## Completed Runs

### GPT-5.2 Medium (Best Result)
**Date:** 2026-02-01
**Run ID:** `run_20260201_005205`

| Metric | Value |
|--------|-------|
| Final Day | 365 / 365 |
| Final Cash | $616,016 |
| Return | +$116,016 (+23.2%) |
| Multiple | **1.23x** |
| Outcome | **Completed** |
| Duration | ~2.3 hours |
| Final Subscribers | ~5,500 |

**Strategy Evolution:**

| Phase | Days | Cash Trend | Subscribers | Strategy |
|-------|------|------------|-------------|----------|
| Conservative Start | 1-35 | $500K → $446K | 0 → 48 | Very low spend (~$1.5K/day) |
| Growth Ramp | 35-60 | $446K → $380K | 48 → 383 | Increased ad spend |
| Consolidation | 60-110 | $380K → $312K | 383 → 328 | Cut spending, slight churn |
| Sustainable Growth | 110-170 | $312K → $295K | 328 → 1,100 | Found profitable equilibrium |
| Breakeven | 160-200 | ~$295K stable | 900 → 1,100 | Cash neutral with growth |
| Profitable Scale | 200-365 | $295K → $616K | 1,100 → 5,500 | Cash + subscriber growth |

**Key Observations:**
- Took conservative approach compared to oracle
- Hit breakeven around Day 160 with ~900 subscribers
- Successfully scaled from breakeven to profitable growth
- Maintained cash discipline throughout

---

### GPT-5.2 High
**Date:** 2026-02-01
**Run ID:** `run_20260201_150820`

| Metric | Value |
|--------|-------|
| Final Day | 365 / 365 |
| Final Cash | $464,277 |
| Return | -$35,723 (-7.1%) |
| Multiple | **0.93x** |
| Outcome | **Completed** |
| Duration | ~3.5 hours |
| Final Subscribers | ~9,500 |

**Strategy Evolution:**

| Phase | Days | Cash Trend | Subscribers | Strategy |
|-------|------|------------|-------------|----------|
| Aggressive Growth | 1-70 | $500K → $414K | 0 → 5,700 | Heavy ad spend, rapid scaling |
| Cash Crisis | 70-142 | $414K → $275K | 5,700 → 6,300 | Burn continues, slow recovery |
| Stabilization | 142-220 | $275K → $319K | 6,300 → 6,900 | Reached profitability |
| Late Growth | 220-365 | $319K → $464K | 6,900 → 9,500 | Steady cash + sub growth |

**Key Observations:**
- More aggressive early strategy (9,500 subs vs 5,500 for Medium)
- Burned cash much lower ($275K minimum vs $295K for Medium)
- Higher subscriber count but lower final cash
- The aggressive growth didn't translate to better returns

---

### GPT-5.2 High #3
**Date:** 2026-02-01
**Run ID:** `run_20260201_184326`

| Metric | Value |
|--------|-------|
| Final Day | 365 / 365 |
| Final Cash | $389,896 |
| Return | -$110,104 (-22.0%) |
| Multiple | **0.78x** |
| Outcome | **Completed** |
| Duration | ~4 hours |

**Key Observations:**
- Worst performing GPT-5.2 run
- Consistent with High reasoning leading to suboptimal outcomes
- Multiple timeout-and-resume cycles during the run

---

### Claude Code Sonnet 4
**Date:** 2026-02-02
**Run ID:** `run_20260202_011357`

| Metric | Value |
|--------|-------|
| Final Day | 365 / 365 |
| Final Cash | $146,401 |
| Return | -$353,599 (-70.7%) |
| Multiple | **0.29x** |
| Outcome | **Completed** |
| Duration | ~2 hours |
| Final Subscribers | Low (exact TBD) |

**Key Observations:**
- Significantly worse performance than Codex GPT-5.2
- Steady cash decline throughout the simulation
- Never achieved sustainable profitability
- Did complete the full 365 days without bankruptcy

**Log Files:**
- `results/claude-code-runs/run_20260202_011357/logs/tool_calls_20260202_011357.jsonl` (1.5MB)
- `results/claude-code-runs/run_20260202_011357/logs/rationales_20260202_011357.json` (375KB)

---

## Analysis

### Medium vs High Reasoning Effort

| Metric | Medium | High | Winner |
|--------|--------|------|--------|
| Final Cash | $616,016 | $464,277 | Medium (+$152K) |
| Return | +23.2% | -7.1% | Medium |
| Final Subscribers | ~5,500 | ~9,500 | High (+4,000) |
| Lowest Cash Point | $295K | $275K | Medium (safer) |
| Duration | 2.3 hrs | 3.5 hrs | Medium (faster) |

**Conclusion:** Medium reasoning effort produces better financial outcomes despite fewer subscribers. The more measured growth strategy of Medium (conservative start, gradual scaling) outperforms High's aggressive early growth approach. High reasoning may lead to over-optimization on subscriber growth at the expense of profitability.

### Codex GPT-5.2 vs Claude Sonnet 4

| Metric | GPT-5.2 Medium | GPT-5.2 High (avg) | Claude Sonnet 4 |
|--------|----------------|-------------------|-----------------|
| Final Cash | $616,016 | $427,087 | $146,401 |
| Return | +23.2% | -14.6% | -70.7% |
| Multiple | 1.23x | 0.85x | 0.29x |

**Conclusion:** Codex GPT-5.2 significantly outperforms Claude Sonnet 4 on this benchmark. Even the worst GPT-5.2 High run ($389K) beats Claude Sonnet by over 2.6x. This suggests that Codex agents may be better suited for long-horizon business simulation tasks requiring sustained strategic planning.

---

## Technical Notes

### Common Issues
1. **Stuck at Day 40-50**: Agent sometimes enters long reasoning loops without calling `next_day`
2. **Timeout after 1 hour**: Codex has a 3600s timeout per iteration
3. **Requires multiple restarts**: Some runs need to be killed and restarted

### Runner Command
```bash
uv run python src/saas_bench/agents/codex/run_test_sandboxed.py \
  --days 365 \
  --model gpt-5.2 \
  --reasoning-effort [low|medium|high]
```

---

## Run History

### Log File Locations

**Codex GPT-5.2 Runs:**
- `results/codex-runs/run_20260201_005205/` - GPT-5.2 Medium (Best)
- `results/codex-runs/run_20260201_150820/` - GPT-5.2 High
- `results/codex-runs/run_20260201_184326/` - GPT-5.2 High #3

**Claude Code Runs:**
- `results/claude-code-runs/run_20260202_011357/` - Claude Sonnet 4

**Each run directory contains:**
- `logs/tool_calls_*.jsonl` - All MCP tool calls with arguments and results
- `logs/rationales_*.json` - Agent reasoning/rationale for each day
- `logs/agent_conversation_*.jsonl` - Full conversation log
- `logs/run_*.json` - Final summary with outcome
- `world.db` - SQLite database with full simulation state

### Incomplete Runs (Not Counted)
- `run_20260131_192428` - Medium, stuck at Day 47
- `run_20260131_224704` - Medium, stuck at Day 48
- `run_20260201_032948` - High, stuck at Day 142
- `run_20260201_183924` - High, stuck at Day 45 (killed)
- `run_20260201_184122` - Medium, stuck at Day 33 (killed)

These runs stalled due to the agent entering long reasoning loops without progressing. They were excluded from the main comparison.
