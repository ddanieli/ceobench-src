"""Test judge + reply with actual Bedrock Haiku — same code path as simulation."""
import sys
sys.path.insert(0, 'src')

from concurrent.futures import ThreadPoolExecutor, as_completed
from saas_bench.config import BenchmarkConfig
from saas_bench.customer_llm import judge_agent_social_post, generate_customer_reply_to_agent, _create_bedrock_client
from saas_bench.personas import GROUP_CHARACTERISTICS

config = BenchmarkConfig()
client = _create_bedrock_client(config)

# Test posts
posts = [
    {"content": "We just cut P99 latency from 340ms to 89ms. Chunked prefill is live. 🔥", "reply_to": None},
    {"content": "our intern wrote better code than GPT-5 lmaooo we're so cooked 💀", "reply_to": None},
    {"content": "NovaMind is SOC2 Type II certified, HIPAA compliant, with full VPC isolation.", "reply_to": None},
    {"content": "Found it — memory leak in our inference router. Pushed a fix 2 hours ago. Can you DM me your account ID? I'll personally debug the remaining 500s.", "reply_to": "This API is garbage, getting 500 errors every day this week"},
]

groups = ['S1', 'S3', 'E2']
total_subs = 5000
mrr = 150000
recent_posts = []

for post in posts:
    content = post["content"]
    reply_to = post["reply_to"]
    print(f"\n{'='*80}")
    print(f"POST: \"{content}\"")
    if reply_to:
        print(f"REPLY TO: \"{reply_to}\"")
    print(f"{'='*80}")

    # Judge all groups in parallel (same as simulation)
    effect_by_group = {}
    judge_futures = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        for gid in groups:
            chars = GROUP_CHARACTERISTICS[gid]
            future = executor.submit(
                judge_agent_social_post,
                client, config, content,
                gid, chars['description'], chars['social_media_tone'],
                total_subs, mrr, recent_posts, reply_to
            )
            judge_futures[future] = gid

        for future in as_completed(judge_futures):
            gid = judge_futures[future]
            try:
                effect, reasoning, in_tok, out_tok = future.result()
                effect_by_group[gid] = effect
                print(f"\n  {gid}: SCORE={effect:+.2f}  ({in_tok}+{out_tok} tokens)")
                print(f"       Raw: {reasoning}")
            except Exception as e:
                print(f"\n  {gid}: ERROR: {e}")
                effect_by_group[gid] = 0.0

    # Generate replies for viral groups (|score| >= 0.6) — all in parallel
    viral_threshold = 0.6
    viral_groups = [g for g in groups if abs(effect_by_group.get(g, 0)) >= viral_threshold]

    if viral_groups:
        print(f"\n  VIRAL GROUPS: {viral_groups}")
        reply_futures = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            for gid in viral_groups:
                chars = GROUP_CHARACTERISTICS[gid]
                eff = effect_by_group[gid]
                future = executor.submit(
                    generate_customer_reply_to_agent,
                    client, config, content,
                    gid, chars['description'], chars['social_media_tone'],
                    eff, reply_to
                )
                reply_futures[future] = gid

            for future in as_completed(reply_futures):
                gid = reply_futures[future]
                try:
                    reply_text, in_tok, out_tok = future.result()
                    print(f"  REPLY from {gid}: \"{reply_text}\"  ({in_tok}+{out_tok} tokens)")
                except Exception as e:
                    print(f"  REPLY from {gid}: ERROR: {e}")
    else:
        print(f"\n  No viral groups (all |scores| < {viral_threshold})")

print("\n\nDone!")
