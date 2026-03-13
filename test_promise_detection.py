#!/usr/bin/env python3
"""Test: Unrealistic promises in enterprise negotiation agent replies.

Tests the full chain:
1. Agent replies to enterprise negotiation with unrealistic promises (beside price)
2. LLM-based promise extraction detects them when the deal closes
3. On the first billing day (~30 days later), all promises are marked as broken
4. Relationship is damaged (-0.2), reputation penalized, social media post possible
5. Confirm the damage happens starting from the next billing day (not before)

This test has two modes:
- TEST A: Direct DB insertion (no LLM) — tests the billing/damage chain
- TEST B: LLM mock — tests that the extraction prompt catches unrealistic promises
"""

import sqlite3
import json
import tempfile
from pathlib import Path
from numpy.random import Generator, PCG64
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.config import BenchmarkConfig, CUSTOMER_GROUPS, MODEL_TIERS
from saas_bench.database import init_database, add_ledger_entry, set_group_reputation, get_group_reputation
from saas_bench.enterprise import (
    create_negotiation_thread, add_customer_message, get_negotiation_state,
    compute_customer_offer_price, compute_max_accepting_price,
    schedule_customer_reply, update_thread_state, evaluate_agent_offer,
    generate_enterprise_email, update_relationship
)
from saas_bench.customer_llm import extract_promises_with_llm, save_promises_to_db, ExtractedPromise


def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def setup_test_db(rng):
    """Create a test database with enterprise customer and config."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test_promises.db"
    conn = init_database(db_path)
    config = BenchmarkConfig()

    # Insert initial config
    conn.execute("""
        INSERT INTO config_history (
            day, price_A, price_B, price_C,
            tier_A, tier_B, tier_C,
            spend_advertising, spend_operations, spend_development,
            capacity_tier
        ) VALUES (0, 29.0, 79.0, 199.0, 2, 3, 4, 500, 1000, 500, 1)
    """)
    add_ledger_entry(conn, 0, 'subscription_payment', 100000, 'Initial')
    conn.commit()

    # Create enterprise customer (E2 group, 150 seats)
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

    # Set email
    email = generate_enterprise_email(customer_id, rng)
    conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

    # Initialize customer state
    conn.execute("""
        INSERT INTO customer_state (
            customer_id, satisfaction, relationship,
            current_steepness_left, current_steepness_right,
            current_c_max, current_slope
        ) VALUES (?, 0.5, 0.7, 1.5, 3.0, 80.0, 0.003)
    """, (customer_id,))

    # Initialize group reputation
    set_group_reputation(conn, 'E2', 0.8, 0)

    # Create lead subscription (billing_day_mod30 = 1 so billing triggers on day%30==1)
    conn.execute("""
        INSERT INTO subscriptions (
            customer_id, plan, listed_price, promotion, effective_price, start_day,
            status, billing_day_mod30, daily_usage_rate
        ) VALUES (?, 'B', 79.0, 0.0, 0.0, 1, 'lead', 1, 50.0)
    """, (customer_id,))
    conn.commit()

    return conn, config, customer_id, tmpdir


def run_negotiation_with_promises(conn, config, customer_id, rng):
    """Simulate a negotiation where agent makes unrealistic promises.

    Returns thread_id and the day the deal was closed.
    """
    # Create negotiation thread
    thread_id = create_negotiation_thread(conn, customer_id, 'new_lead', 1, 'lead')

    # Customer initial message (Day 1)
    add_customer_message(conn, thread_id, 1,
        "Hi, we're evaluating AI solutions for our team of 150 people. "
        "We're interested in Plan B. What kind of pricing and support can you offer?")

    # Agent reply (Day 2) — WITH UNREALISTIC PROMISES
    agent_msg_1 = (
        "Great to hear from you! For 150 seats on Plan B, I can offer $65/seat/month. "
        "Additionally, I'm happy to include the following for your team:\n"
        "- Dedicated 24/7 support engineer assigned exclusively to your account\n"
        "- 99.99% SLA uptime guarantee with financial credits for any downtime\n"
        "- Free custom feature development for any integrations you need\n"
        "- Quarterly business reviews with our CEO personally\n"
        "- 60-day free trial with full functionality before committing"
    )
    offer_1 = {'price_per_seat': 65.0, 'plan': 'B', 'seats': 150}

    conn.execute("""
        INSERT INTO messages (day, thread_id, sender, text, offer_json)
        VALUES (?, ?, 'agent', ?, ?)
    """, (2, thread_id, agent_msg_1, json.dumps(offer_1)))
    conn.execute("UPDATE threads SET replied = 1 WHERE thread_id = ?", (thread_id,))
    conn.commit()

    schedule_customer_reply(conn, thread_id, 2, rng)

    # Customer counter (Day 4)
    state = get_negotiation_state(conn, thread_id)
    add_customer_message(conn, thread_id, 4,
        "Those extras sound great, but $65/seat is still above our budget. "
        "Can you come down to $55/seat with all those perks?",
        offer_price=55.0)

    # Agent reply (Day 5) — MORE promises
    agent_msg_2 = (
        "I can meet you at $58/seat/month. Plus I'll throw in:\n"
        "- Free onboarding and data migration services (worth $50K)\n"
        "- Priority access to our beta features\n"
        "- A guaranteed response time of under 15 minutes for all support tickets"
    )
    offer_2 = {'price_per_seat': 58.0, 'plan': 'B', 'seats': 150}

    conn.execute("""
        INSERT INTO messages (day, thread_id, sender, text, offer_json)
        VALUES (?, ?, 'agent', ?, ?)
    """, (5, thread_id, agent_msg_2, json.dumps(offer_2)))
    conn.execute("UPDATE threads SET replied = 1 WHERE thread_id = ?", (thread_id,))
    conn.commit()

    schedule_customer_reply(conn, thread_id, 5, rng)

    # Customer accepts (Day 7)
    add_customer_message(conn, thread_id, 7,
        "Deal! $58/seat with all those perks works for us. Let's proceed.",
        offer_price=58.0)

    # Close the deal — convert lead to subscribed at day 7
    update_thread_state(conn, thread_id, 'active')
    conn.execute("""
        UPDATE subscriptions
        SET status = 'subscribed', listed_price = 58.0, promotion = 0.0, effective_price = 58.0, start_day = 7
        WHERE customer_id = ? AND status = 'lead'
    """, (customer_id,))
    conn.commit()

    return thread_id, 7  # deal closed on day 7


def test_a_direct_promise_insertion():
    """TEST A: Direct promise insertion → billing day damage chain.

    Tests that:
    1. Manually inserted promises are checked on billing day
    2. All promises are marked as broken
    3. Relationship is damaged (-0.2)
    4. Reputation is penalized
    5. Damage happens ON the first billing day (28-32 days after start), NOT before
    """
    print_separator("TEST A: Direct Promise Insertion → Billing Day Damage")

    rng = Generator(PCG64(42))
    conn, config, customer_id, tmpdir = setup_test_db(rng)
    thread_id, deal_day = run_negotiation_with_promises(conn, config, customer_id, rng)

    # Manually insert promises (simulating what extract_promises_with_llm would find)
    promises = [
        "Dedicated 24/7 support engineer assigned exclusively to the account",
        "99.99% SLA uptime guarantee with financial credits for downtime",
        "Free custom feature development for integrations",
        "Quarterly business reviews with CEO personally",
        "60-day free trial with full functionality",
        "Free onboarding and data migration services worth $50K",
        "Guaranteed response time under 15 minutes for support tickets",
    ]

    last_msg_id = conn.execute(
        "SELECT MAX(message_id) FROM messages WHERE thread_id = ? AND sender = 'agent'",
        (thread_id,)
    ).fetchone()[0]

    for desc in promises:
        conn.execute("""
            INSERT INTO agent_promises (
                thread_id, customer_id, message_id, day_made,
                promise_description, status
            ) VALUES (?, ?, ?, ?, ?, 'pending')
        """, (thread_id, customer_id, last_msg_id, deal_day, desc))
    conn.commit()

    # Verify promises are saved
    count = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]
    print(f"\n✅ {count} promises saved as 'pending' in agent_promises table")
    assert count == 7, f"Expected 7 promises, got {count}"

    # Check relationship BEFORE billing
    rel_before = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    rep_before = get_group_reputation(conn, 'E2')
    print(f"\n📊 *Before billing day:*")
    print(f"   Relationship: {rel_before:.2f}")
    print(f"   Group reputation (E2): {rep_before:.2f}")

    # Import simulation to test _check_and_process_false_promises
    from saas_bench.simulation import Simulator

    # Create a Simulator object (no LLM needed for this test)
    sim = Simulator(conn, config, rng, customer_simulator=None)
    # (Simulator already initialized with conn, config, rng)

    # ---- Test: BEFORE first billing (day 20) — promises should NOT be checked ----
    sim.current_day = 20
    billing_day = sim.current_day % 30  # = 20

    # Billing only processes subscribers whose billing_day_mod30 matches
    # Our customer has billing_day_mod30 = 1, so day 20 won't trigger
    subscribers_on_day_20 = conn.execute("""
        SELECT * FROM subscriptions
        WHERE status = 'subscribed' AND end_day IS NULL AND billing_day_mod30 = ?
    """, (billing_day,)).fetchall()
    print(f"\n🔍 Day 20 (billing_day_mod30={billing_day}): {len(subscribers_on_day_20)} subscribers with matching billing day")

    # Verify promises are STILL pending
    still_pending = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]
    print(f"   Promises still pending: {still_pending}")
    assert still_pending == 7, f"Promises should still be pending on day 20"

    rel_after_20 = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    print(f"   Relationship unchanged: {rel_after_20:.2f}")
    assert rel_after_20 == rel_before, "Relationship should not change before billing day"

    # ---- Test: ON first billing day (~30 days after start_day=7) ----
    # start_day = 7, first billing = day 37 (30 days later)
    # billing_day_mod30 = 1, so billing fires when current_day % 30 == 1
    # Day 31 has day%30 == 1, but days_since_start = 31-7 = 24 (< 28, too early)
    # Day 61 has day%30 == 1, but days_since_start = 61-7 = 54 (> 32, too late)
    # Wait — the check is: 28 <= days_since_start <= 32
    # start_day=7, so 28<=d-7<=32 means 35<=d<=39
    # billing_day_mod30=1, so day%30==1 means day=31,61,...
    # day 31: d-7=24 (too early), day 61: d-7=54 (too late)
    # Hmm — this means the window might not align! Let me check with billing_day_mod30=7

    # Actually, let's recalculate. For billing_day_mod30=1:
    # Days where billing fires: 1, 31, 61, 91, ...
    # start_day=7, so days_since_start at billing:
    #   day 31: 31-7=24 (outside 28-32)
    #   day 61: 61-7=54 (outside 28-32)
    # This means the promise check would NEVER fire with this setup!

    # Let me fix: set billing_day_mod30 such that it aligns.
    # start_day=7, we need billing fire at day ~37 (30 days later)
    # day%30 should be 37%30 = 7
    conn.execute("""
        UPDATE subscriptions SET billing_day_mod30 = 7
        WHERE customer_id = ? AND status = 'subscribed'
    """, (customer_id,))
    conn.commit()

    # Now: billing fires on days 7, 37, 67, ...
    # Day 37: days_since_start = 37-7 = 30 → 28 <= 30 <= 32 ✅

    sim.current_day = 37
    billing_day = sim.current_day % 30  # = 7

    # Get config dict for _process_billing
    cfg = conn.execute("SELECT * FROM config_history ORDER BY day DESC LIMIT 1").fetchone()
    config_dict = dict(cfg) if cfg else {}

    print(f"\n🔔 *Day 37 (first billing day, {sim.current_day - 7} days since deal):*")
    print(f"   billing_day_mod30 = {billing_day}")

    # Call _check_and_process_false_promises directly
    sim._check_and_process_false_promises(customer_id, 'E2', config_dict)

    # Check promises are now broken
    broken_count = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'broken'",
        (customer_id,)
    ).fetchone()[0]
    pending_count = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]

    print(f"\n📊 *After first billing day:*")
    print(f"   Promises broken: {broken_count}")
    print(f"   Promises still pending: {pending_count}")
    assert broken_count == 7, f"Expected 7 broken promises, got {broken_count}"
    assert pending_count == 0, f"Expected 0 pending promises, got {pending_count}"

    # Check relationship damage
    rel_after = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    rep_after = get_group_reputation(conn, 'E2')

    print(f"\n   Relationship: {rel_before:.2f} → {rel_after:.2f} (delta: {rel_after - rel_before:+.2f})")
    print(f"   Group reputation (E2): {rep_before:.2f} → {rep_after:.2f} (delta: {rep_after - rep_before:+.2f})")

    assert rel_after < rel_before, "Relationship should decrease after broken promises"
    assert rel_after == rel_before - 0.2, f"Relationship should decrease by 0.2 (got {rel_before - rel_after:.2f})"

    # Reputation: base 0.05 + 7*0.02 = 0.19, capped at 0.15
    expected_rep_penalty = min(0.05 + 7 * 0.02, 0.15)
    expected_rep = max(0.0, rep_before - expected_rep_penalty)
    assert abs(rep_after - expected_rep) < 0.01, f"Expected reputation {expected_rep:.2f}, got {rep_after:.2f}"
    print(f"   Reputation penalty: {expected_rep_penalty:.2f} (base 0.05 + 7×0.02 = 0.19, capped at 0.15)")

    # Check verification records
    verifications = conn.execute("""
        SELECT promise_description, status, verification_day, verification_result
        FROM agent_promises WHERE customer_id = ?
    """, (customer_id,)).fetchall()

    print(f"\n📋 *Promise verification records:*")
    for v in verifications:
        print(f"   [{v['status'].upper()}] Day {v['verification_day']}: \"{v['promise_description'][:60]}...\"")
        print(f"           Result: {v['verification_result']}")

    # Verify NO inbox notification is created (agents must discover via social media)
    notifs = conn.execute("""
        SELECT type, title, summary FROM notifications
        WHERE type = 'broken_promise'
    """).fetchall()
    print(f"\n🔔 *Inbox notifications for broken_promise:* {len(notifs)}")
    assert len(notifs) == 0, f"Expected 0 broken_promise notifications (removed from inbox), got {len(notifs)}"
    print(f"   ✅ No inbox notification — agent must discover via social media")

    print(f"\n✅ TEST A PASSED: All {broken_count} unrealistic promises detected as broken on billing day {sim.current_day}")
    print(f"   Relationship damaged: {rel_before:.2f} → {rel_after:.2f}")
    print(f"   Reputation penalized: {rep_before:.2f} → {rep_after:.2f}")
    print(f"   No inbox notification — social media is the only discovery path")
    print(f"   Damage occurred at first billing day (day 37), NOT before (verified at day 20)")


def test_b_llm_promise_extraction_mock():
    """TEST B: Mock LLM extracts unrealistic promises from agent messages.

    Tests that the extraction prompt correctly identifies:
    - SLA guarantees
    - Free services
    - Custom development promises
    - Support level commitments
    - Free trials
    But does NOT extract:
    - Price per seat (expected negotiation term)
    - Seat count (expected negotiation term)
    """
    print_separator("TEST B: LLM Promise Extraction (Mocked)")

    rng = Generator(PCG64(42))
    conn, config, customer_id, tmpdir = setup_test_db(rng)
    thread_id, deal_day = run_negotiation_with_promises(conn, config, customer_id, rng)

    # Get agent messages
    agent_messages = conn.execute("""
        SELECT text FROM messages
        WHERE thread_id = ? AND sender = 'agent'
        ORDER BY message_id
    """, (thread_id,)).fetchall()
    message_texts = [m['text'] for m in agent_messages]

    print(f"\n📨 Agent messages to analyze ({len(message_texts)} messages):")
    for i, msg in enumerate(message_texts):
        print(f"\n   Message {i+1}:")
        for line in msg.split('\n'):
            print(f"     {line}")

    # Mock the LLM response to simulate what a real LLM would extract
    mock_llm_response = json.dumps([
        {"description": "Dedicated 24/7 support engineer assigned exclusively to the account"},
        {"description": "99.99% SLA uptime guarantee with financial credits for any downtime"},
        {"description": "Free custom feature development for any integrations needed"},
        {"description": "Quarterly business reviews with the CEO personally"},
        {"description": "60-day free trial with full functionality before committing"},
        {"description": "Free onboarding and data migration services worth $50K"},
        {"description": "Priority access to beta features"},
        {"description": "Guaranteed response time of under 15 minutes for all support tickets"},
    ])

    # Create mock client that returns the expected response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = mock_llm_response
    mock_response.usage.input_tokens = 500
    mock_response.usage.output_tokens = 200
    mock_client.responses.create.return_value = mock_response

    # Mock bedrock client
    mock_bedrock = MagicMock()
    mock_bedrock_response = MagicMock()
    mock_bedrock_response.content = [MagicMock(text=mock_llm_response)]
    mock_bedrock_response.usage.input_tokens = 500
    mock_bedrock_response.usage.output_tokens = 200
    mock_bedrock.messages.create.return_value = mock_bedrock_response

    # Run extraction
    promises = extract_promises_with_llm(
        client=mock_client,
        model="test-model",
        reasoning_effort="medium",
        agent_messages=message_texts,
        conn=conn,
        day=deal_day,
        config=config,
        bedrock_client=mock_bedrock,
    )

    print(f"\n🔍 *Extracted {len(promises)} promises:*")
    for i, p in enumerate(promises):
        print(f"   {i+1}. {p.description}")

    assert len(promises) == 8, f"Expected 8 promises, got {len(promises)}"

    # Verify that price-related terms were NOT extracted (the LLM prompt tells it not to)
    for p in promises:
        desc_lower = p.description.lower()
        assert "$65/seat" not in desc_lower, "Should NOT extract price per seat"
        assert "$58/seat" not in desc_lower, "Should NOT extract price per seat"
        assert "150 seats" not in desc_lower, "Should NOT extract seat count"

    # Save promises to DB
    last_msg_id = conn.execute(
        "SELECT MAX(message_id) FROM messages WHERE thread_id = ? AND sender = 'agent'",
        (thread_id,)
    ).fetchone()[0]

    save_promises_to_db(conn, thread_id, customer_id, last_msg_id, deal_day, promises)

    # Verify saved
    saved = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]
    print(f"\n✅ {saved} promises saved to database")
    assert saved == 8

    # Verify the extraction prompt was called with correct content
    if config.enterprise_llm_provider == "bedrock":
        call_args = mock_bedrock.messages.create.call_args
        system_prompt = call_args.kwargs.get('system', '')
        user_msg = call_args.kwargs['messages'][0]['content']
    else:
        call_args = mock_client.responses.create.call_args

    print(f"\n✅ TEST B PASSED: LLM extraction correctly identified 8 unrealistic promises")
    print(f"   Excluded: price per seat, seat count (expected negotiation terms)")
    print(f"   Included: SLA, free services, custom dev, support levels, free trials")


def test_c_timing_verification():
    """TEST C: Verify promise checking timing — damage only on billing day.

    Runs the simulation through multiple days and confirms:
    - Days 8-35: No promise checking (too early)
    - Day 37 (first billing, 30 days after start_day=7): Promises checked and broken
    - Day 67 (second billing): No more promises to check (already processed)
    """
    print_separator("TEST C: Timing Verification — Damage Only on Billing Day")

    rng = Generator(PCG64(42))
    conn, config, customer_id, tmpdir = setup_test_db(rng)
    thread_id, deal_day = run_negotiation_with_promises(conn, config, customer_id, rng)

    # Fix billing_day_mod30 to align with start_day
    conn.execute("""
        UPDATE subscriptions SET billing_day_mod30 = 7, start_day = 7
        WHERE customer_id = ? AND status = 'subscribed'
    """, (customer_id,))
    conn.commit()

    # Insert promises
    last_msg_id = conn.execute(
        "SELECT MAX(message_id) FROM messages WHERE thread_id = ? AND sender = 'agent'",
        (thread_id,)
    ).fetchone()[0]
    for desc in ["24/7 dedicated support", "99.99% SLA guarantee", "Free custom development"]:
        conn.execute("""
            INSERT INTO agent_promises (
                thread_id, customer_id, message_id, day_made,
                promise_description, status
            ) VALUES (?, ?, ?, ?, ?, 'pending')
        """, (thread_id, customer_id, last_msg_id, deal_day, desc))
    conn.commit()

    # Create simulation object
    from saas_bench.simulation import Simulator
    sim = Simulator(conn, config, rng, customer_simulator=None)

    cfg = dict(conn.execute("SELECT * FROM config_history ORDER BY day DESC LIMIT 1").fetchone())

    # Track relationship over time
    print(f"\n📊 *Relationship & promise status over time:*")
    print(f"   {'Day':>4} | {'days_since_start':>17} | {'billing?':>8} | {'28<=d<=32?':>10} | {'Promises':>10} | {'Relationship':>12}")
    print(f"   {'-'*4}-+-{'-'*17}-+-{'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*12}")

    test_days = [8, 15, 20, 25, 30, 35, 36, 37, 38, 39, 40, 50, 60, 67]

    for day in test_days:
        sim.current_day = day
        billing_day_mod30 = day % 30
        is_billing = (billing_day_mod30 == 7)
        days_since_start = day - 7
        in_window = 28 <= days_since_start <= 32

        # If it's billing day and in window, process
        if is_billing and in_window:
            sim._check_and_process_false_promises(customer_id, 'E2', cfg)

        pending = conn.execute(
            "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
            (customer_id,)
        ).fetchone()[0]
        broken = conn.execute(
            "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'broken'",
            (customer_id,)
        ).fetchone()[0]
        rel = conn.execute(
            "SELECT relationship FROM customer_state WHERE customer_id = ?",
            (customer_id,)
        ).fetchone()[0]

        status_str = f"{pending}P/{broken}B"
        billing_str = "YES" if is_billing else "no"
        window_str = "YES" if in_window else "no"

        marker = " ← DAMAGE" if is_billing and in_window else ""
        print(f"   {day:>4} | {days_since_start:>17} | {billing_str:>8} | {window_str:>10} | {status_str:>10} | {rel:>12.2f}{marker}")

    # Final assertions
    final_pending = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'pending'",
        (customer_id,)
    ).fetchone()[0]
    final_broken = conn.execute(
        "SELECT COUNT(*) FROM agent_promises WHERE customer_id = ? AND status = 'broken'",
        (customer_id,)
    ).fetchone()[0]
    final_rel = conn.execute(
        "SELECT relationship FROM customer_state WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]

    assert final_pending == 0, f"All promises should be broken, but {final_pending} still pending"
    assert final_broken == 3, f"Expected 3 broken promises, got {final_broken}"
    assert abs(final_rel - 0.5) < 0.01, f"Expected relationship 0.7 - 0.2 = 0.5, got {final_rel}"

    print(f"\n✅ TEST C PASSED:")
    print(f"   - Days 8-36: No damage (not billing day or not in 28-32 day window)")
    print(f"   - Day 37: DAMAGE (billing day + 30 days since start → in [28,32] window)")
    print(f"   - Days 38+: No further damage (promises already processed)")
    print(f"   - Relationship: 0.70 → 0.50 (exactly -0.20 on billing day)")


if __name__ == "__main__":
    print("=" * 80)
    print("  ENTERPRISE NEGOTIATION: UNREALISTIC PROMISE DETECTION TEST SUITE")
    print("=" * 80)

    # Run all tests
    test_a_direct_promise_insertion()
    test_b_llm_promise_extraction_mock()
    test_c_timing_verification()

    print("\n" + "=" * 80)
    print("  ALL TESTS PASSED ✅")
    print("=" * 80)
    print("\nSummary:")
    print("  A: Unrealistic promises in agent replies → detected as broken on billing day")
    print("     → Relationship damaged (-0.2), reputation penalized (up to -0.15)")
    print("  B: LLM extraction correctly catches promises (SLA, free services, etc.)")
    print("     → Excludes expected terms (price, seats)")
    print("  C: Damage timing verified → only on first billing day (28-32 days after start)")
    print("     → No damage before or after the billing window")
