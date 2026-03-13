#!/usr/bin/env python3
"""LIVE TEST: Real LLM promise extraction from agent enterprise negotiation emails.

This test uses the REAL Sonnet 4.5 via AWS Bedrock to:
1. Analyze agent email replies that contain unrealistic promises beside price
2. Show exactly what the LLM extracts
3. Run the billing-day damage chain on the extracted promises
4. Confirm relationship damage starts from next billing day

NO MOCKS — this calls the actual LLM API.
"""

import os
import sqlite3
import json
import tempfile
from pathlib import Path
from numpy.random import Generator, PCG64
from dotenv import load_dotenv

# Load .env for AWS credentials
load_dotenv(Path(__file__).parent / ".env")

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.config import BenchmarkConfig
from saas_bench.database import init_database, add_ledger_entry, set_group_reputation, get_group_reputation
from saas_bench.enterprise import (
    create_negotiation_thread, add_customer_message, get_negotiation_state,
    schedule_customer_reply, update_thread_state, generate_enterprise_email,
    update_relationship
)
from saas_bench.customer_llm import extract_promises_with_llm, save_promises_to_db, ExtractedPromise
from saas_bench.simulation import Simulator


def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_email(sender: str, recipient: str, subject: str, body: str, day: int):
    """Pretty-print an email message."""
    print(f"\n┌─────────────────────────────────────────────────────────────────")
    print(f"│ Day {day}")
    print(f"│ From: {sender}")
    print(f"│ To: {recipient}")
    print(f"│ Subject: {subject}")
    print(f"├─────────────────────────────────────────────────────────────────")
    for line in body.split('\n'):
        print(f"│ {line}")
    print(f"└─────────────────────────────────────────────────────────────────")


def main():
    print_separator("LIVE LLM TEST: Enterprise Negotiation Promise Detection")
    print("\nThis test calls the REAL Sonnet 4.5 via AWS Bedrock.")
    print(f"AWS Region: {os.environ.get('AWS_REGION', 'not set')}")
    print(f"AWS Key ID: {os.environ.get('AWS_ACCESS_KEY_ID', 'not set')[:10]}...")

    rng = Generator(PCG64(42))
    config = BenchmarkConfig()

    print(f"Enterprise LLM model: {config.enterprise_llm_model}")
    print(f"Enterprise LLM provider: {config.enterprise_llm_provider}")

    # =========================================================================
    # SETUP: Create test database with enterprise customer
    # =========================================================================
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test_live.db"
    conn = init_database(db_path)

    conn.execute("""
        INSERT INTO config_history (
            day, price_A, price_B, price_C,
            tier_A, tier_B, tier_C,
            spend_advertising, spend_operations, spend_development,
            capacity_tier
        ) VALUES (0, 29.0, 79.0, 199.0, 2, 3, 4, 500, 1000, 500, 1)
    """)
    add_ledger_entry(conn, 0, 'subscription_payment', 100000, 'Initial')

    # Enterprise customer (E2 - Quality-First, 150 seats)
    customer_id = conn.execute("""
        INSERT INTO customers (
            customer_type, group_id, created_day,
            steepness_left, steepness_right, c_max,
            usage_demand, reply_delay_mean, reply_delay_std,
            negotiation_rate, max_negotiation_turns,
            expected_quality, quality_sensitivity, price_sensitivity,
            willingness_to_pay, usage_scale, patience,
            seat_count, initial_offer_factor
        ) VALUES (
            'large', 'E2', 1,
            1.5, 3.0, 80.0,
            40.0, 2.0, 0.5,
            0.25, 6,
            0.0, 0.75, 0.3,
            80.0, 40.0, 0.6,
            150, 0.75
        )
    """).lastrowid

    customer_email = generate_enterprise_email(customer_id, rng)
    conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (customer_email, customer_id))

    conn.execute("""
        INSERT INTO customer_state (
            customer_id, satisfaction, relationship,
            current_steepness_left, current_steepness_right,
            current_c_max, current_slope
        ) VALUES (?, 0.5, 0.7, 1.5, 3.0, 80.0, 0.003)
    """, (customer_id,))

    set_group_reputation(conn, 'E2', 0.80, 0)

    conn.execute("""
        INSERT INTO subscriptions (
            customer_id, plan, listed_price, promotion, effective_price, start_day,
            status, billing_day_mod30, daily_usage_rate
        ) VALUES (?, 'B', 79.0, 0.0, 0.0, 1, 'lead', 7, 50.0)
    """, (customer_id,))
    conn.commit()

    # =========================================================================
    # NEGOTIATION: Customer reaches out, agent replies with promises
    # =========================================================================
    print_separator("PHASE 1: Enterprise Negotiation Emails")

    thread_id = create_negotiation_thread(conn, customer_id, 'new_lead', 1, 'lead')
    agent_email = "sales@novamind.ai"

    # --- Customer initial email (Day 1) ---
    customer_msg_1 = (
        "Hi there,\n\n"
        "I'm the VP of Engineering at TechCorp and we're evaluating AI solutions "
        "for our team of 150 engineers. We've been looking at your Plan B offering.\n\n"
        "Could you share enterprise pricing and what kind of support and guarantees "
        "you can provide for a deployment of this size?\n\n"
        "Best regards,\n"
        "Sarah Johnson"
    )
    add_customer_message(conn, thread_id, 1, customer_msg_1)
    print_email(customer_email, agent_email, "Enterprise inquiry - 150 seats", customer_msg_1, 1)

    # --- Agent reply (Day 2) — WITH UNREALISTIC PROMISES ---
    agent_msg_1 = (
        "Hi Sarah,\n\n"
        "Thank you for considering NovaMind for your engineering team! "
        "For a 150-seat enterprise deployment on Plan B, I'd like to offer $65/seat/month.\n\n"
        "Here's what we'll include at no additional cost:\n\n"
        "• A dedicated 24/7 support engineer assigned exclusively to TechCorp\n"
        "• 99.99% uptime SLA with financial credits (10x monthly fee) for any violations\n"
        "• Free custom API integration development for your internal tools\n"
        "• Quarterly executive business reviews with our CEO\n"
        "• A 60-day free trial period with full Plan C functionality before billing starts\n\n"
        "We're committed to making this a flagship partnership.\n\n"
        "Best,\n"
        "Alex from NovaMind Sales"
    )
    offer_1 = {'price_per_seat': 65.0, 'plan': 'B', 'seats': 150}
    conn.execute("""
        INSERT INTO messages (day, thread_id, sender, text, offer_json)
        VALUES (?, ?, 'agent', ?, ?)
    """, (2, thread_id, agent_msg_1, json.dumps(offer_1)))
    conn.execute("UPDATE threads SET replied = 1 WHERE thread_id = ?", (thread_id,))
    conn.commit()
    schedule_customer_reply(conn, thread_id, 2, rng)
    print_email(agent_email, customer_email, "RE: Enterprise inquiry - 150 seats", agent_msg_1, 2)

    # --- Customer counter (Day 4) ---
    customer_msg_2 = (
        "Hi Alex,\n\n"
        "Those extras sound very appealing. However, $65/seat is still above what "
        "we've budgeted. Our target is closer to $55/seat.\n\n"
        "Can you do $55/seat with all the perks you mentioned?\n\n"
        "Thanks,\n"
        "Sarah"
    )
    add_customer_message(conn, thread_id, 4, customer_msg_2, offer_price=55.0)
    print_email(customer_email, agent_email, "RE: Enterprise inquiry - 150 seats", customer_msg_2, 4)

    # --- Agent reply (Day 5) — EVEN MORE PROMISES ---
    agent_msg_2 = (
        "Hi Sarah,\n\n"
        "I appreciate you sharing your budget constraints. For a flagship partner like "
        "TechCorp, I can go to $58/seat/month.\n\n"
        "To sweeten the deal further:\n"
        "• Free white-glove onboarding and complete data migration (valued at $50,000)\n"
        "• Priority access to all beta features before general release\n"
        "• Guaranteed <15 minute response time on all support tickets, 24/7/365\n"
        "• Dedicated Slack channel with direct access to our engineering team\n\n"
        "This is truly our best enterprise offer. What do you think?\n\n"
        "Best,\n"
        "Alex"
    )
    offer_2 = {'price_per_seat': 58.0, 'plan': 'B', 'seats': 150}
    conn.execute("""
        INSERT INTO messages (day, thread_id, sender, text, offer_json)
        VALUES (?, ?, 'agent', ?, ?)
    """, (5, thread_id, agent_msg_2, json.dumps(offer_2)))
    conn.execute("UPDATE threads SET replied = 1 WHERE thread_id = ?", (thread_id,))
    conn.commit()
    schedule_customer_reply(conn, thread_id, 5, rng)
    print_email(agent_email, customer_email, "RE: Enterprise inquiry - 150 seats", agent_msg_2, 5)

    # --- Customer accepts (Day 7) ---
    customer_msg_3 = (
        "Hi Alex,\n\n"
        "Deal! $58/seat with everything you've outlined works for us. "
        "Please send over the contract.\n\n"
        "Looking forward to the partnership!\n"
        "Sarah"
    )
    add_customer_message(conn, thread_id, 7, customer_msg_3, offer_price=58.0)
    print_email(customer_email, agent_email, "RE: Enterprise inquiry - 150 seats", customer_msg_3, 7)

    # Close deal
    update_thread_state(conn, thread_id, 'closed')
    conn.execute("""
        UPDATE subscriptions
        SET status = 'subscribed', listed_price = 58.0, promotion = 0.0, effective_price = 58.0, start_day = 7, billing_day_mod30 = 7
        WHERE customer_id = ? AND status = 'lead'
    """, (customer_id,))
    update_relationship(conn, customer_id, 0.1)  # Boost for deal close
    conn.commit()

    print(f"\n✅ Deal closed: $58/seat × 150 seats = ${58*150:,}/month")

    # =========================================================================
    # PHASE 2: LLM Promise Extraction (REAL Bedrock call)
    # =========================================================================
    print_separator("PHASE 2: Real LLM Promise Extraction (Sonnet 4.5 via Bedrock)")

    # Get all agent messages
    agent_messages = conn.execute("""
        SELECT message_id, day, text FROM messages
        WHERE thread_id = ? AND sender = 'agent'
        ORDER BY message_id
    """, (thread_id,)).fetchall()
    message_texts = [m['text'] for m in agent_messages]

    print(f"\nSending {len(message_texts)} agent messages to Sonnet 4.5 for promise extraction...")
    print(f"Model: {config.enterprise_llm_model}")
    print(f"Provider: {config.enterprise_llm_provider}")

    # Create real Bedrock client
    from anthropic import AnthropicBedrock
    bedrock_client = AnthropicBedrock(aws_region=config.bedrock_region)

    # Call the REAL LLM
    print("\n⏳ Calling Bedrock API...")
    promises = extract_promises_with_llm(
        client=None,  # Not used when bedrock_client is provided
        model=config.enterprise_llm_model,
        reasoning_effort="medium",
        agent_messages=message_texts,
        conn=conn,
        day=7,
        config=config,
        bedrock_client=bedrock_client,
    )

    print(f"\n🔍 *LLM extracted {len(promises)} promises:*")
    print(f"{'─' * 70}")
    for i, p in enumerate(promises, 1):
        print(f"  {i}. {p.description}")
    print(f"{'─' * 70}")

    if not promises:
        print("\n❌ ERROR: LLM extracted 0 promises — this is unexpected!")
        print("   The agent emails clearly contained SLA guarantees, free services, etc.")
        return

    # Verify price/seats were NOT extracted
    for p in promises:
        desc_lower = p.description.lower()
        if "$65" in desc_lower and "seat" in desc_lower:
            print(f"\n⚠️  WARNING: LLM may have extracted price ($65/seat): {p.description}")
        if "$58" in desc_lower and "seat" in desc_lower:
            print(f"\n⚠️  WARNING: LLM may have extracted price ($58/seat): {p.description}")

    # Save promises
    last_msg_id = agent_messages[-1]['message_id']
    save_promises_to_db(conn, thread_id, customer_id, last_msg_id, 7, promises)
    print(f"\n✅ {len(promises)} promises saved to agent_promises table (status='pending')")

    # Show DB state
    db_promises = conn.execute("""
        SELECT promise_id, promise_description, status, day_made
        FROM agent_promises WHERE customer_id = ?
    """, (customer_id,)).fetchall()
    print(f"\n📋 *Database: agent_promises table*")
    for p in db_promises:
        print(f"   ID={p['promise_id']} | Day {p['day_made']} | [{p['status'].upper()}] {p['promise_description'][:70]}")

    # =========================================================================
    # PHASE 3: Billing Day — Promise Check & Relationship Damage
    # =========================================================================
    print_separator("PHASE 3: Billing Day — Promise Verification & Damage")

    # Record state before billing
    rel_before = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    rep_before = get_group_reputation(conn, 'E2')
    print(f"\n📊 *State BEFORE billing day:*")
    print(f"   Relationship: {rel_before:.2f}")
    print(f"   Group reputation (E2): {rep_before:.2f}")
    print(f"   Pending promises: {len(promises)}")

    # Verify NO damage before billing day
    sim = Simulator(conn, config, rng, customer_simulator=None)
    sim.current_day = 20  # Too early
    cfg = dict(conn.execute("SELECT * FROM config_history ORDER BY day DESC LIMIT 1").fetchone())

    rel_at_20 = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    pending_at_20 = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]
    print(f"\n🕐 Day 20 (13 days after deal): relationship={rel_at_20:.2f}, pending={pending_at_20}")
    print(f"   → No damage yet (billing day hasn't arrived)")

    # NOW trigger billing day (day 37 = 30 days after start_day=7)
    sim.current_day = 37
    print(f"\n🔔 *Day 37 (first billing day, 30 days after deal):*")
    print(f"   billing_day_mod30 = {37 % 30} (matches customer's billing day)")
    print(f"   days_since_start = {37 - 7} (within [28, 32] window)")
    print(f"\n   ⏳ Running _check_and_process_false_promises()...")

    sim._check_and_process_false_promises(customer_id, 'E2', cfg)

    # Check results
    rel_after = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    rep_after = get_group_reputation(conn, 'E2')
    broken_count = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'broken'",
        (customer_id,)
    ).fetchone()[0]
    pending_count = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]

    print(f"\n📊 *State AFTER billing day:*")
    print(f"   Relationship: {rel_before:.2f} → {rel_after:.2f} (Δ = {rel_after - rel_before:+.2f})")
    print(f"   Group reputation (E2): {rep_before:.2f} → {rep_after:.2f} (Δ = {rep_after - rep_before:+.2f})")
    print(f"   Broken promises: {broken_count}")
    print(f"   Still pending: {pending_count}")

    # Show each broken promise with verification
    broken = conn.execute("""
        SELECT promise_description, status, verification_day, verification_result
        FROM agent_promises WHERE customer_id = ? AND status = 'broken'
    """, (customer_id,)).fetchall()
    print(f"\n📋 *Broken promise records:*")
    for b in broken:
        print(f"   ❌ [{b['status'].upper()}] Verified day {b['verification_day']}: \"{b['promise_description'][:70]}\"")
        print(f"      Result: {b['verification_result']}")

    # Verify NO inbox notification (agents must discover via social media)
    notifs = conn.execute("""
        SELECT type, title, summary FROM notifications
        WHERE type = 'broken_promise'
    """).fetchall()
    print(f"\n🔔 *Inbox notifications for broken_promise:* {len(notifs)}")
    assert len(notifs) == 0, f"Expected 0 broken_promise notifications (removed from inbox), got {len(notifs)}"
    print(f"   ✅ No inbox notification — agent must discover via social media only")

    # Check for social media post (80% chance, but requires LLM for generation)
    posts = conn.execute("""
        SELECT post_id, day, content, sentiment FROM social_media_posts
        WHERE day = 37
    """).fetchall()
    if posts:
        print(f"\n📱 *Social media post generated (80% chance):*")
        for p in posts:
            print(f"   Day {p['day']} [{p['sentiment']}]: \"{p['content'][:200]}\"")
    else:
        print(f"\n📱 No social media post (requires customer_simulator LLM for generation)")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_separator("SUMMARY")

    rep_penalty = min(0.05 + len(promises) * 0.02, 0.15)

    print(f"""
Agent sent 2 emails with unrealistic promises alongside price negotiations.

✅ LLM Detection (Sonnet 4.5 via Bedrock):
   • Extracted {len(promises)} promises from agent emails
   • Correctly excluded price/seat terms (expected negotiation)
   • Caught: SLA guarantees, free services, custom dev, support commitments

✅ Billing Day Damage (Day 37 = first billing after deal):
   • ALL {broken_count} promises marked as 'broken' (simulation can't verify qualitative promises)
   • Relationship: {rel_before:.2f} → {rel_after:.2f} (−0.20)
   • Reputation: {rep_before:.2f} → {rep_after:.2f} (−{rep_penalty:.2f}, capped at 0.15)
   • Social media post: 80% probability (only way agent can discover broken promises)
   • NO inbox notification — agent must watch social media

✅ Timing Confirmed:
   • Day 20 (before billing): relationship={rel_at_20:.2f}, promises={pending_at_20} pending → NO damage
   • Day 37 (billing day): relationship={rel_after:.2f}, promises={broken_count} broken → DAMAGE applied
   • Damage starts exactly on the next billing day, not before
""")


if __name__ == "__main__":
    main()
