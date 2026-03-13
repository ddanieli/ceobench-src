#!/usr/bin/env python3
"""Test all negotiation cases with ACTUAL LLM calls using GPT-5.2.

This test runs real LLM-generated conversations for all 4 negotiation types:
1. NEW_LEAD - Enterprise customers arriving as leads requiring sales negotiation
2. PLAN_CHANGE - Existing customers wanting to upgrade/downgrade
3. CHURN_PREVENTION - Customers at risk due to satisfaction dropping
4. BUDGET_FREEZE - Shock event shifting customer's cost-quality curve

Uses GPT-5.2 with the Responses API for both customer and agent messages.
"""

import os
import sqlite3
import json
import tempfile
from pathlib import Path
from numpy.random import Generator, PCG64
from openai import OpenAI

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.config import BenchmarkConfig, CUSTOMER_GROUPS
from saas_bench.database import init_database, add_ledger_entry, add_api_cost
from saas_bench.enterprise import (
    create_negotiation_thread, add_customer_message, get_negotiation_state,
    compute_customer_offer_price, compute_max_accepting_price, get_quality_for_plan,
    schedule_customer_reply, update_thread_state, evaluate_agent_offer,
    generate_enterprise_email
)


# Model settings - loaded from BenchmarkConfig
# Default: gpt-5.2 with low reasoning effort
# Change in config.py: agent_llm_model, agent_llm_reasoning_effort


def print_separator(title: str):
    """Print a separator with title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_conversation(conn: sqlite3.Connection, thread_id: int):
    """Print the full conversation history for a thread."""
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

        email_str = f" <{msg['email']}>" if msg['email'] else ""
        print(f"\nDay {msg['day']} - {sender_icon} {msg['sender'].upper()}{email_str}{offer_str}")
        print(f"  \"{msg['text']}\"")

    print("-" * 60)


def add_agent_message(conn: sqlite3.Connection, thread_id: int, day: int,
                      text: str, offer_price: float = None):
    """Add an agent message to a thread."""
    offer_json = json.dumps({'price': offer_price}) if offer_price else None
    conn.execute("""
        INSERT INTO messages (day, thread_id, sender, text, offer_json)
        VALUES (?, ?, 'agent', ?, ?)
    """, (day, thread_id, text, offer_json))
    conn.commit()


def generate_agent_reply_llm(client: OpenAI, thread_history: list, customer_info: dict,
                              negotiation_context: str, max_price: float,
                              config: BenchmarkConfig) -> tuple:
    """Generate an agent reply using LLM Responses API.

    Returns: (message_text, offer_price or None)
    """
    # Format history for prompt
    history_text = "\n".join([
        f"[Day {m['day']}] {m['sender'].upper()}: {m['text']}"
        for m in thread_history
    ])

    system_prompt = """You are an AI sales agent for NovaMind, an AI SaaS company.
You are negotiating with an enterprise customer. Be professional, helpful, and try to close deals.

IMPORTANT RULES:
1. Always be respectful and professional
2. Try to find a price that works for both parties
3. You can offer discounts but stay above your floor price
4. Keep messages concise (2-4 sentences)

Output JSON with:
- message: Your reply text (string)
- offer_price: Price per seat you're offering (number or null if not making an offer)
"""

    user_prompt = f"""Customer Info:
- Company size: {customer_info.get('seat_count', 100)} seats
- Group: {customer_info.get('group_id', 'E1')}
- Email: {customer_info.get('email', 'unknown')}

Negotiation Context: {negotiation_context}
Customer's max acceptable price (hidden from customer): ${max_price:.2f}/seat

Conversation History:
{history_text}

Generate your next reply as the sales agent."""

    # Use Responses API with config settings
    response = client.responses.create(
        model=config.agent_llm_model,
        input=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        reasoning={"effort": config.agent_llm_reasoning_effort},
        text={"format": {"type": "json_object"}}
    )

    content = response.output_text
    try:
        parsed = json.loads(content)
        return parsed.get('message', content), parsed.get('offer_price')
    except:
        return content, None


def generate_customer_reply_llm(client: OpenAI, thread_history: list, customer_info: dict,
                                 negotiation_context: str, customer_target_price: float,
                                 max_accepting_price: float, config: BenchmarkConfig,
                                 agent_offer: float = None) -> tuple:
    """Generate a customer reply using LLM Responses API.

    Returns: (message_text, counter_offer_price or None, accepts_deal: bool)
    """
    history_text = "\n".join([
        f"[Day {m['day']}] {m['sender'].upper()}: {m['text']}"
        for m in thread_history
    ])

    # Determine if customer should accept based on participation constraint
    should_accept = agent_offer is not None and agent_offer <= max_accepting_price

    system_prompt = f"""You are simulating an enterprise customer negotiating with an AI SaaS vendor.
You are professional but firm about your budget constraints.

YOUR CONSTRAINTS (hidden from vendor):
- Your target price: ${customer_target_price:.2f}/seat
- Maximum you can accept: ${max_accepting_price:.2f}/seat
- Any offer at or below ${max_accepting_price:.2f}/seat is acceptable to you

BEHAVIOR RULES:
1. If the vendor offers ${max_accepting_price:.2f}/seat or less, you should ACCEPT
2. If the vendor's offer is above your max, counter with a price closer to your target
3. Be professional and realistic
4. Keep messages concise (2-3 sentences)

Output JSON with:
- message: Your reply text (string)
- counter_offer: Your counter-offer price (number or null if accepting)
- accepts: true if accepting the deal, false otherwise
"""

    accept_hint = ""
    if should_accept:
        accept_hint = f"\n\nNOTE: The vendor's last offer of ${agent_offer:.2f}/seat is within your acceptable range. You should accept this deal."

    user_prompt = f"""Your Company Info:
- Size: {customer_info.get('seat_count', 100)} seats
- Budget constraint: ${max_accepting_price:.2f}/seat maximum

Negotiation Context: {negotiation_context}

Conversation History:
{history_text}{accept_hint}

Generate your next reply as the customer."""

    # Use Responses API with config settings
    response = client.responses.create(
        model=config.agent_llm_model,
        input=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        reasoning={"effort": config.agent_llm_reasoning_effort},
        text={"format": {"type": "json_object"}}
    )

    content = response.output_text
    try:
        parsed = json.loads(content)
        return (
            parsed.get('message', content),
            parsed.get('counter_offer'),
            parsed.get('accepts', False)
        )
    except:
        return content, None, False


def run_negotiation_with_llm(conn: sqlite3.Connection, client: OpenAI,
                              thread_id: int, customer_info: dict,
                              negotiation_context: str, config: BenchmarkConfig,
                              max_turns: int = 5) -> dict:
    """Run a full negotiation with LLM-generated messages.

    Returns dict with outcome info.
    """
    state = get_negotiation_state(conn, thread_id)
    quality = get_quality_for_plan(conn, 'B', customer_info['customer_id'], config)
    max_price = compute_max_accepting_price(state, quality)
    target_price = compute_customer_offer_price(state, quality, config)

    print(f"\n📊 Negotiation Parameters:")
    print(f"  Quality for Plan B: {quality:.2f}")
    print(f"  Customer's max accepting price: ${max_price:.2f}/seat")
    print(f"  Customer's target price: ${target_price:.2f}/seat")

    day = 1
    last_agent_offer = None

    for turn in range(max_turns):
        # Get conversation history
        messages = conn.execute("""
            SELECT day, sender, text, offer_json
            FROM messages WHERE thread_id = ? ORDER BY message_id
        """, (thread_id,)).fetchall()

        history = [
            {
                'day': m['day'],
                'sender': m['sender'],
                'text': m['text'],
                'offer': json.loads(m['offer_json']) if m['offer_json'] else None
            }
            for m in messages
        ]

        # Agent turn
        day += 1
        print(f"\n🤖 Agent turn {turn + 1}...")
        agent_msg, agent_offer = generate_agent_reply_llm(
            client, history, customer_info, negotiation_context, max_price, config
        )

        if agent_offer:
            last_agent_offer = agent_offer

        add_agent_message(conn, thread_id, day, agent_msg, agent_offer)
        print(f"   Agent: \"{agent_msg}\"")
        if agent_offer:
            print(f"   Offer: ${agent_offer:.2f}/seat")

        # Update history
        history.append({
            'day': day,
            'sender': 'agent',
            'text': agent_msg,
            'offer': {'price': agent_offer} if agent_offer else None
        })

        # Customer turn
        day += 1
        print(f"\n👤 Customer turn {turn + 1}...")
        cust_msg, counter_offer, accepts = generate_customer_reply_llm(
            client, history, customer_info, negotiation_context,
            target_price, max_price, config, last_agent_offer
        )

        if accepts:
            add_customer_message(conn, thread_id, day, cust_msg)
            print(f"   Customer: \"{cust_msg}\"")
            print(f"   ✅ DEAL ACCEPTED!")
            return {
                'outcome': 'accepted',
                'final_price': last_agent_offer,
                'turns': turn + 1
            }

        add_customer_message(conn, thread_id, day, cust_msg, counter_offer)
        print(f"   Customer: \"{cust_msg}\"")
        if counter_offer:
            print(f"   Counter: ${counter_offer:.2f}/seat")

    return {
        'outcome': 'no_deal',
        'final_price': None,
        'turns': max_turns
    }


def setup_test_db(tmpdir: str) -> tuple:
    """Set up test database and return (conn, config, rng)."""
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

    return conn, config, rng


def test_new_lead_llm(client: OpenAI):
    """Test NEW_LEAD negotiation with LLM."""
    print_separator("TEST 1: NEW_LEAD NEGOTIATION (GPT-5.2)")

    with tempfile.TemporaryDirectory() as tmpdir:
        conn, config, rng = setup_test_db(tmpdir)

        # Create enterprise customer
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

        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.5, 0.5, 0.50, 80.0, 0.003)
        """, (customer_id,))
        conn.commit()

        customer_info = {
            'customer_id': customer_id,
            'seat_count': 150,
            'group_id': 'E2',
            'email': email
        }

        print(f"\n📋 Scenario: New enterprise lead (E2 - Quality-First, 150 seats)")
        print(f"Customer: {email}")
        print(f"Curve: q_min=0.50, c_max=$80/seat, slope=0.003")

        # Create thread
        thread_id = create_negotiation_thread(conn, customer_id, 'new_lead', 1, 'lead')

        # Initial customer message (LLM generated)
        initial_msg, _, _ = generate_customer_reply_llm(
            client, [], customer_info,
            "You are a new enterprise lead interested in NovaMind's Plan B for your 150-person team.",
            60.0, 80.0, config, None
        )
        add_customer_message(conn, thread_id, 1, initial_msg)

        # Run negotiation
        result = run_negotiation_with_llm(
            conn, client, thread_id, customer_info,
            "New enterprise lead negotiation for Plan B",
            config, max_turns=4
        )

        print_conversation(conn, thread_id)

        if result['outcome'] == 'accepted':
            print(f"\n✅ Outcome: Deal closed at ${result['final_price']:.2f}/seat after {result['turns']} turns")
        else:
            print(f"\n❌ Outcome: No deal after {result['turns']} turns")


def test_plan_change_llm(client: OpenAI):
    """Test PLAN_CHANGE negotiation with LLM."""
    print_separator("TEST 2: PLAN_CHANGE NEGOTIATION (GPT-5.2)")

    with tempfile.TemporaryDirectory() as tmpdir:
        conn, config, rng = setup_test_db(tmpdir)

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

        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.65, 0.6, 0.45, 60.0, 0.005)
        """, (customer_id,))
        conn.commit()

        customer_info = {
            'customer_id': customer_id,
            'seat_count': 80,
            'group_id': 'E1',
            'email': email
        }

        print(f"\n📋 Scenario: Existing E1 customer (80 seats) upgrading A → B")
        print(f"Customer: {email}")
        print(f"Curve: q_min=0.45, c_max=$60/seat, slope=0.005")

        thread_id = create_negotiation_thread(conn, customer_id, 'plan_change', 30, 'evaluation')

        initial_msg, _, _ = generate_customer_reply_llm(
            client, [], customer_info,
            "You are an existing customer on Plan A wanting to upgrade to Plan B for your 80 seats.",
            45.0, 60.0, config, None
        )
        add_customer_message(conn, thread_id, 30, initial_msg)

        result = run_negotiation_with_llm(
            conn, client, thread_id, customer_info,
            "Plan upgrade negotiation from A to B",
            config, max_turns=4
        )

        print_conversation(conn, thread_id)

        if result['outcome'] == 'accepted':
            print(f"\n✅ Outcome: Upgrade deal at ${result['final_price']:.2f}/seat after {result['turns']} turns")
        else:
            print(f"\n❌ Outcome: No deal after {result['turns']} turns")


def test_churn_prevention_llm(client: OpenAI):
    """Test CHURN_PREVENTION negotiation with LLM."""
    print_separator("TEST 3: CHURN_PREVENTION NEGOTIATION (GPT-5.2)")

    with tempfile.TemporaryDirectory() as tmpdir:
        conn, config, rng = setup_test_db(tmpdir)

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

        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        # Drifted curve - customer now more demanding
        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.45, 0.55, 0.55, 65.0, 0.004)
        """, (customer_id,))
        conn.commit()

        customer_info = {
            'customer_id': customer_id,
            'seat_count': 300,
            'group_id': 'E3',
            'email': email
        }

        print(f"\n📋 Scenario: E3 customer (300 seats) at churn risk")
        print(f"Customer: {email}")
        print(f"Original curve: q_min=0.50, c_max=$70/seat, slope=0.003")
        print(f"Drifted curve: q_min=0.55, c_max=$65/seat, slope=0.004")
        print(f"⚠️ Current price ($60) exceeds new max - CHURN RISK")

        thread_id = create_negotiation_thread(conn, customer_id, 'churn_prevention', 60, 'churn_risk')

        initial_msg, _, _ = generate_customer_reply_llm(
            client, [], customer_info,
            "You are an unhappy customer considering cancellation. Current price of $60/seat no longer works for you.",
            36.0, 48.0, config, None
        )
        add_customer_message(conn, thread_id, 60, initial_msg)

        result = run_negotiation_with_llm(
            conn, client, thread_id, customer_info,
            "Churn prevention - customer unhappy with current value",
            config, max_turns=4
        )

        print_conversation(conn, thread_id)

        if result['outcome'] == 'accepted':
            print(f"\n✅ Outcome: Churn prevented at ${result['final_price']:.2f}/seat after {result['turns']} turns")
        else:
            print(f"\n❌ Outcome: Customer churned after {result['turns']} turns")


def test_budget_freeze_llm(client: OpenAI):
    """Test BUDGET_FREEZE negotiation with LLM."""
    print_separator("TEST 4: BUDGET_FREEZE NEGOTIATION (GPT-5.2)")

    with tempfile.TemporaryDirectory() as tmpdir:
        conn, config, rng = setup_test_db(tmpdir)

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

        email = generate_enterprise_email(customer_id, rng)
        conn.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (email, customer_id))

        # Apply budget shock - dramatic curve shift
        new_c_max = 37.40
        new_slope = 0.0073
        conn.execute("""
            INSERT INTO customer_state (customer_id, satisfaction, relationship, current_q_min, current_c_max, current_slope)
            VALUES (?, 0.55, 0.5, 0.40, ?, ?)
        """, (customer_id, new_c_max, new_slope))
        conn.commit()

        customer_info = {
            'customer_id': customer_id,
            'seat_count': 120,
            'group_id': 'E1',
            'email': email
        }

        print(f"\n📋 Scenario: E1 customer (120 seats) experiences budget shock")
        print(f"Customer: {email}")
        print(f"Original curve: q_min=0.40, c_max=$55/seat, slope=0.006")
        print(f"⚡ BUDGET SHOCK: c_max=$55→$37.40 (32% reduction)")
        print(f"Current price ($50) now exceeds max ($37.40) - URGENT")

        thread_id = create_negotiation_thread(conn, customer_id, 'budget_freeze', 45, 'churn_risk')

        initial_msg, _, _ = generate_customer_reply_llm(
            client, [], customer_info,
            f"Your company just announced budget cuts. Your new maximum budget is ${new_c_max:.2f}/seat. Current subscription at $50/seat is over budget - you need a solution urgently or you'll have to cancel.",
            28.0, new_c_max, config, None
        )
        add_customer_message(conn, thread_id, 45, initial_msg)

        result = run_negotiation_with_llm(
            conn, client, thread_id, customer_info,
            "Budget freeze emergency - company-wide budget cuts",
            config, max_turns=4
        )

        print_conversation(conn, thread_id)

        if result['outcome'] == 'accepted':
            print(f"\n✅ Outcome: Customer retained at ${result['final_price']:.2f}/seat after {result['turns']} turns")
        else:
            print(f"\n❌ Outcome: Customer lost after {result['turns']} turns")


def main():
    """Run all LLM-based negotiation tests."""
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key'")
        return

    client = OpenAI(api_key=api_key)
    config = BenchmarkConfig()

    print("\n" + "🔬 " * 20)
    print("  SAAS BENCH - LLM NEGOTIATION TESTING")
    print(f"  Environment LLM: {config.agent_llm_model} (reasoning: {config.agent_llm_reasoning_effort})")
    print(f"  Agent LLM: {config.agent_llm_model} (reasoning: {config.agent_llm_reasoning_effort})")
    print("🔬 " * 20)

    # Run all tests
    test_new_lead_llm(client)
    test_plan_change_llm(client)
    test_churn_prevention_llm(client)
    test_budget_freeze_llm(client)

    print_separator("SUMMARY")
    print(f"""
✅ All 4 negotiation types tested with LLM Responses API:

Environment LLM: {config.agent_llm_model} (reasoning: {config.agent_llm_reasoning_effort})
Agent LLM: {config.agent_llm_model} (reasoning: {config.agent_llm_reasoning_effort})

1. NEW_LEAD - LLM generates realistic sales conversation
2. PLAN_CHANGE - LLM handles upgrade negotiation
3. CHURN_PREVENTION - LLM simulates unhappy customer
4. BUDGET_FREEZE - LLM handles urgent budget crisis

Key: Customer accepts when agent_offer <= max_accepting_price
The LLM is instructed about the acceptance threshold to generate realistic behavior.

To change model settings, edit config.py:
  - agent_llm_model / agent_llm_reasoning_effort (for agent being benchmarked)
  - enterprise_llm_model / enterprise_llm_provider (for customer negotiation simulation)
  - social_post_llm_model / social_post_llm_provider (for customer social posts)
""")


if __name__ == '__main__':
    main()
