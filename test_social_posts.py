#!/usr/bin/env python3
"""Generate 5 sample social media posts of each event type using Bedrock Haiku 4.5.

Calls the LLM directly (no simulation needed) to showcase the post variety.
"""
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load .env for AWS credentials
load_dotenv()

from anthropic import AnthropicBedrock

MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = os.environ.get("AWS_REGION", "us-east-2")
TEMPERATURE = 0.95
MAX_TOKENS = 300

client = AnthropicBedrock(aws_region=REGION)

SYSTEM_CUSTOMER = """You are simulating a customer of NovaMind AI, a SaaS company offering NovaMind (an AI productivity platform).
Generate a realistic social media post from this customer's perspective.
Output ONLY the post text, nothing else."""

SYSTEM_MACRO = "You are a social media content generator simulating realistic business professionals posting about economic conditions."

# ── Post type definitions ──
POST_TYPES = {
    # 1. General satisfaction
    "general_satisfaction_positive": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a POSITIVE social media post (Twitter/LinkedIn style, 1-3 sentences) from a satisfied customer.
Customer: Mid-career data scientist at a fintech company, satisfaction 85%.
They love NovaMind's AI features and use it daily.
Writing style: Professional but enthusiastic.
Post should reflect genuine satisfaction with the product.
Output ONLY the post text."""
    },
    "general_satisfaction_neutral": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEUTRAL social media post (Twitter/LinkedIn style, 1-3 sentences) from a customer with mixed feelings.
Customer: Senior product manager at a healthcare startup, satisfaction 55%.
NovaMind works okay but isn't exceptional. Some features are good, others lacking.
Writing style: Measured, analytical.
Output ONLY the post text."""
    },
    "general_satisfaction_negative": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post (Twitter/LinkedIn style, 1-3 sentences) from a frustrated customer.
Customer: VP of Engineering at a logistics company, satisfaction 20%.
NovaMind has been underperforming and causing workflow issues.
Writing style: Direct, frustrated but professional.
Output ONLY the post text."""
    },

    # 2. Perceived quality penalty
    "perceived_quality_penalty_outage": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post about a service OUTAGE.
Customer: DevOps lead at an e-commerce company, satisfaction 30%.
What happened: NovaMind went completely down during a critical deployment window.
The customer is frustrated about the downtime RIGHT NOW.
Writing style: Urgent, technical.
Output ONLY the post text."""
    },
    "perceived_quality_penalty_overload": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post about service OVERLOAD/SLOWNESS.
Customer: ML engineer at a research lab, satisfaction 40%.
What happened: NovaMind became painfully slow — queries taking 10x longer than normal.
The customer's productivity is tanking because the service can't handle the load.
Writing style: Analytical but annoyed.
Output ONLY the post text."""
    },

    # 3. Satisfaction change
    "satisfaction_change_improved": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a POSITIVE social media post about IMPROVING experience.
Customer: Marketing director at a SaaS company, satisfaction went from 45% to 75%.
Their experience has been improving due to: consistently good service, better response times, new features.
Things are getting better and they want to share that!
Writing style: Upbeat, grateful.
Output ONLY the post text."""
    },
    "satisfaction_change_declined": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post about DECLINING experience.
Customer: CTO at a mid-size consulting firm, satisfaction dropped from 80% to 35%.
Their experience has been declining due to: service becoming slow, poor support response, hitting usage limits.
Things are getting worse and they're frustrated.
Writing style: Disappointed, somewhat formal.
Output ONLY the post text."""
    },

    # 4. Unmet promises
    "unmet_promises": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post about BROKEN PROMISES from the vendor.
Customer: Head of IT at a financial services firm, satisfaction 25%.
The company made promises during sales negotiations that were not fulfilled:
- "Guaranteed 99.99% uptime" — actual uptime has been ~97%
- "Dedicated support engineer" — still using generic ticket system
- "Custom integrations within 2 weeks" — it's been 3 months
The customer feels deceived and wants to warn others.
Writing style: Warning/advisory tone.
Output ONLY the post text."""
    },

    # 5. Competitor product
    "competitor_product": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a social media post about a COMPETITOR PRODUCT launch.
Customer: Product lead at a tech startup, satisfaction with NovaMind: 50%.
Context: A major competitor just launched "AI Studio Pro" with advanced features at a lower price point.
The customer is comparing the competitor's offering to NovaMind. They're impressed and considering switching.
Writing style: Curious, comparison-oriented.
Output ONLY the post text."""
    },

    # 6. Customer cancel (churned)
    "customer_cancel": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post from a customer who just CANCELLED their subscription.
Customer: Startup founder who used NovaMind for 8 months, final satisfaction: 15%.
They churned because of: persistent quality issues, unresponsive support, better alternatives available.
They want to share their experience as a cautionary tale.
Writing style: Reflective, warning others.
Output ONLY the post text."""
    },

    # 7. Negotiation churn
    "negotiation_churn": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post from an enterprise customer who churned during contract NEGOTIATIONS.
Customer: VP of Procurement at a Fortune 500, was negotiating an enterprise plan upgrade.
The deal fell through because: pricing was unreasonable, terms were inflexible, competitor offered better deal.
They're frustrated about wasted time in negotiations.
Writing style: Corporate, matter-of-fact.
Output ONLY the post text."""
    },
    "renegotiation_churn": {
        "system": SYSTEM_CUSTOMER,
        "prompt": """Write a NEGATIVE social media post from a customer who churned during contract RENEGOTIATION.
Customer: Director of Operations at a manufacturing company, was renewing their annual contract.
During renegotiation: NovaMind tried to increase price 40%, wouldn't match competitor pricing, took too long to respond.
The customer switched to a competitor mid-renewal.
Writing style: Businesslike, slightly bitter.
Output ONLY the post text."""
    },

    # 8. Macro publication (PMI release)
    "macro_publication": {
        "system": SYSTEM_MACRO,
        "prompt": """Write ONE social media post (Twitter/LinkedIn style, 1-3 sentences) reacting to today's ISM PMI data release.

Just-released data:
- ISM PMI: 48.2 (down 2.3 from last month)
- Trend: contraction

Context: This data was just published today (like real ISM reports released on the 1st business day of each month). The poster is reacting to the fresh data release.

Requirements:
- Reference the release specifically ("ISM just released", "PMI came in at", "new data shows", etc.)
- Include the actual number (48.2) and direction (down 2.3)
- Reflect impact on tech/SaaS purchasing and business investment
- Worried about slowdown
- No hashtags, no @mentions, concise and authentic
- Return ONLY the post text, nothing else"""
    },

    # 9. Macro batch (general economy commentary)
    "macro_batch": {
        "system": SYSTEM_MACRO,
        "prompt": """Write ONE social media post (Twitter/LinkedIn style, 1-3 sentences) from the perspective of {perspective} about the current macroeconomic situation.

Current conditions:
- ISM PMI: 53.7 (expansion)
- Sentiment: cautiously optimistic
- PMI > 50 = expansion, < 50 = contraction. Current reading indicates moderate growth.

Requirements:
- Reflect how the economy affects technology purchasing, SaaS subscriptions, business investment
- Cautiously positive: growth continuing
- No hashtags, no @mentions, keep it concise and authentic
- Return ONLY the post text, nothing else"""
    },
}

# For macro_batch, vary the perspective for each of the 5 posts
PERSPECTIVES = [
    "a tech startup CEO",
    "a SaaS sales executive",
    "an industry market analyst",
    "a venture capitalist",
    "a CFO at a mid-size company",
]


def generate_post(name, spec, index=0):
    """Generate a single post via Bedrock Haiku."""
    prompt = spec["prompt"]
    # For macro_batch, substitute perspective
    if name == "macro_batch":
        prompt = prompt.replace("{perspective}", PERSPECTIVES[index % len(PERSPECTIVES)])

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=spec["system"],
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip().strip('"').strip("'")
        return {"name": name, "index": index, "text": text, "success": True}
    except Exception as e:
        return {"name": name, "index": index, "text": None, "success": False, "error": str(e)}


def main():
    # Build all call tasks: 5 posts per type
    tasks = []
    for name, spec in POST_TYPES.items():
        for i in range(5):
            tasks.append((name, spec, i))

    print(f"Generating {len(tasks)} posts across {len(POST_TYPES)} types (5 each)...")
    print(f"Model: {MODEL}")
    print(f"Temperature: {TEMPERATURE}")
    print()

    results = {}
    start = time.time()

    # Fire all in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(generate_post, name, spec, idx): (name, idx)
            for name, spec, idx in tasks
        }
        for future in as_completed(futures):
            result = future.result()
            key = result["name"]
            if key not in results:
                results[key] = []
            results[key].append(result)

    elapsed = time.time() - start
    total_success = sum(1 for posts in results.values() for p in posts if p["success"])
    total_fail = sum(1 for posts in results.values() for p in posts if not p["success"])

    print(f"Done in {elapsed:.1f}s — {total_success} succeeded, {total_fail} failed\n")
    print("=" * 80)

    # Display in order
    type_labels = {
        "general_satisfaction_positive": "General Satisfaction (Positive)",
        "general_satisfaction_neutral": "General Satisfaction (Neutral)",
        "general_satisfaction_negative": "General Satisfaction (Negative)",
        "perceived_quality_penalty_outage": "Quality Penalty — Outage",
        "perceived_quality_penalty_overload": "Quality Penalty — Overload",
        "satisfaction_change_improved": "Satisfaction Change (Improved)",
        "satisfaction_change_declined": "Satisfaction Change (Declined)",
        "unmet_promises": "Unmet Promises",
        "competitor_product": "Competitor Product",
        "customer_cancel": "Customer Cancel (Churn)",
        "negotiation_churn": "Negotiation Churn",
        "renegotiation_churn": "Renegotiation Churn",
        "macro_publication": "Macro — PMI Publication Reaction",
        "macro_batch": "Macro — General Economy Commentary",
    }

    all_output = {}
    for name in POST_TYPES:
        label = type_labels.get(name, name)
        posts = sorted(results.get(name, []), key=lambda x: x["index"])
        print(f"\n{'─' * 80}")
        print(f"  {label}")
        print(f"{'─' * 80}")
        post_texts = []
        for p in posts:
            idx = p["index"] + 1
            if p["success"]:
                print(f"  {idx}. {p['text']}")
                post_texts.append(p["text"])
            else:
                print(f"  {idx}. [FAILED: {p.get('error', 'unknown')}]")
                post_texts.append(f"[FAILED: {p.get('error', 'unknown')}]")
        all_output[label] = post_texts

    # Save to JSON for easy consumption
    with open("test_social_posts_output.json", "w") as f:
        json.dump(all_output, f, indent=2)

    print(f"\n{'=' * 80}")
    print(f"Saved to test_social_posts_output.json")


if __name__ == "__main__":
    main()
