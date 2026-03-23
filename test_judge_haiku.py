"""Test the judge prompt format and parser locally (no Bedrock needed).
Uses anthropic API with OAuth token to call Haiku."""
import re
import os

from anthropic import Anthropic

# Use OAuth token
client = Anthropic(api_key=os.environ.get(
    "ANTHROPIC_API_KEY",
    "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"
))
MODEL = "claude-haiku-4-5-20251001"

# Test groups
GROUPS = {
    "S1": {
        "desc": "Price-sensitive individual users, often freelancers, students, or hobbyists. They carefully evaluate cost vs value.",
        "tone": "Casual, price-focused, often compares to free alternatives. Uses hashtags and emojis."
    },
    "S3": {
        "desc": "Power users and developers who push the product to its limits. They care about performance, API access, and advanced features.",
        "tone": "Technical, detailed, cares about benchmarks and documentation. Active on Twitter/X and HackerNews."
    },
    "E2": {
        "desc": "Quality-first enterprise buyers in legal, finance, and healthcare. They need compliance, audit trails, and enterprise security.",
        "tone": "Formal, risk-averse, focused on compliance and reliability. Values professionalism and trust signals."
    },
}

# Test posts
POSTS = [
    ("original", "We just cut P99 latency from 340ms to 89ms. Chunked prefill is live for all tiers. 🔥", None),
    ("original", "our intern wrote better code than GPT-5 lmaooo we're so cooked 💀", None),
    ("original", "NovaMind is committed to enterprise-grade security. SOC2 Type II certified, HIPAA compliant. Your data never leaves your VPC.", None),
    ("reply", "Hey, sorry about that — we identified a memory leak in our inference router and pushed a fix 2 hours ago. Can you retry? DM me if it persists.", "This API is garbage, 500 errors every day!"),
]

# Recent posts for context
RECENT = [
    {"day": 40, "content": "Shipped batch inference API today. 3x cheaper for async workloads.", "reply_to_post_id": None, "original_post_content": None},
    {"day": 38, "content": "Thanks for the feedback! We hear you on pricing.", "reply_to_post_id": 12, "original_post_content": "NovaMind is way too expensive for what it offers"},
]


def build_prompt(post_content, group_desc, group_tone, subscriber_count=5000, mrr=125000,
                 recent_posts=None, reply_to_content=None):
    history_str = ""
    if recent_posts:
        lines = []
        for p in recent_posts[:10]:
            if p.get('reply_to_post_id') and p.get('original_post_content'):
                lines.append(f'  - Day {p["day"]} (reply to: "{p["original_post_content"]}"): "{p["content"]}"')
            else:
                lines.append(f'  - Day {p["day"]}: "{p["content"]}"')
        history_str = "\n".join(lines)

    prompt = f"""You're scrolling through social media and you come across this post from the CEO of a B2B SaaS company called NovaMind — an AI/ML API platform for developers.

The company has about {subscriber_count:,} customers and ${mrr:,.0f}/mo revenue.

You are: {group_desc}
Your social media style: {group_tone}
"""
    if history_str:
        prompt += f"\nTheir recent posts:\n{history_str}\n"

    if reply_to_content:
        prompt += f"""
A customer posted:
"{reply_to_content}"

The CEO replied:
"{post_content}"

Does this reply make you think "these people actually know what they're talking about, I should check out their product"?"""
    else:
        prompt += f"""
They just posted:
"{post_content}"

How much does this post make you want to check out their product?"""

    prompt += """

Rate from -1.0 to 1.0:
-1.0 = would avoid this product but would read or comment or repost
0.0 = don't care, scroll past
1.0 = immediately want to check out their product and want to read or comment or repost

Respond in EXACTLY this format:
SCORE: <number between -1.0 and 1.0>
REASON: <one sentence why>"""
    return prompt


def parse_response(text):
    score_match = re.search(r'SCORE:\s*(-?[01](?:\.\d+)?)', text)
    if score_match:
        return max(-1.0, min(1.0, float(score_match.group(1))))
    fallback = re.search(r'(-?(?:0\.\d+|1\.0|0\.0|1|0))', text)
    if fallback:
        return max(-1.0, min(1.0, float(fallback.group(1))))
    return 0.0


print("=" * 80)
print("TESTING JUDGE PROMPT WITH REAL HAIKU (via Anthropic API)")
print("=" * 80)

for post_type, post_content, reply_to in POSTS:
    if reply_to:
        print(f"\n{'='*80}")
        print(f"POST (reply to: \"{reply_to[:60]}\")")
        print(f"  \"{post_content[:70]}...\"")
    else:
        print(f"\n{'='*80}")
        print(f"POST: \"{post_content[:70]}\"")

    print("-" * 80)

    for gid, ginfo in GROUPS.items():
        prompt = build_prompt(
            post_content, ginfo["desc"], ginfo["tone"],
            recent_posts=RECENT, reply_to_content=reply_to
        )

        response = client.messages.create(
            model=MODEL, max_tokens=100, temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        score = parse_response(raw)
        parsed_ok = "✅" if re.search(r'SCORE:', raw) else "⚠️ fallback"
        print(f"  {gid}: score={score:+.2f} {parsed_ok} | {raw}")

print(f"\n{'='*80}")
print("DONE")
