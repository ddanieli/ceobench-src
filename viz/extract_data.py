#!/usr/bin/env python3
"""Extract run data into a JSON structure for the web visualization."""
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

RUN_DIR = Path(__file__).parent.parent / "baseline_runs" / "run_b118ae38"
OUT_DIR = Path(__file__).parent / "data"
OUT_DIR.mkdir(exist_ok=True)

def extract():
    # 1. Load tool results (per-day tool calls with arguments and results)
    tool_calls_by_day = defaultdict(list)
    with open(RUN_DIR / "logs" / "tool_results_b118ae38.jsonl") as f:
        for line in f:
            d = json.loads(line)
            day = d["day"]
            tool_calls_by_day[day].append({
                "turn": d.get("turn"),
                "tool": d["tool"],
                "arguments": d.get("arguments", {}),
                "result": d.get("result", ""),
            })

    # 2. Load run log events (daily snapshots, agent actions, simulator events)
    snapshots_by_day = {}
    events_by_day = defaultdict(list)
    rationales_by_day = defaultdict(list)
    with open(RUN_DIR / "logs" / "run_b118ae38.jsonl") as f:
        for line in f:
            d = json.loads(line)
            day = d.get("day", 0)
            et = d.get("event_type", "")
            cat = d.get("category", "")
            if et == "state_change" and cat == "daily_snapshot":
                snapshots_by_day[day] = d.get("details", {})
            elif et == "simulator":
                events_by_day[day].append({
                    "category": cat,
                    "details": d.get("details", {}),
                })
            elif et == "agent_action" and cat == "log_rationale":
                rationales_by_day[day].append(
                    d.get("details", {}).get("arguments", {}).get("rationale", "")
                )

    # 3. Load raw responses for thinking/text content
    thinking_by_day = defaultdict(list)
    with open(RUN_DIR / "logs" / "raw_responses_b118ae38.jsonl") as f:
        for line in f:
            d = json.loads(line)
            day = d.get("day", 0)
            resp = d.get("raw_response", {})
            for block in resp.get("content", []):
                if block.get("type") == "text" and block.get("text", "").strip():
                    thinking_by_day[day].append({
                        "turn": d.get("turn"),
                        "text": block["text"],
                    })

    # 4. Get hidden stats from world.db
    hidden_stats_by_day = {}
    conn = sqlite3.connect(str(RUN_DIR / "world.db"))
    conn.row_factory = sqlite3.Row

    # Get daily financial data from ledger
    cur = conn.cursor()
    cur.execute("""
        SELECT day,
               SUM(CASE WHEN category='subscription_revenue' THEN amount ELSE 0 END) as revenue,
               SUM(CASE WHEN category='advertising' THEN amount ELSE 0 END) as ad_spend,
               SUM(CASE WHEN category='operations' THEN amount ELSE 0 END) as ops_spend,
               SUM(CASE WHEN category='development' THEN amount ELSE 0 END) as dev_spend,
               SUM(CASE WHEN category='capacity' THEN amount ELSE 0 END) as capacity_cost,
               SUM(CASE WHEN category='dividend' THEN amount ELSE 0 END) as dividends,
               SUM(CASE WHEN category IN ('vc_investment', 'vc_tranche_2') THEN amount ELSE 0 END) as vc_inflow
        FROM ledger
        GROUP BY day
        ORDER BY day
    """)
    for row in cur.fetchall():
        day = row[0]
        hidden_stats_by_day[day] = {
            "revenue": row[1],
            "ad_spend": abs(row[2]),
            "ops_spend": abs(row[3]),
            "dev_spend": abs(row[4]),
            "capacity_cost": abs(row[5]),
            "dividends": abs(row[6]),
            "vc_inflow": row[7],
        }

    # Get subscriber counts per day
    cur.execute("""
        SELECT day, total_usage_units, p95_ms, error_rate, downtime_minutes, capacity_tier
        FROM service_day ORDER BY day
    """)
    for row in cur.fetchall():
        day = row[0]
        if day in hidden_stats_by_day:
            hidden_stats_by_day[day].update({
                "total_usage": row[1],
                "p95_ms": row[2],
                "error_rate": row[3],
                "downtime_minutes": row[4],
                "capacity_tier": row[5],
            })

    # Get config history
    config_by_day = {}
    cur.execute("SELECT * FROM config_history ORDER BY day")
    cols = [desc[0] for desc in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        config_by_day[d["day"]] = d

    # Get cumulative dividends
    cur.execute("SELECT day, total_amount, founder_payout FROM dividends ORDER BY day")
    dividend_events = []
    cum_founder = 0
    for row in cur.fetchall():
        cum_founder += row[2]
        dividend_events.append({"day": row[0], "amount": row[1], "founder": row[2], "cum_founder": cum_founder})

    # Get subscription counts per day from snapshots
    sub_counts_by_day = {}
    for day, snap in snapshots_by_day.items():
        sub_counts_by_day[day] = {
            "cash": snap.get("cash", 0),
            "mrr": snap.get("mrr", 0),
            "subscribers": snap.get("subscribers", 0),
            "usage": snap.get("usage", 0),
            "overload": snap.get("overload", 0),
            "outage": snap.get("outage", False),
            "reputations": snap.get("group_reputations", {}),
            "awareness": snap.get("group_awareness", {}),
        }

    # Count simulator events per day
    sim_summary_by_day = {}
    for day, evts in events_by_day.items():
        summary = defaultdict(int)
        for e in evts:
            summary[e["category"]] += 1
        sim_summary_by_day[day] = dict(summary)

    conn.close()

    # 5. Build per-day output
    all_days = sorted(set(
        list(tool_calls_by_day.keys()) +
        list(snapshots_by_day.keys()) +
        list(hidden_stats_by_day.keys())
    ))
    # Filter to actual simulation days (1+)
    all_days = [d for d in all_days if d >= 1]

    days_data = []
    cum_div_map = {}
    for de in dividend_events:
        cum_div_map[de["day"]] = de["cum_founder"]

    running_cum_div = 0
    last_config = {}
    for day in all_days:
        # Get dashboard text from tool calls
        dashboard_text = ""
        for tc in tool_calls_by_day.get(day, []):
            if tc["tool"] == "_dashboard":
                dashboard_text = tc["result"]
                break

        # Track cumulative dividends
        if day in cum_div_map:
            running_cum_div = cum_div_map[day]

        # Update config
        if day in config_by_day:
            last_config = config_by_day[day]

        day_obj = {
            "day": day,
            "dashboard": dashboard_text,
            "snapshot": sub_counts_by_day.get(day, {}),
            "hidden_stats": hidden_stats_by_day.get(day, {}),
            "config": last_config,
            "cum_founder_dividends": running_cum_div,
            "tool_calls": tool_calls_by_day.get(day, []),
            "thinking": thinking_by_day.get(day, []),
            "rationale": rationales_by_day.get(day, []),
            "sim_events": sim_summary_by_day.get(day, {}),
            "sim_event_details": events_by_day.get(day, [])[:20],  # limit to 20 for size
        }
        days_data.append(day_obj)

    # 6. Build summary metrics for charts
    chart_data = {
        "days": [],
        "cash": [],
        "mrr": [],
        "subscribers": [],
        "cum_dividends": [],
        "daily_revenue": [],
    }
    running_div = 0
    for dd in days_data:
        chart_data["days"].append(dd["day"])
        snap = dd["snapshot"]
        chart_data["cash"].append(snap.get("cash", 0))
        chart_data["mrr"].append(snap.get("mrr", 0))
        chart_data["subscribers"].append(snap.get("subscribers", 0))
        chart_data["cum_dividends"].append(dd["cum_founder_dividends"])
        chart_data["daily_revenue"].append(dd["hidden_stats"].get("revenue", 0))

    output = {
        "run_id": "b118ae38",
        "model": "Sonnet 4.5 (Bedrock)",
        "seed": 42,
        "total_days": len(days_data),
        "chart_data": chart_data,
        "dividend_events": dividend_events,
        "days": days_data,
    }

    # Write output
    out_path = OUT_DIR / "run_data.json"
    with open(out_path, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    print(f"Wrote {out_path} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Days: {len(days_data)}, Tool calls total: {sum(len(d['tool_calls']) for d in days_data)}")

if __name__ == "__main__":
    extract()
