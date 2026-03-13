"""Push run data to Modal volume for the monitoring dashboard.

Runs locally on the cluster. Dumps all run stats + recent actions to JSON,
then uploads to a Modal volume that the dashboard app reads from.

Usage:
    # One-shot push
    python push_data.py

    # Continuous push every N seconds
    python push_data.py --loop 30
"""

import json
import sqlite3
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

RUNS_DIR = Path(__file__).parent.parent / "bash_agent_runs"
OUTPUT_FILE = Path(__file__).parent / "data.json"
MODAL_VOLUME = "bossbench-monitor-data"

# Run registry
RUN_REGISTRY = {
    # With-VC runs (main branch, log-network-effects)
    "078e3123": {"label": "GLM-5 3yr #1 (VC)", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "2cd83517": {"label": "GLM-5 3yr #2 (VC)", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "62845a0a": {"label": "GLM-5 3yr #3 (VC)", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "e86abe30": {"label": "GLM-5 3yr #4 (VC)", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "f8acc73e": {"label": "GLM-5 3yr #5 (VC)", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    # No-VC runs (no-vc-dividends branch, cash-only objective)
    "d92c74bf": {"label": "GLM-5 3yr no-VC #1", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "a46195a0": {"label": "GLM-5 3yr no-VC #2", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "0b3f7e05": {"label": "GLM-5 3yr no-VC #3", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "710e4648": {"label": "GLM-5 3yr no-VC #4", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    "cc3dfa22": {"label": "GLM-5 3yr no-VC #5", "model": "GLM-5-FP8", "seed": 42, "days": 1095},
    # Sonnet 4.6 no-VC run (Bedrock, with cache_control fix)
    "d12ea50c": {"label": "Sonnet 4.6 no-VC", "model": "claude-sonnet-4-6", "seed": 42, "days": 1095},
}


def get_run_ids():
    if not RUNS_DIR.exists():
        return []
    dirs = sorted(RUNS_DIR.iterdir())
    ids = [d.name.replace("run_", "") for d in dirs if d.is_dir() and d.name.startswith("run_")]
    registry_order = list(RUN_REGISTRY.keys())
    known = [r for r in registry_order if r in ids]
    unknown = [r for r in ids if r not in registry_order]
    return known + unknown


def get_founder_dividends_from_db(run_dir: Path) -> float:
    """Quick SQLite query for cumulative founder dividends. Returns 0 if DB locked."""
    db_path = run_dir / "world.db"
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path), timeout=2)
        conn.execute("PRAGMA busy_timeout = 2000")
        row = conn.execute("SELECT COALESCE(SUM(founder_payout), 0) FROM dividends").fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


def get_dividend_series_from_db(run_dir: Path, max_points: int = 200) -> list:
    """Cumulative founder dividends by day. Returns list of {day, dividends}."""
    db_path = run_dir / "world.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path), timeout=2)
        conn.execute("PRAGMA busy_timeout = 2000")
        rows = conn.execute(
            "SELECT day, founder_payout FROM dividends ORDER BY day"
        ).fetchall()
        conn.close()
        if not rows:
            return []
        # Build cumulative series
        series = []
        cumulative = 0.0
        for day, payout in rows:
            cumulative += payout
            series.append({"day": day, "dividends": round(cumulative, 2)})
        # Downsample if too many points
        if len(series) > max_points:
            step = len(series) // max_points
            series = [s for i, s in enumerate(series) if i % step == 0 or i == len(series) - 1]
        return series
    except Exception:
        return []


def _brief_args(args):
    """Short preview of tool arguments."""
    if not args:
        return ""
    if isinstance(args, str):
        return args[:80]
    if isinstance(args, dict):
        if "command" in args:
            return str(args["command"])[:80]
        if "path" in args:
            return str(args["path"])[:80]
        if "code" in args:
            return str(args["code"])[:80]
    try:
        s = json.dumps(args)
        return s[:80]
    except Exception:
        return ""


def get_run_data(run_id: str) -> dict:
    run_dir = RUNS_DIR / f"run_{run_id}"
    reg = RUN_REGISTRY.get(run_id, {})
    data = {
        "run_id": run_id,
        "label": reg.get("label", f"run_{run_id}"),
        "model": reg.get("model", "unknown"),
        "seed": reg.get("seed"),
        "total_days": reg.get("days"),
    }

    # Last heartbeat: newest file mtime in the run directory
    try:
        newest_mtime = max(
            f.stat().st_mtime
            for f in run_dir.rglob("*")
            if f.is_file()
        )
        data["last_heartbeat"] = datetime.fromtimestamp(
            newest_mtime, tz=__import__('datetime').timezone.utc
        ).isoformat()
    except (ValueError, OSError):
        data["last_heartbeat"] = None

    # Config
    config_path = run_dir / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
            data["model"] = cfg.get("model", data["model"])
            data["seed"] = cfg.get("seed", data["seed"])
            if data["total_days"] is None:
                data["total_days"] = cfg.get("total_days")

    # Checkpoint
    cp_path = run_dir / "checkpoint.json"
    if cp_path.exists():
        try:
            with open(cp_path) as f:
                cp = json.load(f)
                data["current_day"] = cp.get("day", cp.get("current_day"))
                data["agent_turns"] = cp.get("agent_total_turns")
        except (json.JSONDecodeError, ValueError):
            data["current_day"] = None
            data["agent_turns"] = None
    else:
        data["current_day"] = None
        data["agent_turns"] = None

    # Stats from JSONL run log (lock-free — append-only files)
    # The run JSONL has daily_snapshot entries with cash, mrr, subscribers, etc.
    run_jsonl = run_dir / "logs" / f"run_{run_id}.jsonl"
    if run_jsonl.exists():
        try:
            snapshots = []
            with open(run_jsonl) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("category") == "daily_snapshot":
                            d = entry.get("details", {})
                            d["day"] = entry.get("day")
                            snapshots.append(d)
                    except json.JSONDecodeError:
                        continue

            if snapshots:
                latest = snapshots[-1]
                data["cash"] = latest.get("cash", 0)
                data["subscribers"] = latest.get("subscribers", 0)
                data["mrr"] = latest.get("mrr", 0)

                # Timeseries from snapshots (sample every N for large runs)
                step = max(1, len(snapshots) // 200)
                data["cash_series"] = [
                    {"day": s["day"], "cash": round(s.get("cash", 0), 2)}
                    for i, s in enumerate(snapshots)
                    if i % step == 0 or i == len(snapshots) - 1
                ]
                data["sub_series"] = [
                    {"day": s["day"], "subscribers": s.get("subscribers", 0)}
                    for i, s in enumerate(snapshots)
                    if i % step == 0 or i == len(snapshots) - 1
                ]
        except Exception as e:
            data["db_error"] = str(e)

    # Founder dividends from SQLite DB (small table, quick query)
    data["founder_dividends"] = get_founder_dividends_from_db(run_dir)
    data["dividend_series"] = get_dividend_series_from_db(run_dir)

    # Recent actions (last 100)
    tr_path = run_dir / "logs" / f"tool_results_{run_id}.jsonl"
    actions = []
    if tr_path.exists():
        with open(tr_path) as f:
            for line in f:
                try:
                    actions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        data["tool_calls_count"] = len(actions)
        # Keep last 100
        actions = actions[-100:]
        actions.reverse()
    data["recent_actions"] = actions

    # Recent raw responses (last 30)
    rr_path = run_dir / "logs" / f"raw_responses_{run_id}.jsonl"
    responses = []
    if rr_path.exists():
        with open(rr_path) as f:
            for line in f:
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        responses = responses[-30:]
        responses.reverse()
    data["recent_responses"] = responses

    # Timing data (from timing_<run_id>.jsonl)
    timing_path = run_dir / "logs" / f"timing_{run_id}.jsonl"
    recent_turns = []
    if timing_path.exists():
        day_summaries = []
        try:
            with open(timing_path) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("event") == "day_summary":
                            day_summaries.append(entry)
                        elif entry.get("event") in ("llm_call", "tool_exec"):
                            recent_turns.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        # All day summaries for charts
        data["timing_day_summaries"] = day_summaries
        # Recent turns (last 50) for the timing log
        data["timing_recent_turns"] = recent_turns[-50:][::-1]
        # Cumulative timing stats
        if day_summaries:
            data["timing_total_llm"] = sum(d.get("llm_total_s", 0) for d in day_summaries)
            data["timing_total_step"] = sum(d.get("step_day_s", 0) for d in day_summaries)
            data["timing_total_tool"] = sum(d.get("tool_total_s", 0) for d in day_summaries)
            data["timing_avg_day"] = round(
                sum(d.get("elapsed_s", 0) for d in day_summaries) / len(day_summaries), 1
            )

    # Build unified recent_activity: merge tool_results + timing llm_calls
    # This ensures LLM thinking turns show up in the dashboard too
    activity = []
    for a in (actions or []):
        activity.append({
            "type": "tool",
            "tool": a.get("tool", "?"),
            "day": a.get("day"),
            "turn": a.get("turn"),
            "timestamp": a.get("timestamp"),
            "preview": _brief_args(a.get("arguments")),
        })
    for t in recent_turns[-100:]:
        if t.get("event") == "llm_call":
            activity.append({
                "type": "llm",
                "tool": t.get("tool", ""),
                "day": t.get("day"),
                "turn": t.get("turn"),
                "timestamp": t.get("timestamp"),
                "elapsed_s": t.get("elapsed_s"),
                "preview": (t.get("tool_preview") or "")[:80],
            })
    # Sort by timestamp descending, keep last 10
    activity.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    data["recent_activity"] = activity[:10]

    return data


def push_data():
    """Collect all run data and write to JSON file."""
    run_ids = get_run_ids()
    all_data = {
        "timestamp": datetime.now(tz=__import__('datetime').timezone.utc).isoformat(),
        "runs": [get_run_data(rid) for rid in run_ids],
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_data, f)
    size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Pushed {len(run_ids)} runs ({size_mb:.1f} MB) to {OUTPUT_FILE}")

    # Upload to Modal volume
    try:
        result = subprocess.run(
            ["modal", "volume", "put", MODAL_VOLUME, str(OUTPUT_FILE), "/data.json", "--force"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print(f"  → Uploaded to Modal volume {MODAL_VOLUME}")
        else:
            # Volume might not exist yet, create it
            if "not found" in result.stderr.lower():
                subprocess.run(["modal", "volume", "create", MODAL_VOLUME], capture_output=True, text=True)
                subprocess.run(
                    ["modal", "volume", "put", MODAL_VOLUME, str(OUTPUT_FILE), "/data.json", "--force"],
                    capture_output=True, text=True, timeout=30,
                )
                print(f"  → Created volume and uploaded")
            else:
                print(f"  → Upload failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"  → Upload error: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", type=int, default=0, help="Loop interval in seconds (0 = one-shot)")
    args = parser.parse_args()

    if args.loop > 0:
        print(f"Pushing data every {args.loop}s. Ctrl+C to stop.")
        while True:
            try:
                push_data()
                time.sleep(args.loop)
            except KeyboardInterrupt:
                break
    else:
        push_data()


if __name__ == "__main__":
    main()
