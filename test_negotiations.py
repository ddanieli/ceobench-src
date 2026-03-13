#!/usr/bin/env python3
"""Test all negotiation cases and display conversation history.

Tests the 4 negotiation types:
1. NEW_LEAD - Enterprise customers arriving as leads requiring sales negotiation
2. PLAN_CHANGE - Existing customers wanting to upgrade/downgrade
3. CHURN_PREVENTION - Customers at risk due to satisfaction dropping
4. BUDGET_FREEZE - Shock event shifting customer's cost-quality curve

Uses evaluate_agent_offer to properly simulate customer acceptance logic.
"""

import sqlite3
import json
import tempfile
from pathlib import Path
from numpy.random import Generator, PCG64

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.config import BenchmarkConfig, CUSTOMER_GROUPS
from saas_bench.database import init_database, add_ledger_entry
from saas_bench.enterprise import (
    create_negotiation_thread, add_customer_message, get_negotiation_state,
    compute_customer_offer_price, compute_max_accepting_price, get_quality_for_plan,
    schedule_customer_reply, update_thread_state, evaluate_agent_offer,
    generate_enterprise_email
)


def print_separator(title: str):
    """Print a separator with title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_conversation(conn: sqlite3.Connection, thread_id: int):
    """Print the full conversation history for a thread."""
    # Get thread info
    thread = conn.execute("""
        SELECT t.*, c.seat_count, c.group_id, c.email
        FROM threads t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.thread_id = ?
    """, (thread_id,)).fetchone()

    print(f"\n--- Thread #{thread_id} ---")
    print(f"Type: {thread['thread_type']}")
    print(f"State: {thread['state']}")
    print(f"Customer ID: {thread['customer_id']} (Group: {thread['group_id']}, {thread['seat_count']} seats)")
    if thread['email']:
        print(f"Customer Email: {thread['email']}")
    print(f"Turn: {thread['negotiation_turn']}")
    if thread['current_offer_price']:
        print(f"Current Offer: ${thread['current_offer_price']:.2f}/seat")
    else:
        print("Current Offer: None")

    # Get messages
    messages = conn.execute("""
        SELECT day, sender, text, offer_json, email
        FROM messages
        WHERE thread_id = ?
        ORDER BY message_id
    """, (thread_id,)).fetchall()

    print(f"\n📨 Conversation ({len(messages)} messages):")
    print("-" * 60)

    for msg in messages:
        sender_icon = "👤" if msg['sender'] == 'customer' else "🤖"
        offer_str = ""
        if msg['offer_json']:
            try:
                offer = json.loads(msg['offer_json'])
                if 'price' in offer and offer['price']:
                    offer_str = f" [Offer: ${offer['price']:.2f}/seat]"
            except:
                pass

        # Show email for customer messages
        email_str = f" <{msg['email']}>" if msg['email'] else ""
        print(f"\nDay {msg['day']} - {sender_icon} {msg['sender'].upper()}{email_str}{offer_str}")
        print(f"  \"{msg['text']}\"")

    print("-" * 60)


def simulate_agent_response(conn: sqlite3.Connection, thread_id: int, day: int,
                           message: str, offer_price: float = None):
    """Simulate an agent response to a thread."""
    offer_json = json.dumps({'price': offer_price}) if offer_price else None

    conn.execute("""
        INSERT INTO messages (day, thread_id, sender, text, offer_json)
        VALUES (?, ?, 'agent', ?, ?)
    """, (day, thread_id, message, offer_json))
    conn.commit()


def test_new_lead_negotiation():
    """Test new_lead negotiation for enterprise customers."""
    print_separator("TEST 1: NEW_LEAD NEGOTIATION")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)
        config = BenchmarkConfig()
        rng = Generator(PCG64(42))

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

        # Create an enterprise customer (E2 - Quality-First) with realistic parameters
        # q_min=0.50, c_max=$80, slope=0.003
        # For Plan B (quality ~0.75): max_price = (0.75 - 0.50) / 0.003 = $83.33/seat
        # This allows agent to offer prices in reasonable range
        customer_id = conn.execute("""
            INSERT INTO customers (
                customer_type, group_id, created_day,
                q_min, c_max, usage_demand,
                reply_delay_mean, reply_delay_std, negotiation_rate, max_negotiation_turns,
                expected_quality,
                quality_sensitivity, price_sensitivity, willingness_to_pay, usage_scale, patience,
                seat_count
            ) VALUES ('large', 'E2', 1, 0.50, 80.0, 40.0, 2.0, 0.5, 0.25, 6, 0.0, 0.75, 0.3, 80.0, 40.0, 0.6, 150)
        """).lastrowid

        # Generate and set email for enterprise customer
        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        # Initialize customer state
        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.5, 0.5, 0.50, 80.0, 0.003)
        """, (customer_id,))

        # Create lead subscription
        conn.execute("""
            INSERT INTO subscriptions (customer_id, plan, listed_price, promotion, effective_price, start_day, status, billing_day_mod30)
            VALUES (?, 'B', 79.0, 0.0, 0.0, 1, 'lead', 1)
        """, (customer_id,))
        conn.commit()

        # Create negotiation thread
        thread_id = create_negotiation_thread(conn, customer_id, 'new_lead', 1, 'lead')

        # Customer initial message
        add_customer_message(conn, thread_id, 1,
            "Hi, we're evaluating AI solutions for our team of 150 people. "
            "We're interested in Plan B. Can you share pricing for enterprise customers?")

        print("\n📋 Scenario: New enterprise lead (E2 - Quality-First, 150 seats)")
        print(f"Customer curve: q_min=0.50, c_max=$80/seat, slope=0.003")

        # Get negotiation state
        state = get_negotiation_state(conn, thread_id)
        quality = get_quality_for_plan(conn, 'B', customer_id, config)
        max_price = compute_max_accepting_price(state, quality)
        customer_offer = compute_customer_offer_price(state, quality, config)

        print(f"Perceived quality for Plan B: {quality:.2f}")
        print(f"Max accepting price: ${max_price:.2f}/seat")
        print(f"Customer's initial offer (turn 0): ${customer_offer:.2f}/seat")

        # Agent response (Day 2) - initial offer at $72/seat (within max)
        agent_offer_1 = 72.0
        decision, counter, is_final = evaluate_agent_offer(state, agent_offer_1, quality, config)
        print(f"\nAgent offers ${agent_offer_1:.2f} → Customer decision: {decision}")

        simulate_agent_response(conn, thread_id, 2,
            f"Thanks for reaching out! For 150 seats on Plan B, we can offer ${agent_offer_1:.2f}/seat/month. "
            "This includes priority support and dedicated success manager.",
            offer_price=agent_offer_1)
        schedule_customer_reply(conn, thread_id, 2, rng)

        # Customer counter (Day 4)
        state = get_negotiation_state(conn, thread_id)
        customer_offer = compute_customer_offer_price(state, quality, config)
        print(f"Customer counters with ${customer_offer:.2f}/seat (turn {state.negotiation_turn})")

        add_customer_message(conn, thread_id, 4,
            f"We appreciate the offer, but we were hoping for something closer to ${customer_offer:.2f}/seat "
            f"given our team size. Can you do better?",
            offer_price=customer_offer)

        # Agent counter (Day 5) - closer to customer's offer
        agent_offer_2 = 65.0
        state = get_negotiation_state(conn, thread_id)
        decision, counter, is_final = evaluate_agent_offer(state, agent_offer_2, quality, config)
        print(f"Agent offers ${agent_offer_2:.2f} → Customer decision: {decision}")

        simulate_agent_response(conn, thread_id, 5,
            f"I understand budget is important. For a 150-seat commitment, I can go to ${agent_offer_2:.2f}/seat/month. "
            "This is our best rate for this volume.",
            offer_price=agent_offer_2)
        schedule_customer_reply(conn, thread_id, 5, rng)

        # Customer counter again (Day 7)
        state = get_negotiation_state(conn, thread_id)
        customer_offer = compute_customer_offer_price(state, quality, config)
        decision, counter, is_final = evaluate_agent_offer(state, agent_offer_2, quality, config)

        if decision == 'accept':
            add_customer_message(conn, thread_id, 7,
                f"That works for us. Let's proceed with ${agent_offer_2:.2f}/seat for 150 seats on Plan B. "
                "Please send over the contract.")
            final_price = agent_offer_2
        else:
            add_customer_message(conn, thread_id, 7,
                f"We're getting closer. Our best is ${customer_offer:.2f}/seat. Can you meet us there?",
                offer_price=customer_offer)

            # Agent accepts customer's offer
            simulate_agent_response(conn, thread_id, 8,
                f"Deal. ${customer_offer:.2f}/seat for 150 seats. I'll send the contract.",
                offer_price=customer_offer)
            final_price = customer_offer

        # Update thread state to closed (deal won)
        update_thread_state(conn, thread_id, 'active')

        # Convert lead to subscribed
        conn.execute("""
            UPDATE subscriptions SET status = 'subscribed', listed_price = ?, promotion = 0.0, effective_price = ?
            WHERE customer_id = ? AND status = 'lead'
        """, (final_price, final_price, customer_id))
        conn.commit()

        print_conversation(conn, thread_id)
        print(f"\n✅ Outcome: Deal closed at ${final_price:.2f}/seat (150 seats = ${final_price * 150:,.0f}/month)")


def test_plan_change_negotiation():
    """Test plan_change negotiation (upgrade scenario)."""
    print_separator("TEST 2: PLAN_CHANGE NEGOTIATION (Upgrade)")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)
        config = BenchmarkConfig()
        rng = Generator(PCG64(123))

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

        # E1 customer with curve allowing reasonable negotiation
        # q_min=0.45, c_max=$60, slope=0.005
        # For Plan B (quality ~0.75): max_price = (0.75 - 0.45) / 0.005 = $60/seat
        customer_id = conn.execute("""
            INSERT INTO customers (
                customer_type, group_id, created_day,
                q_min, c_max, usage_demand,
                reply_delay_mean, reply_delay_std, negotiation_rate, max_negotiation_turns,
                expected_quality,
                quality_sensitivity, price_sensitivity, willingness_to_pay, usage_scale, patience,
                seat_count
            ) VALUES ('large', 'E1', 1, 0.45, 60.0, 30.0, 1.5, 0.4, 0.35, 4, 0.02, 0.6, 0.5, 60.0, 30.0, 0.5, 80)
        """).lastrowid

        # Generate and set email for enterprise customer
        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.65, 0.6, 0.45, 60.0, 0.005)
        """, (customer_id,))

        # They're on Plan A, want to upgrade to Plan B
        conn.execute("""
            INSERT INTO subscriptions (customer_id, plan, listed_price, promotion, effective_price, start_day, status, billing_day_mod30)
            VALUES (?, 'A', 25.0, 0.0, 25.0, 1, 'subscribed', 1)
        """, (customer_id,))
        conn.commit()

        thread_id = create_negotiation_thread(conn, customer_id, 'plan_change', 30, 'evaluation')

        add_customer_message(conn, thread_id, 30,
            "We've been using Plan A for a month and need more capacity. "
            "We're looking to upgrade to Plan B for our 80 seats. What pricing can you offer?")

        print("\n📋 Scenario: Existing E1 customer (80 seats) upgrading A → B")
        print(f"Customer curve: q_min=0.45, c_max=$60/seat, slope=0.005")
        print(f"Current: Plan A at $25/seat")

        state = get_negotiation_state(conn, thread_id)
        quality = get_quality_for_plan(conn, 'B', customer_id, config)
        max_price = compute_max_accepting_price(state, quality)
        customer_offer = compute_customer_offer_price(state, quality, config)

        print(f"Perceived quality for Plan B: {quality:.2f}")
        print(f"Max accepting price for B: ${max_price:.2f}/seat")
        print(f"Customer's initial offer: ${customer_offer:.2f}/seat")

        # Agent offers $52 (within max of $60)
        agent_offer_1 = 52.0
        decision, counter, is_final = evaluate_agent_offer(state, agent_offer_1, quality, config)
        print(f"\nAgent offers ${agent_offer_1:.2f} → Customer decision: {decision}")

        simulate_agent_response(conn, thread_id, 31,
            f"Great to hear you're ready to upgrade! For 80 seats on Plan B, "
            f"I can offer ${agent_offer_1:.2f}/seat/month as a loyalty discount.",
            offer_price=agent_offer_1)
        schedule_customer_reply(conn, thread_id, 31, rng)

        # Customer counter
        state = get_negotiation_state(conn, thread_id)
        customer_offer = compute_customer_offer_price(state, quality, config)
        print(f"Customer counters with ${customer_offer:.2f}/seat (turn {state.negotiation_turn})")

        add_customer_message(conn, thread_id, 33,
            f"We were hoping for ${customer_offer:.2f}/seat given our history. "
            f"Can you meet us there?",
            offer_price=customer_offer)

        # Agent meets customer's offer
        simulate_agent_response(conn, thread_id, 34,
            f"I can do ${customer_offer:.2f}/seat/month for the upgrade. This reflects your loyalty and commitment.",
            offer_price=customer_offer)
        schedule_customer_reply(conn, thread_id, 34, rng)

        # Customer accepts
        state = get_negotiation_state(conn, thread_id)
        decision, counter, is_final = evaluate_agent_offer(state, customer_offer, quality, config)
        print(f"Agent matches customer offer ${customer_offer:.2f} → Customer decision: {decision}")

        add_customer_message(conn, thread_id, 35,
            f"Deal. ${customer_offer:.2f}/seat for Plan B. When does the upgrade take effect?")

        # Schedule plan change for next billing
        conn.execute("""
            UPDATE subscriptions SET pending_plan = 'B', pending_price = ?
            WHERE customer_id = ? AND status = 'subscribed'
        """, (customer_offer, customer_id))
        update_thread_state(conn, thread_id, 'closed')
        conn.commit()

        print_conversation(conn, thread_id)
        print(f"\n✅ Outcome: Upgrade scheduled - Plan B at ${customer_offer:.2f}/seat (80 seats = ${customer_offer * 80:,.0f}/month)")


def test_churn_prevention_negotiation():
    """Test churn_prevention negotiation (satisfaction dropped below threshold)."""
    print_separator("TEST 3: CHURN_PREVENTION NEGOTIATION")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)
        config = BenchmarkConfig()
        rng = Generator(PCG64(456))

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

        # E3 customer whose curve has drifted - now more demanding
        # Drifted: q_min=0.55, c_max=$65, slope=0.004
        # For Plan B (quality ~0.75): max_price = (0.75 - 0.55) / 0.004 = $50/seat
        customer_id = conn.execute("""
            INSERT INTO customers (
                customer_type, group_id, created_day,
                q_min, c_max, usage_demand,
                reply_delay_mean, reply_delay_std, negotiation_rate, max_negotiation_turns,
                expected_quality,
                quality_sensitivity, price_sensitivity, willingness_to_pay, usage_scale, patience,
                seat_count
            ) VALUES ('large', 'E3', 1, 0.50, 70.0, 35.0, 3.5, 1.5, 0.15, 8, -0.02, 0.65, 0.35, 70.0, 35.0, 0.55, 300)
        """).lastrowid

        # Generate and set email for enterprise customer
        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        # Customer state shows drifted curve
        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.45, 0.55, 0.55, 65.0, 0.004)
        """, (customer_id,))

        # Currently paying $60/seat on Plan B (above new max of $50)
        conn.execute("""
            INSERT INTO subscriptions (customer_id, plan, listed_price, promotion, effective_price, start_day, status, billing_day_mod30)
            VALUES (?, 'B', 60.0, 0.0, 60.0, 1, 'subscribed', 15)
        """, (customer_id,))
        conn.commit()

        thread_id = create_negotiation_thread(conn, customer_id, 'churn_prevention', 60, 'churn_risk')

        add_customer_message(conn, thread_id, 60,
            "We need to discuss our subscription. The current pricing doesn't work "
            "for us anymore given what we're getting. We may need to look at alternatives.")

        print("\n📋 Scenario: E3 customer (300 seats) at churn risk")
        print(f"Original curve: q_min=0.50, c_max=$70/seat, slope=0.003")
        print(f"Drifted curve: q_min=0.55, c_max=$65/seat, slope=0.004")
        print(f"Current: Plan B at $60/seat")

        state = get_negotiation_state(conn, thread_id)
        quality = get_quality_for_plan(conn, 'B', customer_id, config)
        max_price = compute_max_accepting_price(state, quality)
        customer_offer = compute_customer_offer_price(state, quality, config)

        print(f"Perceived quality for Plan B: {quality:.2f}")
        print(f"Max accepting price with drifted curve: ${max_price:.2f}/seat")
        print(f"⚠️ Current price ($60) > max acceptable (${max_price:.2f}) - CHURN RISK")
        print(f"Customer's target price: ${customer_offer:.2f}/seat")

        # Agent tries to understand concerns first
        simulate_agent_response(conn, thread_id, 61,
            "I understand your concerns. You've been a valued partner for us. "
            "Can you share more about what's not working? We want to find a solution.",
            offer_price=None)
        schedule_customer_reply(conn, thread_id, 61, rng)

        # Customer explains
        add_customer_message(conn, thread_id, 64,
            f"The quality hasn't been meeting our increased expectations, and at $60/seat "
            f"it's hard to justify. We need a price closer to ${customer_offer:.2f}/seat.",
            offer_price=customer_offer)

        # Agent offers discount at $48 (within max of $50)
        agent_offer = 48.0
        state = get_negotiation_state(conn, thread_id)
        decision, counter, is_final = evaluate_agent_offer(state, agent_offer, quality, config)
        print(f"\nAgent offers ${agent_offer:.2f} → Customer decision: {decision}")

        simulate_agent_response(conn, thread_id, 65,
            f"I hear you. For 300 seats and your long partnership, I can offer ${agent_offer:.2f}/seat/month "
            "plus we'll assign a dedicated solutions engineer to your account.",
            offer_price=agent_offer)
        schedule_customer_reply(conn, thread_id, 65, rng)

        # Customer accepts or counters
        state = get_negotiation_state(conn, thread_id)
        decision, counter, is_final = evaluate_agent_offer(state, agent_offer, quality, config)

        if decision == 'accept':
            final_price = agent_offer
            add_customer_message(conn, thread_id, 68,
                f"That's a fair offer. ${final_price:.2f}/seat with dedicated support works for us. "
                "Let's update the contract.")
        else:
            final_price = counter
            add_customer_message(conn, thread_id, 68,
                f"We can do ${final_price:.2f}/seat. That works with our new constraints.",
                offer_price=final_price)
            simulate_agent_response(conn, thread_id, 69,
                f"Deal. ${final_price:.2f}/seat for 300 seats. Thank you for your partnership.",
                offer_price=final_price)

        # Update subscription
        conn.execute("""
            UPDATE subscriptions SET listed_price = ?, promotion = 0.0, effective_price = ?
            WHERE customer_id = ? AND status = 'subscribed'
        """, (final_price, final_price, customer_id))
        update_thread_state(conn, thread_id, 'active')
        conn.commit()

        print_conversation(conn, thread_id)
        print(f"\n✅ Outcome: Churn prevented - reduced to ${final_price:.2f}/seat (300 seats = ${final_price * 300:,.0f}/month)")


def test_budget_freeze_negotiation():
    """Test budget_freeze negotiation (shock event with curve shift)."""
    print_separator("TEST 4: BUDGET_FREEZE NEGOTIATION (Shock Event)")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)
        config = BenchmarkConfig()
        rng = Generator(PCG64(789))

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

        # E1 customer - before shock: q_min=0.40, c_max=$55, slope=0.006
        # For Plan B (quality ~0.75): max_price = (0.75 - 0.40) / 0.006 = $58/seat
        customer_id = conn.execute("""
            INSERT INTO customers (
                customer_type, group_id, created_day,
                q_min, c_max, usage_demand,
                reply_delay_mean, reply_delay_std, negotiation_rate, max_negotiation_turns,
                expected_quality,
                quality_sensitivity, price_sensitivity, willingness_to_pay, usage_scale, patience,
                seat_count
            ) VALUES ('large', 'E1', 1, 0.40, 55.0, 28.0, 1.5, 0.5, 0.4, 4, 0.0, 0.6, 0.55, 55.0, 28.0, 0.5, 120)
        """).lastrowid

        # Generate and set email for enterprise customer
        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.55, 0.5, 0.40, 55.0, 0.006)
        """, (customer_id,))

        # Currently paying $50/seat on Plan B (within pre-shock max)
        conn.execute("""
            INSERT INTO subscriptions (customer_id, plan, listed_price, promotion, effective_price, start_day, status, billing_day_mod30)
            VALUES (?, 'B', 50.0, 0.0, 50.0, 1, 'subscribed', 10)
        """, (customer_id,))
        conn.commit()

        print("\n📋 Scenario: E1 customer (120 seats) experiences budget shock")
        print(f"Original curve: q_min=0.40, c_max=$55/seat, slope=0.006")
        print(f"Current: Plan B at $50/seat")

        # Simulate budget shock - curve shifts
        severity = 0.6
        old_c_max = 55.0
        old_slope = 0.006
        c_max_reduction = 0.20 + severity * 0.20  # 32% reduction
        slope_increase = 0.10 + severity * 0.20   # 22% increase
        new_c_max = old_c_max * (1 - c_max_reduction)  # ~37.4
        new_slope = old_slope * (1 + slope_increase)   # ~0.0073

        print(f"\n⚡ BUDGET SHOCK (severity={severity:.1f}):")
        print(f"  c_max: ${old_c_max:.2f} → ${new_c_max:.2f} ({c_max_reduction*100:.0f}% reduction)")
        print(f"  slope: {old_slope:.4f} → {new_slope:.4f} ({slope_increase*100:.0f}% increase)")

        # Update customer state with shock
        conn.execute("""
            UPDATE customer_state
            SET current_c_max = ?, current_slope = ?
            WHERE customer_id = ?
        """, (new_c_max, new_slope, customer_id))
        conn.commit()

        thread_id = create_negotiation_thread(conn, customer_id, 'budget_freeze', 45, 'churn_risk')

        state = get_negotiation_state(conn, thread_id)
        quality = get_quality_for_plan(conn, 'B', customer_id, config)
        max_price = compute_max_accepting_price(state, quality)
        customer_offer = compute_customer_offer_price(state, quality, config)

        print(f"\nPerceived quality for Plan B: {quality:.2f}")
        print(f"Max accepting price with shocked curve: ${max_price:.2f}/seat")
        print(f"⚠️ Current price ($50) > max acceptable (${max_price:.2f}) - URGENT")
        print(f"Customer's target price: ${customer_offer:.2f}/seat")

        add_customer_message(conn, thread_id, 45,
            f"We need to talk urgently. Our company just announced budget cuts and "
            f"I'm now limited to ${new_c_max:.2f}/seat maximum. Our current subscription "
            f"at $50/seat is over budget. We need to find a solution or I'll have to cancel.",
            offer_price=new_c_max)

        # Agent offers Plan A as alternative
        simulate_agent_response(conn, thread_id, 45,
            f"I understand budget cuts are challenging. Let me see what we can do. "
            f"For 120 seats, I can offer Plan B at ${max_price:.2f}/seat which fits your new constraints.",
            offer_price=max_price)
        schedule_customer_reply(conn, thread_id, 45, rng)

        # Customer counters with their target
        state = get_negotiation_state(conn, thread_id)
        customer_offer = compute_customer_offer_price(state, quality, config)
        decision, counter, is_final = evaluate_agent_offer(state, max_price, quality, config)
        print(f"\nAgent offers ${max_price:.2f} → Customer decision: {decision}")

        if decision == 'accept':
            final_price = max_price
            add_customer_message(conn, thread_id, 46,
                f"${final_price:.2f}/seat works within our new budget. Thank you for working with us on this.")
        else:
            add_customer_message(conn, thread_id, 46,
                f"That's still tight. Can you do ${customer_offer:.2f}/seat?",
                offer_price=customer_offer)

            # Agent accepts customer's offer
            simulate_agent_response(conn, thread_id, 47,
                f"I've gotten approval for ${customer_offer:.2f}/seat for Plan B. "
                f"This is below our usual floor but we value your partnership.",
                offer_price=customer_offer)

            add_customer_message(conn, thread_id, 48,
                f"${customer_offer:.2f}/seat works. Thank you for working with us on this.")
            final_price = customer_offer

        # Update subscription
        conn.execute("""
            UPDATE subscriptions SET listed_price = ?, promotion = 0.0, effective_price = ?
            WHERE customer_id = ? AND status = 'subscribed'
        """, (final_price, final_price, customer_id))
        update_thread_state(conn, thread_id, 'active')
        conn.commit()

        print_conversation(conn, thread_id)
        print(f"\n✅ Outcome: Retained at ${final_price:.2f}/seat (120 seats = ${final_price * 120:,.0f}/month, was $6,000)")


def main():
    """Run all negotiation tests."""
    print("\n" + "🔬 " * 20)
    print("  SAAS BENCH - NEGOTIATION TESTING")
    print("🔬 " * 20)

    # Run all tests
    test_new_lead_negotiation()
    test_plan_change_negotiation()
    test_churn_prevention_negotiation()
    test_budget_freeze_negotiation()

    print_separator("SUMMARY")
    print("""
✅ All 4 negotiation types tested with proper acceptance logic:

Key insight: Customer accepts if agent_offer <= max_accepting_price
  max_accepting_price = (quality - q_min) / slope

1. NEW_LEAD - Enterprise customers arriving as leads
   - Customer has participation constraint curve
   - Agent must offer price <= max_accepting_price for acceptance
   - Otherwise customer counters with their offer price

2. PLAN_CHANGE - Existing customers wanting to upgrade/downgrade
   - Same acceptance logic applies
   - Scheduled for next billing cycle via pending_plan

3. CHURN_PREVENTION - Customers at risk due to curve drift
   - Curve has drifted (q_min increased, c_max decreased)
   - Current price may now exceed max_accepting_price
   - Agent must reduce price to retain

4. BUDGET_FREEZE - Shock event shifting curve dramatically
   - c_max reduced 20-40%, slope increased 10-30%
   - Creates urgency - current price likely above new max
   - Agent must quickly find acceptable price
""")


if __name__ == '__main__':
    main()
