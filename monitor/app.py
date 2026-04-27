"""BossBench Run Monitor — Local FastAPI webapp for monitoring parallel runs.

Reads from bash_agent_runs/ SQLite databases and JSONL logs.
Exposed via seashells for remote access.
"""

import json
import sqlite3
import os
import re
import html
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

RUNS_DIR = Path(__file__).parent.parent / "bash_agent_runs"

# Run registry — labels for known runs
RUN_REGISTRY = {
    "1a4872f2": {"label": "Sonnet 4.5 test run", "model": "claude-sonnet-4-5", "seed": 42, "days": 3650},
    "fbbe2386": {"label": "GLM-5 test run", "model": "GLM-5-FP8", "seed": 42, "days": 3650},
    "0608fbc3": {"label": "GLM-5 3yr #1", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "1b2bb6c0": {"label": "GLM-5 3yr #2", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "9dd2e48b": {"label": "GLM-5 3yr #3", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "c2f52635": {"label": "GLM-5 3yr #4", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "395fa005": {"label": "GLM-5 3yr #5", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
}

app = FastAPI(title="BossBench Monitor")


def _get_run_ids():
    """List all run IDs sorted by registry order then alphabetically."""
    if not RUNS_DIR.exists():
        return []
    dirs = sorted(RUNS_DIR.iterdir())
    ids = [d.name.replace("run_", "") for d in dirs if d.is_dir() and d.name.startswith("run_")]
    # Sort: registry order first, then unknown
    registry_order = list(RUN_REGISTRY.keys())
    known = [r for r in registry_order if r in ids]
    unknown = [r for r in ids if r not in registry_order]
    return known + unknown


def _get_db(run_id: str) -> Optional[sqlite3.Connection]:
    db_path = RUNS_DIR / f"run_{run_id}" / "world.db"
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _get_run_summary(run_id: str) -> dict:
    """Get summary stats for a run."""
    run_dir = RUNS_DIR / f"run_{run_id}"
    reg = RUN_REGISTRY.get(run_id, {})
    summary = {
        "run_id": run_id,
        "label": reg.get("label", f"run_{run_id}"),
        "model": reg.get("model", "unknown"),
        "seed": reg.get("seed"),
        "total_days": reg.get("days"),
    }

    # Read config.json
    config_path = run_dir / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
            summary["model"] = cfg.get("model", summary["model"])
            summary["seed"] = cfg.get("seed", summary["seed"])
            summary["total_days"] = cfg.get("total_days", summary["total_days"])

    # Read checkpoint
    cp_path = run_dir / "checkpoint.json"
    if cp_path.exists():
        with open(cp_path) as f:
            cp = json.load(f)
            summary["current_day"] = cp.get("day", cp.get("current_day"))
            summary["agent_turns"] = cp.get("agent_total_turns")
    else:
        summary["current_day"] = None
        summary["agent_turns"] = None

    # Query DB for live stats
    conn = _get_db(run_id)
    if conn:
        try:
            summary["cash"] = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
            summary["subscribers"] = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL"
            ).fetchone()[0]
            summary["founder_dividends"] = conn.execute(
                "SELECT COALESCE(SUM(founder_payout), 0) FROM dividends"
            ).fetchone()[0]
            # MRR
            summary["mrr"] = conn.execute(
                "SELECT COALESCE(SUM(effective_price), 0) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL"
            ).fetchone()[0]
            # Latest day from config_history
            row = conn.execute("SELECT MAX(day) FROM config_history").fetchone()
            if row and row[0] and summary["current_day"] is None:
                summary["current_day"] = row[0]
        except Exception as e:
            summary["db_error"] = str(e)
        finally:
            conn.close()

    # Count tool results
    tr_path = run_dir / "logs" / f"tool_results_{run_id}.jsonl"
    if tr_path.exists():
        with open(tr_path) as f:
            summary["tool_calls"] = sum(1 for _ in f)
    else:
        summary["tool_calls"] = 0

    return summary


def _get_recent_actions(run_id: str, limit: int = 50, offset: int = 0) -> list:
    """Get recent tool calls from tool_results JSONL."""
    tr_path = RUNS_DIR / f"run_{run_id}" / "logs" / f"tool_results_{run_id}.jsonl"
    if not tr_path.exists():
        return []
    entries = []
    with open(tr_path) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    # Return most recent first
    entries.reverse()
    return entries[offset:offset + limit]


def _get_raw_responses(run_id: str, limit: int = 20, offset: int = 0) -> list:
    """Get raw LLM responses."""
    rr_path = RUNS_DIR / f"run_{run_id}" / "logs" / f"raw_responses_{run_id}.jsonl"
    if not rr_path.exists():
        return []
    entries = []
    with open(rr_path) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.reverse()
    return entries[offset:offset + limit]


# ─── API Endpoints ───

@app.get("/api/runs")
def api_runs():
    ids = _get_run_ids()
    return [_get_run_summary(r) for r in ids]


@app.get("/api/run/{run_id}")
def api_run(run_id: str):
    return _get_run_summary(run_id)


@app.get("/api/run/{run_id}/actions")
def api_actions(run_id: str, limit: int = 50, offset: int = 0):
    return _get_recent_actions(run_id, limit, offset)


@app.get("/api/run/{run_id}/responses")
def api_responses(run_id: str, limit: int = 20, offset: int = 0):
    return _get_raw_responses(run_id, limit, offset)


@app.get("/api/run/{run_id}/timeseries")
def api_timeseries(run_id: str):
    """Get daily cash/subscribers/MRR timeseries from ledger + config_history."""
    conn = _get_db(run_id)
    if not conn:
        return {"error": "DB not found"}
    try:
        # Cash balance over time (cumulative ledger by day)
        rows = conn.execute("""
            SELECT day, SUM(amount) as daily_net
            FROM ledger GROUP BY day ORDER BY day
        """).fetchall()
        cash_series = []
        running = 0
        for r in rows:
            running += r["daily_net"]
            cash_series.append({"day": r["day"], "cash": round(running, 2)})

        # Subscriber count by day (approximate from config_history or subscriptions)
        sub_rows = conn.execute("""
            SELECT l.day, COUNT(DISTINCT s.subscription_id) as subs
            FROM (SELECT DISTINCT day FROM ledger) l
            LEFT JOIN subscriptions s ON s.start_day <= l.day
                AND (s.end_day IS NULL OR s.end_day > l.day)
                AND s.status IN ('subscribed', 'cancelled')
            GROUP BY l.day ORDER BY l.day
        """).fetchall()
        sub_series = [{"day": r["day"], "subscribers": r["subs"]} for r in sub_rows]

        # Founder dividends cumulative
        div_rows = conn.execute("""
            SELECT day, SUM(founder_payout) as daily_div
            FROM dividends GROUP BY day ORDER BY day
        """).fetchall()
        div_series = []
        running_div = 0
        for r in div_rows:
            running_div += r["daily_div"]
            div_series.append({"day": r["day"], "dividends": round(running_div, 2)})

        return {"cash": cash_series, "subscribers": sub_series, "dividends": div_series}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ─── HTML Dashboard ───

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BossBench Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text2: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --red: #f85149; --yellow: #d29922; --purple: #bc8cff;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }

  /* Header */
  .header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }
  .header h1 { font-size: 18px; font-weight: 600; white-space: nowrap; }
  .header select { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; font-size: 14px; min-width: 260px; }
  .header .refresh-info { margin-left: auto; font-size: 12px; color: var(--text2); display: flex; align-items: center; gap: 8px; }
  .header .refresh-info .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); display: inline-block; }

  /* Layout */
  .container { max-width: 1400px; margin: 0 auto; padding: 16px 24px; }

  /* Overview grid */
  .overview { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .run-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; cursor: pointer; transition: border-color 0.2s; }
  .run-card:hover, .run-card.active { border-color: var(--accent); }
  .run-card .label { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
  .run-card .meta { font-size: 12px; color: var(--text2); margin-bottom: 8px; }
  .agent-badge { display: inline-block; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; padding: 1px 6px; border-radius: 3px; margin-right: 6px; vertical-align: 1px; text-transform: uppercase; }
  .agent-badge.bash { background: #0366d6; color: #fff; }
  .agent-badge.codex { background: #6f42c1; color: #fff; }
  .run-card .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 13px; }
  .run-card .stats .val { font-weight: 600; }
  .run-card .stats .val.cash { color: var(--green); }
  .run-card .stats .val.divs { color: var(--yellow); }
  .run-card .progress { margin-top: 8px; }
  .run-card .progress-bar { background: var(--bg); border-radius: 4px; height: 6px; overflow: hidden; }
  .run-card .progress-fill { background: var(--accent); height: 100%; border-radius: 4px; transition: width 0.3s; }
  .run-card .progress-text { font-size: 11px; color: var(--text2); margin-top: 2px; }

  /* Detail panel */
  .detail { display: none; }
  .detail.visible { display: block; }
  .detail h2 { font-size: 16px; margin-bottom: 12px; color: var(--accent); }

  /* Charts */
  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
  .chart-box { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .chart-box h3 { font-size: 13px; color: var(--text2); margin-bottom: 8px; }
  .chart-box canvas { max-height: 220px; }

  /* Tabs */
  .tabs { display: flex; gap: 0; margin-bottom: 0; }
  .tab { padding: 8px 20px; font-size: 13px; font-weight: 500; cursor: pointer; border: 1px solid var(--border); border-bottom: none; background: var(--bg); color: var(--text2); border-radius: 6px 6px 0 0; }
  .tab.active { background: var(--surface); color: var(--text); }
  .tab-content { background: var(--surface); border: 1px solid var(--border); border-radius: 0 8px 8px 8px; padding: 0; display: none; }
  .tab-content.active { display: block; }

  /* Action log */
  .action-list { max-height: 600px; overflow-y: auto; }
  .action-item { padding: 10px 16px; border-bottom: 1px solid var(--border); font-size: 13px; }
  .action-item:last-child { border-bottom: none; }
  .action-item .action-header { display: flex; gap: 12px; align-items: baseline; margin-bottom: 4px; }
  .action-item .day-badge { background: var(--accent); color: #000; font-size: 11px; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
  .action-item .turn-badge { background: var(--border); font-size: 11px; padding: 1px 6px; border-radius: 3px; }
  .action-item .tool-name { font-weight: 600; color: var(--purple); }
  .action-item .timestamp { color: var(--text2); font-size: 11px; margin-left: auto; }
  .action-item .args { color: var(--text2); font-size: 12px; margin: 2px 0; font-family: 'SF Mono', Monaco, Consolas, monospace; }
  .action-item .result-toggle { color: var(--accent); cursor: pointer; font-size: 12px; user-select: none; }
  .action-item .result-content { display: none; margin-top: 6px; background: var(--bg); border-radius: 6px; padding: 12px; font-size: 12px; font-family: 'SF Mono', Monaco, Consolas, monospace; white-space: pre-wrap; word-break: break-word; max-height: 500px; overflow-y: auto; line-height: 1.5; }
  .action-item .result-content.visible { display: block; }

  /* Response cards */
  .response-card { padding: 14px 16px; border-bottom: 1px solid var(--border); }
  .response-card:last-child { border-bottom: none; }
  .response-card .resp-header { display: flex; gap: 12px; align-items: baseline; margin-bottom: 6px; }
  .response-card .content-block { background: var(--bg); border-radius: 6px; padding: 12px; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; max-height: 600px; overflow-y: auto; }
  .response-card .content-block code { background: #1c2129; padding: 1px 4px; border-radius: 3px; font-family: 'SF Mono', Monaco, Consolas, monospace; font-size: 12px; }
  .response-card .tool-calls { margin-top: 8px; }
  .response-card .tc-item { background: var(--bg); border-radius: 6px; padding: 8px 12px; margin-top: 4px; font-size: 12px; }
  .response-card .tc-item .tc-name { color: var(--purple); font-weight: 600; }
  .response-card .tc-item pre { margin-top: 4px; font-family: 'SF Mono', Monaco, Consolas, monospace; white-space: pre-wrap; color: var(--text2); }

  /* Loading */
  .loading { text-align: center; padding: 40px; color: var(--text2); }

  /* Compare table */
  .compare-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .compare-table th, .compare-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
  .compare-table th { color: var(--text2); font-weight: 500; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  .compare-table td.num { text-align: right; font-family: 'SF Mono', Monaco, Consolas, monospace; }
  .compare-table tr:hover { background: rgba(88,166,255,0.05); }

  @media (max-width: 800px) {
    .charts { grid-template-columns: 1fr; }
    .overview { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>BossBench Monitor</h1>
  <select id="runSelect" onchange="selectRun(this.value)">
    <option value="">— All Runs Overview —</option>
  </select>
  <div class="refresh-info">
    <span class="dot"></span>
    Auto-refresh 15s
    <span id="lastUpdate"></span>
  </div>
</div>

<div class="container">
  <!-- Overview (all runs) -->
  <div id="overviewSection">
    <div style="margin-bottom: 16px;">
      <h2 style="font-size:16px; color:var(--text2); margin-bottom:8px;">Compare All Runs</h2>
      <div style="background:var(--surface); border:1px solid var(--border); border-radius:8px; overflow:hidden;">
        <table class="compare-table">
          <thead><tr>
            <th>Run</th><th>Model</th><th>Day</th><th>Progress</th>
            <th style="text-align:right">Cash</th>
            <th style="text-align:right">Subscribers</th>
            <th style="text-align:right">MRR</th>
            <th style="text-align:right">F. Dividends</th>
            <th style="text-align:right">Turns</th>
          </tr></thead>
          <tbody id="compareBody"></tbody>
        </table>
      </div>
    </div>
    <div class="overview" id="runCards"></div>
  </div>

  <!-- Detail (single run) -->
  <div id="detailSection" class="detail">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
      <button onclick="selectRun('')" style="background:var(--surface); border:1px solid var(--border); color:var(--accent); padding:4px 12px; border-radius:6px; cursor:pointer; font-size:13px;">← Back</button>
      <h2 id="detailTitle" style="margin:0;"></h2>
    </div>

    <!-- Stats row -->
    <div class="overview" id="detailStats" style="grid-template-columns: repeat(6, 1fr);"></div>

    <!-- Charts -->
    <div class="charts">
      <div class="chart-box"><h3>Cash Balance</h3><canvas id="cashChart"></canvas></div>
      <div class="chart-box"><h3>Subscribers</h3><canvas id="subsChart"></canvas></div>
    </div>

    <!-- Tabs: Actions / Responses -->
    <div class="tabs">
      <div class="tab active" onclick="switchTab('actions')">Tool Calls</div>
      <div class="tab" onclick="switchTab('responses')">LLM Responses</div>
    </div>
    <div id="actionsTab" class="tab-content active">
      <div class="action-list" id="actionList"><div class="loading">Loading...</div></div>
    </div>
    <div id="responsesTab" class="tab-content">
      <div class="action-list" id="responseList"><div class="loading">Loading...</div></div>
    </div>
  </div>
</div>

<script>
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);
let allRuns = [];
let currentRun = null;
let charts = {};
let refreshTimer = null;

function fmt(n, prefix='') {
  if (n == null) return '—';
  if (Math.abs(n) >= 1e6) return prefix + (n/1e6).toFixed(2) + 'M';
  if (Math.abs(n) >= 1e3) return prefix + (n/1e3).toFixed(1) + 'K';
  return prefix + n.toLocaleString();
}
function fmtCash(n) { return n == null ? '—' : '$' + fmt(n); }
function pct(cur, total) { return total ? Math.round(cur / total * 100) : 0; }
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function timeAgo(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const s = Math.floor((Date.now() - d) / 1000);
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s/60) + 'm ago';
  return Math.floor(s/3600) + 'h ago';
}

// Pretty-print JSON or Python code
function fmtResult(raw) {
  if (!raw) return '(empty)';
  const s = String(raw);
  // Try JSON parse for pretty print
  try {
    const obj = JSON.parse(s);
    return esc(JSON.stringify(obj, null, 2));
  } catch(e) {}
  // Highlight Python-ish code
  return esc(s);
}

function fmtArgs(args) {
  if (!args) return '';
  if (typeof args === 'string') return esc(args);
  if (args.command) return esc(args.command);
  if (args.path) return esc(args.path);
  if (args.code) return esc(args.code.substring(0, 200));
  return esc(JSON.stringify(args));
}

// ─── Data fetch ───
async function fetchRuns() {
  const r = await fetch('/api/runs');
  allRuns = await r.json();
  renderOverview();
  if (currentRun) renderDetail();
  $('#lastUpdate').textContent = new Date().toLocaleTimeString();
}

// ─── Overview ───
function renderOverview() {
  // Compare table
  let tbody = '';
  for (const r of allRuns) {
    const p = pct(r.current_day || 0, r.total_days || 1095);
    const agentBadge = r.agent_type ? `<span class="agent-badge ${r.agent_type==='codex'?'codex':'bash'}">${r.agent_type==='codex'?'CODEX':'BASH'}</span>` : '';
    tbody += `<tr style="cursor:pointer" onclick="selectRun('${r.run_id}')">
      <td>${agentBadge}<strong>${esc(r.label)}</strong><br><span style="color:var(--text2);font-size:11px">${r.run_id}</span></td>
      <td style="font-size:12px">${esc(r.model)}</td>
      <td class="num">${r.current_day || '—'}</td>
      <td><div style="display:flex;align-items:center;gap:8px;">
        <div style="flex:1;background:var(--bg);border-radius:3px;height:4px;"><div style="width:${p}%;background:var(--accent);height:100%;border-radius:3px;"></div></div>
        <span style="font-size:11px;color:var(--text2);min-width:35px">${p}%</span>
      </div></td>
      <td class="num" style="color:${(r.cash||0)<0?'var(--red)':'var(--green)'}">${fmtCash(r.cash)}</td>
      <td class="num">${fmt(r.subscribers)}</td>
      <td class="num">${fmtCash(r.mrr)}</td>
      <td class="num" style="color:var(--yellow)">${fmtCash(r.founder_dividends)}</td>
      <td class="num">${fmt(r.agent_turns)}</td>
    </tr>`;
  }
  $('#compareBody').innerHTML = tbody;

  // Cards
  let cards = '';
  for (const r of allRuns) {
    const p = pct(r.current_day || 0, r.total_days || 1095);
    const cardBadge = r.agent_type ? `<span class="agent-badge ${r.agent_type==='codex'?'codex':'bash'}">${r.agent_type==='codex'?'CODEX':'BASH'}</span>` : '';
    cards += `<div class="run-card ${currentRun===r.run_id?'active':''}" onclick="selectRun('${r.run_id}')">
      <div class="label">${cardBadge}${esc(r.label)}</div>
      <div class="meta">${esc(r.model)} · seed ${r.seed} · ${r.run_id}</div>
      <div class="stats">
        <div>Cash: <span class="val cash">${fmtCash(r.cash)}</span></div>
        <div>Subs: <span class="val">${fmt(r.subscribers)}</span></div>
        <div>MRR: <span class="val">${fmtCash(r.mrr)}</span></div>
        <div>Divs: <span class="val divs">${fmtCash(r.founder_dividends)}</span></div>
      </div>
      <div class="progress">
        <div class="progress-bar"><div class="progress-fill" style="width:${p}%"></div></div>
        <div class="progress-text">Day ${r.current_day||'?'} / ${r.total_days||'?'} (${p}%) · ${fmt(r.agent_turns)} turns</div>
      </div>
    </div>`;
  }
  $('#runCards').innerHTML = cards;

  // Update select
  const sel = $('#runSelect');
  const curVal = sel.value;
  sel.innerHTML = '<option value="">— All Runs Overview —</option>';
  for (const r of allRuns) {
    sel.innerHTML += `<option value="${r.run_id}" ${r.run_id===curVal?'selected':''}>${esc(r.label)} (${r.run_id})</option>`;
  }
}

// ─── Detail ───
async function selectRun(runId) {
  currentRun = runId || null;
  $('#runSelect').value = runId;
  if (!runId) {
    $('#overviewSection').style.display = '';
    $('#detailSection').classList.remove('visible');
    return;
  }
  $('#overviewSection').style.display = 'none';
  $('#detailSection').classList.add('visible');
  renderDetail();
}

async function renderDetail() {
  if (!currentRun) return;
  const r = allRuns.find(x => x.run_id === currentRun);
  if (!r) return;

  const p = pct(r.current_day || 0, r.total_days || 1095);
  $('#detailTitle').textContent = `${r.label} — ${r.model} (${r.run_id})`;

  // Stats
  const stats = [
    {label:'Day', val: `${r.current_day||'?'} / ${r.total_days||'?'} (${p}%)`},
    {label:'Cash', val: fmtCash(r.cash), cls: (r.cash||0)<0?'color:var(--red)':'color:var(--green)'},
    {label:'Subscribers', val: fmt(r.subscribers)},
    {label:'MRR', val: fmtCash(r.mrr)},
    {label:'F. Dividends', val: fmtCash(r.founder_dividends), cls:'color:var(--yellow)'},
    {label:'Agent Turns', val: fmt(r.agent_turns)},
  ];
  $('#detailStats').innerHTML = stats.map(s =>
    `<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;">
      <div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:0.5px;">${s.label}</div>
      <div style="font-size:18px;font-weight:700;margin-top:2px;${s.cls||''}">${s.val}</div>
    </div>`
  ).join('');

  // Charts
  loadCharts(currentRun);

  // Actions
  loadActions(currentRun);
  loadResponses(currentRun);
}

async function loadCharts(runId) {
  const res = await fetch(`/api/run/${runId}/timeseries`);
  const data = await res.json();
  if (data.error) return;

  const chartOpts = (label, color) => ({
    type: 'line',
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#21262d' }, ticks: { color: '#8b949e', font: { size: 10 } } },
        y: { grid: { color: '#21262d' }, ticks: { color: '#8b949e', font: { size: 10 } } },
      },
      elements: { point: { radius: 0 }, line: { borderWidth: 2 } },
    },
  });

  // Cash chart
  if (charts.cash) charts.cash.destroy();
  const cashCtx = $('#cashChart').getContext('2d');
  charts.cash = new Chart(cashCtx, {
    ...chartOpts('Cash', '#3fb950'),
    data: {
      labels: (data.cash || []).map(d => d.day),
      datasets: [{
        label: 'Cash',
        data: (data.cash || []).map(d => d.cash),
        borderColor: '#3fb950', backgroundColor: 'rgba(63,185,80,0.1)', fill: true,
      }]
    }
  });

  // Subs chart
  if (charts.subs) charts.subs.destroy();
  const subsCtx = $('#subsChart').getContext('2d');
  charts.subs = new Chart(subsCtx, {
    ...chartOpts('Subscribers', '#58a6ff'),
    data: {
      labels: (data.subscribers || []).map(d => d.day),
      datasets: [{
        label: 'Subscribers',
        data: (data.subscribers || []).map(d => d.subscribers),
        borderColor: '#58a6ff', backgroundColor: 'rgba(88,166,255,0.1)', fill: true,
      }]
    }
  });
}

async function loadActions(runId) {
  const res = await fetch(`/api/run/${runId}/actions?limit=100`);
  const actions = await res.json();
  if (!actions.length) { $('#actionList').innerHTML = '<div class="loading">No actions yet</div>'; return; }

  let html = '';
  for (const a of actions) {
    const toolEmoji = {'bash':'🔧','read_file':'📂','write_file':'✍️','edit_file':'✏️','search_files':'🔍','glob_files':'🔍','_dashboard':'📊','_reasoning':'💭'}[a.tool] || '⚙️';
    const argsStr = fmtArgs(a.arguments);
    const resultStr = fmtResult(a.result);
    const id = 'r_' + Math.random().toString(36).slice(2,8);
    html += `<div class="action-item">
      <div class="action-header">
        <span class="day-badge">Day ${a.day}</span>
        <span class="turn-badge">Turn ${a.turn}</span>
        <span class="tool-name">${toolEmoji} ${esc(a.tool)}</span>
        <span class="timestamp">${timeAgo(a.timestamp)}</span>
      </div>
      ${argsStr ? `<div class="args">${argsStr}</div>` : ''}
      <span class="result-toggle" onclick="this.nextElementSibling.classList.toggle('visible'); this.textContent = this.textContent === '▶ Show result' ? '▼ Hide result' : '▶ Show result';">▶ Show result</span>
      <div class="result-content" id="${id}">${resultStr}</div>
    </div>`;
  }
  $('#actionList').innerHTML = html;
}

async function loadResponses(runId) {
  const res = await fetch(`/api/run/${runId}/responses?limit=30`);
  const responses = await res.json();
  if (!responses.length) { $('#responseList').innerHTML = '<div class="loading">No responses yet</div>'; return; }

  let html = '';
  for (const r of responses) {
    const raw = r.raw_response || {};
    const choices = raw.choices || [];
    const msg = choices[0]?.message || {};
    const content = msg.content || '';
    const toolCalls = msg.tool_calls || [];
    const usage = raw.usage || {};

    html += `<div class="response-card">
      <div class="resp-header">
        <span class="day-badge">Day ${r.day}</span>
        <span class="turn-badge">Turn ${r.turn}</span>
        <span style="font-size:12px;color:var(--text2)">
          ${usage.prompt_tokens ? `${fmt(usage.prompt_tokens)} in / ${fmt(usage.completion_tokens)} out` : ''}
        </span>
        <span class="timestamp">${timeAgo(r.timestamp)}</span>
      </div>
      ${content ? `<div class="content-block">${fmtResult(content)}</div>` : ''}
      ${toolCalls.length ? `<div class="tool-calls">
        <div style="font-size:12px;color:var(--text2);margin-top:6px;">Tool calls (${toolCalls.length}):</div>
        ${toolCalls.map(tc => {
          let args = '';
          try { args = JSON.stringify(JSON.parse(tc.function?.arguments || '{}'), null, 2); }
          catch(e) { args = tc.function?.arguments || ''; }
          return `<div class="tc-item">
            <span class="tc-name">${esc(tc.function?.name || '?')}</span>
            <pre>${esc(args)}</pre>
          </div>`;
        }).join('')}
      </div>` : ''}
    </div>`;
  }
  $('#responseList').innerHTML = html;
}

function switchTab(tab) {
  $$('.tab').forEach(t => t.classList.remove('active'));
  $$('.tab-content').forEach(t => t.classList.remove('active'));
  if (tab === 'actions') {
    $$('.tab')[0].classList.add('active');
    $('#actionsTab').classList.add('active');
  } else {
    $$('.tab')[1].classList.add('active');
    $('#responsesTab').classList.add('active');
  }
}

// ─── Init ───
fetchRuns();
refreshTimer = setInterval(fetchRuns, 15000);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
