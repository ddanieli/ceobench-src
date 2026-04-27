"""Autoplay loop — run a simple strategy for N days automatically.

Run with:
    ./novamind-operation python examples/autoplay_loop.py

This demonstrates how to combine strategy + next-week advancement in a single script.
"""
import json
import os
import subprocess
import sys
import novamind_api as nm

DAYS_TO_PLAY = 10

print(f"🎮 Autoplay: Running {DAYS_TO_PLAY} days with basic strategy\n")

for i in range(DAYS_TO_PLAY):
    day = nm.vars.current_day

    # --- Strategy decisions ---
    nm.pricing.set_prices(A=19, B=59, C=149)
    nm.marketing.set_daily_spend(operations=2000, development=2000)
    # Ad spend is per (channel, group) — split a $3000/day budget across channels and groups
    nm.marketing.set_targeted_ad_spend(targeted_spend={
        "social_media":      {"S1": 600, "S2": 400, "S3": 200},
        "search_ads":        {"S1": 400, "S2": 300, "S3": 100},
        "linkedin":          {"E1": 400, "E2": 300, "E3": 100},
        "content_marketing": {"S1": 50,  "S2": 50,  "S3": 50},
        "referral_program":  {"S1": 50,  "S2": 50,  "S3": 0},
    })
    nm.analytics.log_rationale(f"Day {day}: Autoplay basic strategy")

    # --- Advance the week ---
    # Call next-week via the API directly
    result = nm._client.next_week()

    if result.get("success"):
        new_day = result.get("day", "?")
        dashboard = result.get("dashboard", "")
        # Print just the key metrics from dashboard (first few lines)
        lines = dashboard.split("\n")
        for line in lines[:8]:
            print(line)
        print(f"  ... (day {new_day} complete)\n")
    else:
        print(f"❌ Error: {result.get('error')}")
        break

# Final status
result = nm.query("SELECT SUM(amount) as cash FROM ledger")
cash = result['rows'][0]['cash'] if result['rows'] and result['rows'][0]['cash'] else 0
print(f"\n🏁 Final cash after {DAYS_TO_PLAY} days: ${cash:,.0f}")
