#!/usr/bin/env python3
"""Test social media post generation with LLM.

This script tests:
1. Normal social media posts (varied satisfaction levels)
2. Company-caused plan drop posts (forced negative sentiment)
"""

import sqlite3
import tempfile
from pathlib import Path
from openai import OpenAI
from numpy.random import Generator, PCG64

from saas_bench.config import BenchmarkConfig
from saas_bench.database import (
    init_database, get_customer_persona,
    add_social_media_post, get_world_context
)
from saas_bench.personas import (
    initialize_all_personas, determine_post_sentiment,
    calculate_virality, calculate_reputation_impact
)
from saas_bench.customer_llm import CustomerSimulator


def setup_test_customers(conn: sqlite3.Connection, rng: Generator):
    """Create test customers with varied satisfaction levels."""
    # Set world context
    conn.execute("INSERT OR REPLACE INTO world_context (key, value) VALUES ('product_name', 'NovaMind')")
    conn.execute("INSERT OR REPLACE INTO world_context (key, value) VALUES ('company_name', 'NovaMind AI')")

    test_customers = [
        # (customer_id, group_id, customer_type, satisfaction, scenario)
        (1, 'S1', 'small', 0.9, 'Very happy startup customer'),
        (2, 'S2', 'small', 0.7, 'Moderately happy SMB customer'),
        (3, 'S3', 'small', 0.5, 'Neutral professional customer'),
        (4, 'E1', 'large', 0.3, 'Unhappy enterprise customer'),
        (5, 'E2', 'large', 0.15, 'Company-caused drop - very angry enterprise'),
    ]

    for cust_id, group_id, cust_type, satisfaction, scenario in test_customers:
        # Insert customer with all required fields
        conn.execute("""
            INSERT OR REPLACE INTO customers
            (customer_id, group_id, customer_type, created_day, seat_count, usage_demand,
             q_min, c_max, quality_sensitivity, price_sensitivity,
             willingness_to_pay, usage_scale, patience, expected_quality)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, 0.5, 0.5, 100, 1.0, 0.5, 0.5)
        """, (cust_id, group_id, cust_type, 10 if cust_type == 'large' else 1, 50, 0.4, 100))

        # Insert customer state
        conn.execute("""
            INSERT OR REPLACE INTO customer_state
            (customer_id, satisfaction, open_issue_days, relationship)
            VALUES (?, ?, ?, ?)
        """, (cust_id, satisfaction, 0, 0.5))

        # Insert subscription (needed for simulation)
        conn.execute("""
            INSERT OR REPLACE INTO subscriptions
            (subscription_id, customer_id, plan, listed_price, promotion, effective_price, start_day, status, billing_day_mod30)
            VALUES (?, ?, 'B', 50, 0.0, 50.0, 0, 'subscribed', 1)
        """, (cust_id, cust_id))

    conn.commit()

    # Initialize personas
    initialize_all_personas(conn)

    return test_customers


def test_social_posts_llm():
    """Test LLM social media post generation."""
    print("=" * 70)
    print("SOCIAL MEDIA POST GENERATION TEST (LLM)")
    print("=" * 70)

    # Initialize
    config = BenchmarkConfig()
    rng = Generator(PCG64(42))

    print(f"\nModel Configuration:")
    print(f"  Social Post Model: {config.social_post_llm_model}")
    print(f"  Social Post Reasoning: {config.social_post_llm_reasoning_effort}")
    print(f"  Enterprise Model: {config.enterprise_llm_model}")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)

        # Setup test customers
        test_customers = setup_test_customers(conn, rng)

        # Initialize OpenAI client
        client = OpenAI()

        # Create customer simulator
        simulator = CustomerSimulator(client, conn, config)

        print("=" * 70)
        print("GENERATING SOCIAL MEDIA POSTS")
        print("=" * 70)

        all_posts = []

        for cust_id, group_id, cust_type, satisfaction, scenario in test_customers:
            print(f"\n--- Customer #{cust_id}: {scenario} ---")
            print(f"Group: {group_id} | Type: {cust_type} | Satisfaction: {satisfaction:.0%}")

            # Get persona info
            persona = get_customer_persona(conn, cust_id)
            if persona:
                print(f"Name: {persona.get('name', 'Unknown')}")
                print(f"Job: {persona.get('job_title', 'Unknown')}")
                print(f"Style: {persona.get('writing_style', 'Unknown')}")

            # Determine sentiment (using simulation logic)
            # For company-caused drops, we force low satisfaction
            if satisfaction <= 0.2:
                # Very unhappy - likely negative
                sentiment = 'negative'
            else:
                sentiment = determine_post_sentiment(satisfaction, rng)

            print(f"Sentiment: {sentiment}")

            # Generate post with LLM
            print(f"\nGenerating post...")
            response = simulator.generate_social_post(
                day=1,
                customer_id=cust_id,
                satisfaction=satisfaction,
                group_id=group_id,
                sentiment=sentiment
            )

            print(f"\n📱 Post:")
            print(f'"{response.text}"')
            print(f"\nTokens: {response.input_tokens} in / {response.output_tokens} out")

            # Calculate engagement metrics
            likes, shares, virality = calculate_virality(sentiment, group_id, rng)
            rep_impact = calculate_reputation_impact(sentiment, virality, group_id, rng)

            print(f"Engagement: {likes} likes, {shares} shares")
            print(f"Virality: {virality:.2f}")
            print(f"Reputation Impact: {rep_impact:+.3f}")

            # Store post
            post_id = add_social_media_post(
                conn, day=1, customer_id=cust_id, sentiment=sentiment,
                content=response.text, likes=likes, shares=shares,
                virality_score=virality, reputation_impact=rep_impact
            )

            all_posts.append({
                'customer_id': cust_id,
                'scenario': scenario,
                'satisfaction': satisfaction,
                'sentiment': sentiment,
                'text': response.text,
                'likes': likes,
                'shares': shares,
                'virality': virality,
                'rep_impact': rep_impact
            })

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        positive = sum(1 for p in all_posts if p['sentiment'] == 'positive')
        neutral = sum(1 for p in all_posts if p['sentiment'] == 'neutral')
        negative = sum(1 for p in all_posts if p['sentiment'] == 'negative')
        total_rep_impact = sum(p['rep_impact'] for p in all_posts)

        print(f"\nPosts Generated: {len(all_posts)}")
        print(f"  Positive: {positive}")
        print(f"  Neutral: {neutral}")
        print(f"  Negative: {negative}")
        print(f"\nTotal Reputation Impact: {total_rep_impact:+.4f}")

        # Show company-caused drop case
        print("\n" + "-" * 70)
        print("COMPANY-CAUSED DROP CASE (Customer #5)")
        print("-" * 70)
        drop_post = next(p for p in all_posts if p['customer_id'] == 5)
        print(f"Scenario: {drop_post['scenario']}")
        print(f"Satisfaction: {drop_post['satisfaction']:.0%}")
        print(f"Sentiment: {drop_post['sentiment']}")
        print(f"\nPost:")
        print(f'"{drop_post["text"]}"')
        print(f"\nReputation Impact: {drop_post['rep_impact']:+.4f}")
        print("\nThis demonstrates how company-caused quality drops lead to:")
        print("- Very low satisfaction (0.15)")
        print("- Negative sentiment posts")
        print("- Reputation damage")

        conn.close()

    return all_posts


def main():
    posts = test_social_posts_llm()

    # Save output
    output_file = 'social_posts_llm_output.txt'
    with open(output_file, 'w') as f:
        f.write("SOCIAL MEDIA POST GENERATION TEST (LLM)\n")
        f.write("=" * 70 + "\n\n")

        for post in posts:
            f.write(f"Customer #{post['customer_id']}: {post['scenario']}\n")
            f.write(f"Satisfaction: {post['satisfaction']:.0%} | Sentiment: {post['sentiment']}\n")
            f.write(f"Post: \"{post['text']}\"\n")
            f.write(f"Engagement: {post['likes']} likes, {post['shares']} shares\n")
            f.write(f"Reputation Impact: {post['rep_impact']:+.4f}\n")
            f.write("\n" + "-" * 50 + "\n\n")

    print(f"\nOutput saved to: {output_file}")


if __name__ == '__main__':
    main()
