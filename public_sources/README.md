# CEOBench — Agent Instructions

You are the CEO of NovaMind AI. Your job: run the company for **500 simulated
days** and end with as much cash as possible. Final cash on day 500 is your
score.

You drive the simulator entirely through the `./novamind-operation` CLI in this
directory. There is no other interface.

---

## 1. Install

```bash
pip install -r requirements.txt
```

That's it. The simulator engine is bundled inside `novamind-operation` (a
zipapp); `requirements.txt` only installs the third-party libraries the engine
imports at runtime (`numpy`, `pandas`, `scikit-learn`, `openai`, `anthropic`,
`sqlcipher3-binary`, `python-dotenv`).

Requires Python 3.13+.

---

## 2. Read the docs first

Before making any decisions, read these in order:

1. `docs/simulator-instructions.md` — game mechanics, customer segments,
   pricing/marketing/R&D rules, scoring.
2. `docs/tools-reference.md` — every tool you can call, with arguments.
3. `docs/tables-reference.md` — database schema (use this when querying).
4. `docs/cli-reference.md` — full CLI surface.

Working examples live in `docs/examples/`.

---

## 3. Start the run

```bash
./novamind-operation new-session --days 500 --seed 42
```

This creates a fresh session and prints a `session_id`. All subsequent commands
default to the latest session.

---

## 4. The weekly loop

You operate the company in 1-week steps. **Each iteration:**

1. **Inspect.** Look at the current dashboard / query the DB:
   ```bash
   ./novamind-operation status
   ./novamind-operation query "SELECT day, COUNT(*) FROM subscriptions WHERE status='active' GROUP BY day ORDER BY day DESC LIMIT 5"
   ```

2. **Decide.** Set prices, ad spend, ops/dev spend, R&D, enterprise deals, etc.
   ```bash
   ./novamind-operation call set_prices --args '{"A": 25, "B": 69, "C": 179}'
   ./novamind-operation call set_daily_spend --args '{"operations": 2000, "development": 3000}'
   ./novamind-operation call set_targeted_ad_spend --args '{"targeted_spend": {"linkedin": {"E1": 1500}, "search_ads": {"S1": 1500}}}'
   ```
   Or run a Python strategy script:
   ```bash
   ./novamind-operation python my_week_plan.py
   ```

3. **Forecast & advance.** `next-week` advances 7 days. It requires three cash
   predictions (1 week, 4 weeks, 12 weeks ahead). Predictions are scored on
   percent error against actual cash at each horizon.
   ```bash
   ./novamind-operation next-week 1050000 1200000 1800000
   ```

Repeat for **72 weeks** to cover 500 days.

---

## 5. When you're done

After day 500 the session ends. Your final score is total cash:

```bash
./novamind-operation query "SELECT COALESCE(SUM(amount), 0) AS final_cash FROM ledger"
```

That number is what you're optimizing.

---

## Tips

- `./novamind-operation history` shows every action you've taken.
- `./novamind-operation call <tool> --args '{...}'` is the most direct way to
  use a single tool. Use the Python interface (`novamind_api`) when you want
  to compose logic.
- The `world.nmdb` ledger is encrypted — you cannot peek ahead. You must learn
  the world by acting in it.
- Cash on hand at any day = running sum of `ledger.amount`. Subscriptions, ad
  spend, ops/dev spend, R&D, enterprise deals all flow through this single
  table.
