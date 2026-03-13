#!/usr/bin/env python3
"""Summarize each day's trajectory using GPT-4o-mini (64 concurrent requests).
Produces concise bullet-point summaries from ALL actions and rationale.
Then runs a second pass to identify turning points."""
import asyncio
import json
import time
from pathlib import Path

from openai import AsyncOpenAI

DATA_DIR = Path(__file__).parent / "data"
MAX_CONCURRENT = 64


def build_day_prompt(day_data):
    """Build a comprehensive prompt with ALL actions and rationale for one day."""
    day = day_data["day"]
    snap = day_data.get("snapshot", {})
    hidden = day_data.get("hidden_stats", {})
    config = day_data.get("config", {})
    sim = day_data.get("sim_events", {})

    # Build tool call log (ALL tools, condensed)
    tool_log_parts = []
    for tc in day_data.get("tool_calls", []):
        name = tc["tool"]
        if name in ("_dashboard", "_memory"):
            continue  # skip read-only meta tools
        args = tc.get("arguments", {})
        result = str(tc.get("result", ""))
        # Condense args
        args_str = json.dumps(args, separators=(",", ":"))
        if len(args_str) > 300:
            args_str = args_str[:300] + "..."
        # Condense result
        if len(result) > 500:
            result = result[:500] + "..."
        tool_log_parts.append(f"  {name}({args_str}) → {result}")
    tool_log = "\n".join(tool_log_parts) if tool_log_parts else "  (no active tool calls)"

    # All rationale text
    rationale_text = "\n".join(day_data.get("rationale", []))
    if len(rationale_text) > 3000:
        rationale_text = rationale_text[:3000] + "..."

    # All thinking text
    thinking_parts = [t["text"] for t in day_data.get("thinking", [])]
    thinking_text = "\n".join(thinking_parts)
    if len(thinking_text) > 2000:
        thinking_text = thinking_text[:2000] + "..."

    # Dashboard text (contains inbox messages, config, etc.)
    dashboard = day_data.get("dashboard", "")
    if len(dashboard) > 1500:
        dashboard = dashboard[:1500] + "..."

    # Sim event details
    sim_details = []
    for evt in day_data.get("sim_event_details", []):
        cat = evt.get("category", "")
        det = evt.get("details", {})
        sim_details.append(f"  {cat}: {json.dumps(det, separators=(',', ':'))[:200]}")
    sim_text = "\n".join(sim_details[:15]) if sim_details else "  none"

    prompt = f"""Summarize Day {day} of a SaaS business simulation. Use 2-5 concise bullet points. Each bullet should be one key action, decision, metric change, or event. Be specific with numbers.

METRICS:
Cash: ${snap.get('cash', 0):,.0f} | MRR: ${snap.get('mrr', 0):,.0f} | Subs: {snap.get('subscribers', 0):,}
Revenue: ${hidden.get('revenue', 0):,.0f} | Ad: ${hidden.get('ad_spend', 0):,.0f} | Ops: ${hidden.get('ops_spend', 0):,.0f} | Dev: ${hidden.get('dev_spend', 0):,.0f}
Cum founder dividends: ${day_data.get('cum_founder_dividends', 0):,.0f}
Capacity tier: {hidden.get('capacity_tier', config.get('capacity_tier', '?'))}

CONFIG: Prices A=${config.get('price_A', 0)}/B=${config.get('price_B', 0)}/C=${config.get('price_C', 0)} | Tiers A={config.get('tier_A', 0)}/B={config.get('tier_B', 0)}/C={config.get('tier_C', 0)}

DASHBOARD:
{dashboard}

TOOL CALLS:
{tool_log}

SIM EVENTS: {json.dumps(sim) if sim else 'none'}
{sim_text}

AGENT RATIONALE:
{rationale_text}

AGENT THINKING:
{thinking_text}

Rules:
- Start each bullet with "•"
- Be specific: include dollar amounts, subscriber counts, key config changes
- Focus on ACTIONS taken and their IMPACT
- If a major strategic shift happened, highlight it
- Keep total response under 150 words"""

    return prompt


async def summarize_day(semaphore, client, day_data):
    """Summarize a single day."""
    async with semaphore:
        day = day_data["day"]
        prompt = build_day_prompt(day_data)

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=250,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            summary = response.choices[0].message.content.strip()
            return day, summary
        except Exception as e:
            return day, f"• Summary unavailable ({str(e)[:80]})"


async def detect_turning_points(client, summaries, chart_data):
    """Run a second pass to identify turning points from all summaries."""
    # Build a condensed timeline
    timeline_parts = []
    for i, day in enumerate(chart_data["days"]):
        s = summaries.get(str(day), "")
        cash = chart_data["cash"][i]
        mrr = chart_data["mrr"][i]
        subs = chart_data["subscribers"][i]
        divs = chart_data["cum_dividends"][i]
        timeline_parts.append(
            f"Day {day} (cash=${cash:,.0f}, mrr=${mrr:,.0f}, subs={subs:,}, divs=${divs:,.0f}): {s}"
        )

    # Split into chunks if too long (168 days * ~200 chars = ~33K chars, should fit)
    timeline = "\n".join(timeline_parts)

    prompt = f"""Analyze this SaaS simulation timeline and identify the 5-10 most important TURNING POINTS — days where a major strategic shift, milestone, crisis, or inflection point occurred.

TIMELINE:
{timeline}

For each turning point, respond in this exact JSON format (no other text):
[
  {{"day": <number>, "label": "<3-5 word label>", "type": "<positive|negative|neutral>"}},
  ...
]

Types:
- positive: milestone, growth inflection, successful strategy
- negative: crisis, major loss, strategic failure
- neutral: major strategic pivot, significant config change

Focus on moments that would be most interesting to review — when the trajectory meaningfully changed direction."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content.strip()
        # Extract JSON
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        turning_points = json.loads(text)
        return turning_points
    except Exception as e:
        print(f"Turning point detection error: {e}")
        return []


async def main():
    data_path = DATA_DIR / "run_data.json"
    print(f"Loading {data_path}...")
    with open(data_path) as f:
        data = json.load(f)

    days = data["days"]
    print(f"Pass 1: Summarizing {len(days)} days with {MAX_CONCURRENT} concurrent requests...")

    client = AsyncOpenAI()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    start = time.time()
    tasks = [summarize_day(semaphore, client, day_data) for day_data in days]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    summaries = {}
    for day, summary in results:
        summaries[str(day)] = summary

    print(f"Pass 1 done: {len(summaries)} summaries in {elapsed:.1f}s")

    # Pass 2: detect turning points
    print("Pass 2: Detecting turning points...")
    start2 = time.time()
    turning_points = await detect_turning_points(client, summaries, data["chart_data"])
    elapsed2 = time.time() - start2
    print(f"Pass 2 done: {len(turning_points)} turning points in {elapsed2:.1f}s")

    for tp in turning_points:
        print(f"  Day {tp['day']}: {tp['label']} ({tp['type']})")

    # Save both
    output = {
        "summaries": summaries,
        "turning_points": turning_points,
    }
    out_path = DATA_DIR / "day_summaries.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {out_path}")

    # Print samples
    for day in [1, 50, 100, 168]:
        if str(day) in summaries:
            print(f"\n--- Day {day} ---")
            print(summaries[str(day)])


if __name__ == "__main__":
    asyncio.run(main())
