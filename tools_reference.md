# SaaS Bench — Complete Tools Reference

All tools available to the agent, organized by category. The agent interacts via three interfaces:
1. **API Tools** — Called via the tool-calling API (function calls)
2. **Python Library** — `novamind_api` (importable in `python_exec` and scripts)
3. **CLI** — `novamind-operation` and `novamind` shell commands

---

## Tool Summary (34 API tools + 4 CLI commands + 6 bash agent tools)

| Category | Count | Tools |
|----------|-------|-------|
| Business Configuration | 7 | set_prices, set_model_tiers, set_capacity_tier, set_usage_quotas, set_ads_strength, set_lead_promotion, set_promotion |
| Marketing & Spend | 5 | set_daily_spend, set_ad_channel_spend, set_targeted_ad_spend, set_targeted_ops_spend, set_targeted_dev_spend |
| Customer Communication | 2 | send_enterprise_deal, reject_enterprise_deal |
| Analytics & Monitoring | 3 | python_exec, get_social_posts, get_cost_info |
| Automation | 7 | register_daily_calculation, remove_daily_calculation, list_daily_calculations, register_script, run_script, list_scripts, delete_script |
| Market Discovery | 4 | research_market, research_group, get_market_overview, get_group_insights |
| R&D Research Projects | 2 | start_research_project, list_research_projects |
| Help & Documentation | 3 | list_all_tables, describe_tables, get_tool_documentation |
| Session Management | 1 | log_rationale |
| Simulation Control | 1 | next_day |
| Bash Agent Tools | 6 | bash, read_file, write_file, edit_file, search_files, glob_files |
| CLI Commands | 4 | ./novamind-operation next-day, novamind register-daily-script, novamind list-daily-scripts, novamind remove-daily-script |

---

## API Tools (by Category)

### Business Configuration

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `set_prices` | Set monthly subscription prices for plans A, B, and C | `A`, `B`, `C` (floats) |
| `set_model_tiers` | Set AI model tiers for plans A, B, C. Higher tiers = better quality but higher compute cost | `A`, `B`, `C` (integers) |
| `set_capacity_tier` | Set infrastructure capacity tier. Higher tiers handle more usage but cost more/day | `tier` (integer) |
| `set_usage_quotas` | Set daily usage quotas (rate limits) per customer for each plan | `A`, `B`, `C` (integers) |
| `set_ads_strength` | Set in-app ad strength (0–1). Generates revenue but reduces perceived quality. Log curve: small values already have large effect. Global/group/individual levels are additive, capped at 1.0 | `global_strength`, `group_strength` (dict), `customer_strength` (dict) |
| `set_lead_promotion` | Set dollar deduction for new leads (first billing only). Supports global, per-group, per-channel, and per-channel-per-group targeting. All additive | `global_promotion`, `group_promotion`, `channel_promotion`, `channel_group_promotion` |
| `set_promotion` | Set ongoing dollar deduction for existing subscribers. Applied each billing period. Additive across global/group/customer/group_plan levels | `global_promotion`, `group_promotion`, `customer_promotion`, `group_plan_promotion` |

### Marketing & Spend

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `set_daily_spend` | Set daily spending for advertising, operations, and development | `advertising`, `operations`, `development` (floats) |
| `set_ad_channel_spend` | Set per-channel ad budget allocation as percentages. Allows targeting specific customer groups | Channel names as kwargs with percentage values |
| `set_targeted_ad_spend` | Set ADDITIONAL per-group per-channel ad spend on top of overall channel allocation | `targeted_spend` (dict of group → channel → amount) |
| `set_targeted_ops_spend` | Set ADDITIONAL per-group operations spending. Adds extra issue resolution capacity per group | `targeted_spend` (dict of group → amount) |
| `set_targeted_dev_spend` | Set ADDITIONAL per-group dev spending. Provides CUMULATIVE per-group quality bonus that grows daily while spending continues. Persists after spending stops | `targeted_spend` (dict of group → amount) |

### Customer Communication

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `send_enterprise_deal` | Send enterprise deal offerings. Compact tuple format: `[customer_id, [[plan, price_per_seat, contract_months], ...]]`. Up to 3 offerings per deal. Late replies damage relationship (−0.02/day after 1-day grace). No response within 3 days = customer LOST FOREVER | `deals` (list of deal tuples) |
| `reject_enterprise_deal` | Reject enterprise deals by customer_id. New leads are lost; existing customers may churn | `deals` (list of customer_ids) |

### Analytics & Monitoring

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `python_exec` | Execute Python code for custom data analysis. Has read-only access to the full simulation database. Primary analytics tool for any analysis not covered by other tools | `code` (string) |
| `get_social_posts` | Search social media posts about your company. Sentiment is NOT provided — must be inferred from content | `days` (int, default 7), `limit` (int, default 50) |
| `get_cost_info` | Get current cost structure for compute and capacity. Shows model tier costs and capacity tier costs | (none) |

### Automation

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `register_daily_calculation` | Register a named calculation to run automatically at the start of each day. Output appears in dashboard | `name` (string), `code` (string) |
| `remove_daily_calculation` | Remove a registered daily calculation | `name` (string) |
| `list_daily_calculations` | List all registered daily calculations | (none) |
| `register_script` | Save a named Python script for later execution via `run_script`. Scripts persist across days | `name` (string), `code` (string) |
| `run_script` | Execute a previously registered script by name. Runs in same environment as `python_exec` | `name` (string) |
| `list_scripts` | List all registered scripts with code previews | (none) |
| `delete_script` | Delete a previously registered script | `name` (string) |

### Market Discovery

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `research_market` | Discover new customer segments. Costs $25,000/attempt, 30% success chance. Result is instant. Agent starts with 6 known groups (S1–S3, E1–E3); 20 additional to discover (10 individual, 10 enterprise) | (none) |
| `research_group` | Research a discovered group to reach a specific info level (2–5). Any level can be targeted directly. Takes several days; results delivered to inbox. Cost deducted immediately | `group_id` (string), `target_level` (int) |
| `get_market_overview` | Overview of all known segments, info levels, undiscovered count, and latest macroeconomic conditions (ISM PMI — published monthly with ~30 day delay) | (none) |
| `get_group_insights` | Get estimated parameters for a discovered group based on current info level. Returns noisy estimates that improve with higher levels. Attributes: willingness_to_pay, usage_volume, quality_floor_q_min, contract_lockin_aversion, market_cap, market_cap_growth. Enterprise groups also return seat_range, decision_rounds, avg_response_days. Estimates are deterministic | `group_id` (string) |

### R&D Research Projects

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `start_research_project` | Start an R&D research tier. Costs deducted immediately. Completes after sampled duration with sampled quality boost. Tiers are REPEATABLE. Only one invocation per tier can be in-progress at a time. Higher tiers = more expensive, bigger boosts, longer delays, higher variance | `tier` (integer) |
| `list_research_projects` | List all 10 R&D tiers with status, cost, duration range, quality range, in-progress invocations, and completion history | (none) |

### Help & Documentation

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_all_tables` | List all available database tables with descriptions. Quick overview of available data | (none) |
| `describe_tables` | Get descriptions of visible columns for specified tables. Returns column names, types, and descriptions | `tables` (list of table names) |
| `get_tool_documentation` | Get detailed documentation for environment tools including parameters, examples, and expected outputs | `tools` (list of tool names, or omit for all) |

### Session Management

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `log_rationale` | Log thinking/rationale for decisions. MUST be called EXACTLY ONCE per day, immediately before calling `next_day` | `rationale` (string) |

### Simulation Control

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `next_day` | Advance the simulation by one day and receive the next day's dashboard | (none) |

---

## Bash Agent Tools

These are the low-level tools available to the bash agent (separate from the simulation API tools above):

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `bash` | Execute a bash command in the agent working directory. Used to run `./novamind-operation` CLI commands and Python scripts | `command` (string) |
| `read_file` | Read file contents with optional offset/limit for large files | `path`, `offset`, `limit` |
| `write_file` | Create or overwrite a file with given content | `path`, `content` |
| `edit_file` | Edit an existing file by replacing `old_string` with `new_string` (must be unique) | `path`, `old_string`, `new_string` |
| `search_files` | Search file contents using regex (like grep). Returns matching lines with paths and line numbers | `pattern`, `path`, `glob` |
| `glob_files` | Find files matching a glob pattern | `pattern` |

---

## CLI Commands

### `novamind-operation` — Simulation Control

| Command | Description |
|---------|-------------|
| `./novamind-operation next-day` | Advance simulator to next day. Prints dashboard to stdout with key metrics, yesterday's results, and inbox notifications |

### `novamind` — Script Management

| Command | Description |
|---------|-------------|
| `novamind register-daily-script <path>` | Register a Python script to run automatically at the start of each day. Content is snapshotted at registration time |
| `novamind list-daily-scripts` | List all registered daily scripts with names and sizes |
| `novamind remove-daily-script <name>` | Remove a registered daily script |

---

## Python Library (`novamind_api`)

Available for import in `python_exec` code and registered scripts. Wraps the API tools as Python functions:

### Modules & Functions

| Module | Functions |
|--------|-----------|
| `novamind_api.pricing` | `set_prices(A, B, C)`, `set_model_tiers(A, B, C)`, `set_usage_quotas(A, B, C)`, `set_promotion(...)` |
| `novamind_api.marketing` | `set_daily_spend(...)`, `set_ad_channel_spend(...)`, `set_targeted_ad_spend(...)`, `set_ads_strength(...)`, `set_lead_promotion(...)` |
| `novamind_api.infrastructure` | `set_capacity_tier(tier)`, `get_cost_info()` |
| `novamind_api.enterprise` | `send_enterprise_deal(deals)`, `reject_enterprise_deal(deals)` |
| `novamind_api.analytics` | `get_social_posts(...)`, `set_targeted_ops_spend(...)`, `set_targeted_dev_spend(...)`, `log_rationale(...)` |
| `novamind_api.market` | `research_market()`, `research_group(group_id, target_level)`, `get_market_overview()`, `get_group_insights(group_id)` |
| `novamind_api.research` | `start_research_project(tier)`, `list_research_projects()` |
| `novamind_api._client` | `call(tool_name, args)`, `next_day()`, `query(sql)`, `get_vars()` |

### Special Variables in `python_exec` Environment

| Variable | Description |
|----------|-------------|
| `conn` | Read-only SQLite connection to the simulation database |
| `row(sql)` | Shortcut: execute SQL and return first row |
| `rows(sql)` | Shortcut: execute SQL and return all rows |
| `pd` | Pre-imported pandas |
| `novamind_api` | Pre-imported API library |
