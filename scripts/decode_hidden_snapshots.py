#!/usr/bin/env python3
"""Decode hidden snapshot tables from a SaaSBench run.

Usage:
    python decode_hidden_snapshots.py <path_to_world.db> [--csv] [--day START:END]

Examples:
    python decode_hidden_snapshots.py bash_agent_runs/run_abc123/world.db
    python decode_hidden_snapshots.py bash_agent_runs/run_abc123/world.db --csv
    python decode_hidden_snapshots.py bash_agent_runs/run_abc123/world.db --day 100:200
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Decode hidden snapshot tables from SaaSBench run")
    parser.add_argument("db_path", help="Path to world.db")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    parser.add_argument("--day", type=str, default=None, help="Day range START:END (inclusive)")
    parser.add_argument("--table", choices=["params", "quality", "both"], default="both",
                        help="Which table to dump (default: both)")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"Error: {db_path} not found", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Check if tables exist
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '_hidden_%'"
    ).fetchall()]

    if not tables:
        print("No hidden snapshot tables found in this database.", file=sys.stderr)
        print("This run may have been started before the snapshot feature was added.", file=sys.stderr)
        sys.exit(1)

    day_filter = ""
    day_params = ()
    if args.day:
        parts = args.day.split(":")
        if len(parts) == 2:
            start, end = int(parts[0]), int(parts[1])
            day_filter = " WHERE day >= ? AND day <= ?"
            day_params = (start, end)
        else:
            day_filter = " WHERE day = ?"
            day_params = (int(parts[0]),)

    if args.table in ("params", "both") and "_hidden_group_params_history" in tables:
        rows = conn.execute(
            f"SELECT * FROM _hidden_group_params_history{day_filter} ORDER BY day, group_id",
            day_params
        ).fetchall()
        if args.csv:
            cols = rows[0].keys() if rows else []
            print(",".join(cols))
            for r in rows:
                print(",".join(str(r[c]) for c in cols))
        else:
            print(f"\n{'='*80}")
            print(f"GROUP PARAMETERS HISTORY ({len(rows)} rows)")
            print(f"{'='*80}")
            print(f"{'Day':>5} {'Group':>6} {'c_max_mean':>11} {'q_min_mean':>11} {'q_max_mean':>11} {'steep_L':>8} {'repute':>8} {'aware':>8}")
            print("-" * 80)
            for r in rows:
                print(f"{r['day']:>5} {r['group_id']:>6} {r['current_c_max_mean']:>11.4f} "
                      f"{r['current_q_min_mean']:>11.4f} {r['current_q_max_mean']:>11.4f} "
                      f"{r['current_steepness_left_factor']:>8.4f} {r['reputation']:>8.4f} {r['awareness']:>8.4f}")

        if not args.csv:
            print()

    if args.table in ("quality", "both") and "_hidden_quality_snapshot" in tables:
        rows = conn.execute(
            f"SELECT * FROM _hidden_quality_snapshot{day_filter} ORDER BY day, group_id, plan",
            day_params
        ).fetchall()
        if args.csv:
            cols = rows[0].keys() if rows else []
            print(",".join(cols))
            for r in rows:
                print(",".join(str(r[c]) for c in cols))
        else:
            print(f"\n{'='*80}")
            print(f"QUALITY SNAPSHOT ({len(rows)} rows)")
            print(f"{'='*80}")
            print(f"{'Day':>5} {'Group':>6} {'Plan':>5} {'base_pq':>8} {'q_shared':>8} {'q_group':>8} "
                  f"{'Tier':>5} {'TierMul':>8} {'Delivered':>10}")
            print("-" * 80)
            for r in rows:
                print(f"{r['day']:>5} {r['group_id']:>6} {r['plan']:>5} {r['base_product_quality']:>8.4f} "
                      f"{r['q_shared_bonus']:>8.4f} {r['q_group_bonus']:>8.4f} "
                      f"{r['tier']:>5} {r['tier_multiplier']:>8.4f} {r['delivered_quality']:>10.4f}")

    conn.close()


if __name__ == "__main__":
    main()
