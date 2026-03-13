"""Modal web app for selecting which DB columns to hide from the BossBench agent."""

import json
import modal

image = modal.Image.debian_slim(python_version="3.11").pip_install("fastapi[standard]")
app = modal.App("bossbench-column-picker", image=image)

# Volume to persist submissions
vol = modal.Volume.from_name("bossbench-column-picker-vol", create_if_missing=True)

SCHEMA = {
    "customers": {
        "desc": "Per-customer attributes",
        "columns": [
            ("customer_id", "INTEGER", "PK"),
            ("customer_type", "TEXT", "small/large"),
            ("group_id", "TEXT", "segment group"),
            ("created_day", "INTEGER", ""),
            ("q_max", "REAL", "⚠️ latent quality ceiling"),
            ("q_min", "REAL", "⚠️ latent quality floor"),
            ("contract_lockin_penalty", "REAL", ""),
            ("persona_industry", "TEXT", ""),
            ("persona_role", "TEXT", ""),
            ("persona_experience", "TEXT", ""),
            ("persona_work_style", "TEXT", ""),
            ("persona_tech_savvy", "TEXT", ""),
            ("company_size_descriptor", "TEXT", ""),
            ("company_culture", "TEXT", ""),
            ("company_decision_style", "TEXT", ""),
            ("company_primary_concern", "TEXT", ""),
            ("persona_description", "TEXT", ""),
            ("seat_count", "REAL", ""),
            ("email", "TEXT", ""),
            ("contract_start_day", "INTEGER", ""),
            ("acquisition_source", "TEXT", ""),
            ("ads_quality_sensitivity", "REAL", ""),
            ("ads_return_sensitivity", "REAL", ""),
        ],
    },
    "subscriptions": {
        "desc": "Active/cancelled subscriptions",
        "columns": [
            ("subscription_id", "INTEGER", "PK"),
            ("customer_id", "INTEGER", ""),
            ("plan", "TEXT", ""),
            ("listed_price", "REAL", ""),
            ("promotion", "REAL", ""),
            ("effective_price", "REAL", ""),
            ("effective_c_max", "REAL", "⚠️ willingness-to-pay at sub time"),
            ("start_day", "INTEGER", ""),
            ("end_day", "INTEGER", ""),
            ("status", "TEXT", ""),
            ("billing_day_mod30", "INTEGER", ""),
            ("pending_plan", "TEXT", ""),
            ("pending_price", "REAL", ""),
            ("seat_count", "INTEGER", ""),
            ("contract_months", "INTEGER", ""),
            ("contract_end_day", "INTEGER", ""),
            ("churn_reason", "TEXT", ""),
            ("first_billing_done", "INTEGER", ""),
        ],
    },
    "enterprise_turns": {
        "desc": "Negotiation threads",
        "columns": [
            ("message_id", "INTEGER", "PK"),
            ("thread_id", "INTEGER", ""),
            ("customer_id", "INTEGER", ""),
            ("thread_type", "TEXT", ""),
            ("turn_number", "INTEGER", ""),
            ("sender", "TEXT", ""),
            ("message_text", "TEXT", ""),
            ("offer_json", "TEXT", ""),
            ("day", "INTEGER", ""),
            ("email", "TEXT", ""),
            ("seat_count", "INTEGER", ""),
            ("closed", "INTEGER", ""),
            ("close_reason", "TEXT", ""),
        ],
    },
    "social_media_posts": {
        "desc": "Social media",
        "columns": [
            ("post_id", "INTEGER", "PK"),
            ("day", "INTEGER", ""),
            ("customer_id", "INTEGER", ""),
            ("content", "TEXT", ""),
            ("likes", "INTEGER", ""),
            ("shares", "INTEGER", ""),
            ("virality_score", "REAL", ""),
        ],
    },
    "ledger": {
        "desc": "Financial transactions",
        "columns": [
            ("id", "INTEGER", "PK"),
            ("day", "INTEGER", ""),
            ("category", "TEXT", ""),
            ("amount", "REAL", ""),
            ("note", "TEXT", ""),
        ],
    },
    "daily_usage": {
        "desc": "Daily usage per customer",
        "columns": [
            ("day", "INTEGER", ""),
            ("customer_id", "INTEGER", ""),
            ("usage_units", "INTEGER", ""),
        ],
    },
    "config_history": {
        "desc": "Pricing/capacity config changes",
        "columns": [
            ("day", "INTEGER", ""),
            ("price_A", "REAL", ""),
            ("price_B", "REAL", ""),
            ("price_C", "REAL", ""),
            ("tier_A", "INTEGER", ""),
            ("tier_B", "INTEGER", ""),
            ("tier_C", "INTEGER", ""),
            ("spend_advertising", "REAL", ""),
            ("spend_operations", "REAL", ""),
            ("spend_development", "REAL", ""),
            ("capacity_tier", "INTEGER", ""),
            ("ad_spend_social_media", "REAL", ""),
            ("ad_spend_search_ads", "REAL", ""),
            ("ad_spend_linkedin", "REAL", ""),
            ("ad_spend_content_marketing", "REAL", ""),
            ("ad_spend_referral_program", "REAL", ""),
            ("quota_A", "INTEGER", ""),
            ("quota_B", "INTEGER", ""),
            ("quota_C", "INTEGER", ""),
        ],
    },
    "service_day": {
        "desc": "Daily service metrics",
        "columns": [
            ("day", "INTEGER", ""),
            ("total_usage_units", "INTEGER", ""),
            ("p95_ms", "REAL", ""),
            ("error_rate", "REAL", ""),
            ("downtime_minutes", "INTEGER", ""),
            ("capacity_tier", "INTEGER", ""),
            ("capacity_units", "INTEGER", ""),
        ],
    },
    "research_projects": {
        "desc": "R&D projects",
        "columns": [
            ("project_id", "TEXT", "PK"),
            ("tier", "INTEGER", ""),
            ("status", "TEXT", ""),
            ("started_day", "INTEGER", ""),
            ("expected_completion_day", "INTEGER", ""),
            ("expected_quality_boost", "REAL", ""),
            ("quality_boost_applied", "REAL", ""),
            ("current_decay_reduction", "REAL", ""),
            ("decay_reduction_expiry_day", "INTEGER", ""),
        ],
    },
    "issues": {
        "desc": "Customer support issues",
        "columns": [
            ("issue_id", "INTEGER", "PK"),
            ("customer_id", "INTEGER", ""),
            ("group_id", "TEXT", ""),
            ("open_day", "INTEGER", ""),
            ("days_open", "INTEGER", ""),
            ("status", "TEXT", ""),
            ("resolved_day", "INTEGER", ""),
            ("resolution_type", "TEXT", ""),
        ],
    },
    "notifications": {
        "desc": "System notifications",
        "columns": [
            ("notification_id", "INTEGER", "PK"),
            ("day", "INTEGER", ""),
            ("type", "TEXT", ""),
            ("message", "TEXT", ""),
        ],
    },
    "macroeconomic_conditions": {
        "desc": "PMI/macro data",
        "columns": [
            ("day", "INTEGER", ""),
            ("pmi_value", "REAL", ""),
            ("pmi_trend", "TEXT", ""),
            ("pmi_change", "REAL", ""),
            ("cycle_phase", "TEXT", ""),
            ("description", "TEXT", ""),
        ],
    },
    "competitor_events": {
        "desc": "Competitor actions",
        "columns": [
            ("event_id", "INTEGER", "PK"),
            ("start_day", "INTEGER", ""),
            ("boost_amount", "REAL", ""),
            ("post_end_day", "INTEGER", ""),
            ("description", "TEXT", ""),
            ("applied", "INTEGER", ""),
        ],
    },
    "ads_revenue": {
        "desc": "Ad revenue per customer",
        "columns": [
            ("day", "INTEGER", ""),
            ("customer_id", "INTEGER", ""),
            ("group_id", "TEXT", ""),
            ("ads_strength", "REAL", ""),
            ("sensitivity", "REAL", ""),
            ("seat_count", "INTEGER", ""),
            ("revenue", "REAL", ""),
        ],
    },
    "ad_channel_leads": {
        "desc": "Leads per ad channel",
        "columns": [
            ("id", "INTEGER", "PK"),
            ("day", "INTEGER", ""),
            ("channel_id", "TEXT", ""),
            ("group_id", "TEXT", ""),
            ("leads_generated", "INTEGER", ""),
            ("spend", "REAL", ""),
        ],
    },
    "config_overrides": {
        "desc": "Tool config overrides",
        "columns": [
            ("id", "INTEGER", "PK"),
            ("day", "INTEGER", ""),
            ("tool_name", "TEXT", ""),
            ("setting_type", "TEXT", ""),
            ("settings_json", "TEXT", ""),
        ],
    },
    "segment_discovery": {
        "desc": "Market research attempts",
        "columns": [
            ("id", "INTEGER", "PK"),
            ("day", "INTEGER", ""),
            ("cost", "REAL", ""),
            ("success", "INTEGER", ""),
            ("discovered_group_id", "TEXT", ""),
            ("remaining_undiscovered", "INTEGER", ""),
        ],
    },
    "group_info_levels": {
        "desc": "Research levels per group",
        "columns": [
            ("group_id", "TEXT", "PK"),
            ("info_level", "INTEGER", ""),
            ("is_discoverable", "INTEGER", ""),
            ("discovered_day", "INTEGER", ""),
            ("last_research_day", "INTEGER", ""),
        ],
    },
}

ALREADY_HIDDEN = [
    "c_max", "steepness_left", "steepness_right",
    "usage_demand", "quality_sensitivity", "price_sensitivity",
    "willingness_to_pay", "usage_scale", "patience",
    "reply_delay_mean", "reply_delay_std", "negotiation_rate", "max_negotiation_turns",
    "next_reply_day", "current_offer_price",
    "daily_usage_rate", "billing_period_usage",
    "satisfaction", "relationship", "open_issue_days",
    "current_steepness_left", "current_steepness_right", "current_c_max", "current_slope",
    "last_drift_day", "plan_was_acceptable", "last_quality", "last_satisfaction", "shock_event_id",
    "reputation", "awareness", "last_updated_day", "last_marketing_day",
    "change_reason", "actual_completion_day", "initial_offer_factor",
    "persona_communication", "_internal_status",
    "sentiment", "reputation_impact", "influence_score",
]

HIDDEN_TABLES = [
    "api_costs", "customer_persona_map", "customer_personas", "customer_state",
    "enterprise_thread_counter", "events", "feature_tests", "global_state",
    "group_awareness", "group_characteristics", "group_parameters",
    "group_reputation", "pending_group_research", "reputation_history",
    "test_assignments", "world_context",
]


def build_html():
    """Build the HTML page with checkboxes."""
    rows_html = ""
    for table_name, table_info in SCHEMA.items():
        rows_html += f"""
        <div class="table-section">
            <div class="table-header" onclick="toggleTable('{table_name}')">
                <span class="arrow" id="arrow-{table_name}">▼</span>
                <code>{table_name}</code>
                <span class="table-desc">— {table_info['desc']}</span>
                <span class="col-count" id="count-{table_name}">0 selected</span>
            </div>
            <div class="table-cols" id="cols-{table_name}">
        """
        for col_name, col_type, note in table_info["columns"]:
            warn_class = "warn" if "⚠️" in note else ""
            note_html = f'<span class="note {warn_class}">{note}</span>' if note else ""
            rows_html += f"""
                <label class="col-row">
                    <input type="checkbox" name="col" value="{table_name}.{col_name}"
                           onchange="updateCount('{table_name}')" />
                    <code class="col-name">{col_name}</code>
                    <span class="col-type">{col_type}</span>
                    {note_html}
                </label>
            """
        rows_html += "</div></div>"

    hidden_tables_html = ", ".join(f"<code>{t}</code>" for t in sorted(HIDDEN_TABLES))
    hidden_cols_html = ", ".join(f"<code>{c}</code>" for c in sorted(ALREADY_HIDDEN))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BossBench — Column Visibility Picker</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    padding: 20px;
    max-width: 900px;
    margin: 0 auto;
}}
h1 {{
    color: #58a6ff;
    font-size: 1.6rem;
    margin-bottom: 8px;
}}
.subtitle {{
    color: #8b949e;
    font-size: 0.95rem;
    margin-bottom: 20px;
}}
.info-box {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 20px;
    font-size: 0.85rem;
    color: #8b949e;
}}
.info-box summary {{
    cursor: pointer;
    color: #58a6ff;
    font-weight: 600;
    margin-bottom: 8px;
}}
.info-box code {{
    background: #21262d;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.8rem;
    color: #f0883e;
}}
.table-section {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-bottom: 12px;
    overflow: hidden;
}}
.table-header {{
    padding: 12px 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #161b22;
    border-bottom: 1px solid #30363d;
    user-select: none;
}}
.table-header:hover {{ background: #1c2129; }}
.arrow {{
    color: #8b949e;
    font-size: 0.8rem;
    transition: transform 0.2s;
    width: 16px;
}}
.arrow.collapsed {{ transform: rotate(-90deg); }}
.table-header code {{
    color: #79c0ff;
    font-size: 1rem;
    font-weight: 600;
}}
.table-desc {{ color: #8b949e; font-size: 0.85rem; flex: 1; }}
.col-count {{
    color: #f0883e;
    font-size: 0.8rem;
    font-weight: 600;
    min-width: 80px;
    text-align: right;
}}
.table-cols {{
    padding: 8px 16px 12px 16px;
}}
.table-cols.hidden {{ display: none; }}
.col-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
    cursor: pointer;
    border-bottom: 1px solid #21262d;
}}
.col-row:last-child {{ border-bottom: none; }}
.col-row:hover {{ background: #1c2129; margin: 0 -16px; padding: 5px 16px; }}
.col-row input[type="checkbox"] {{
    width: 18px;
    height: 18px;
    accent-color: #f85149;
    cursor: pointer;
    flex-shrink: 0;
}}
.col-name {{
    color: #c9d1d9;
    font-size: 0.9rem;
    min-width: 200px;
}}
.col-type {{
    color: #484f58;
    font-size: 0.8rem;
    min-width: 70px;
}}
.note {{
    color: #8b949e;
    font-size: 0.8rem;
}}
.note.warn {{
    color: #d29922;
    font-weight: 600;
}}
.submit-area {{
    position: sticky;
    bottom: 0;
    background: #0d1117;
    padding: 16px 0;
    border-top: 1px solid #30363d;
    display: flex;
    align-items: center;
    gap: 16px;
}}
.submit-btn {{
    background: #f85149;
    color: white;
    border: none;
    padding: 12px 32px;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
}}
.submit-btn:hover {{ background: #da3633; }}
.submit-btn:disabled {{ background: #484f58; cursor: not-allowed; }}
.total-selected {{
    color: #f0883e;
    font-size: 1rem;
    font-weight: 600;
}}
.result {{
    margin-top: 16px;
    padding: 16px;
    border-radius: 8px;
    font-size: 0.9rem;
    display: none;
}}
.result.success {{
    display: block;
    background: #0d2818;
    border: 1px solid #238636;
    color: #3fb950;
}}
.result.error {{
    display: block;
    background: #2d1115;
    border: 1px solid #f85149;
    color: #f85149;
}}
</style>
</head>
<body>
<h1>🔒 BossBench — Column Visibility Picker</h1>
<p class="subtitle">Check columns you want to <strong style="color:#f85149">HIDE</strong> from the agent, then hit Submit.</p>

<details class="info-box">
<summary>ℹ️ Already hidden (click to expand)</summary>
<p style="margin-top:8px"><strong>Hidden tables (16):</strong> {hidden_tables_html}</p>
<p style="margin-top:8px"><strong>Hidden columns ({len(ALREADY_HIDDEN)}):</strong> {hidden_cols_html}</p>
</details>

<form id="form">
{rows_html}

<div class="submit-area">
    <button type="submit" class="submit-btn" id="submitBtn">Submit Selections</button>
    <span class="total-selected" id="totalSelected">0 columns selected to hide</span>
</div>
</form>

<div id="result" class="result"></div>

<script>
function toggleTable(name) {{
    const cols = document.getElementById('cols-' + name);
    const arrow = document.getElementById('arrow-' + name);
    cols.classList.toggle('hidden');
    arrow.classList.toggle('collapsed');
}}

function updateCount(name) {{
    const cols = document.getElementById('cols-' + name);
    const checked = cols.querySelectorAll('input:checked').length;
    document.getElementById('count-' + name).textContent = checked ? checked + ' selected' : '';

    // Update total
    const total = document.querySelectorAll('#form input[type="checkbox"]:checked').length;
    document.getElementById('totalSelected').textContent = total + ' column' + (total !== 1 ? 's' : '') + ' selected to hide';
}}

document.getElementById('form').addEventListener('submit', async (e) => {{
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    const result = document.getElementById('result');
    btn.disabled = true;
    btn.textContent = 'Submitting...';

    const checked = [];
    document.querySelectorAll('#form input[type="checkbox"]:checked').forEach(cb => {{
        checked.push(cb.value);
    }});

    try {{
        const resp = await fetch('/submit', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ columns: checked }})
        }});
        const data = await resp.json();
        result.className = 'result success';
        result.innerHTML = '✅ <strong>Submitted ' + checked.length + ' columns to hide!</strong><br>' +
            'Columns: ' + checked.map(c => '<code>' + c + '</code>').join(', ') +
            '<br><br>Tell Claude in Slack to apply the changes.';
    }} catch (err) {{
        result.className = 'result error';
        result.textContent = '❌ Error: ' + err.message;
    }}
    btn.disabled = false;
    btn.textContent = 'Submit Selections';
}});
</script>
</body>
</html>"""


@app.function(volumes={"/data": vol})
@modal.asgi_app()
def picker():
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    import datetime

    web = FastAPI()

    @web.get("/")
    async def index():
        return HTMLResponse(build_html())

    @web.post("/submit")
    async def submit(request: Request):
        body = await request.json()
        columns = body.get("columns", [])
        submission = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "columns_to_hide": columns,
        }
        # Save to volume
        with open("/data/latest_submission.json", "w") as f:
            json.dump(submission, f, indent=2)
        # Also append to history
        history = []
        try:
            with open("/data/submission_history.json") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        history.append(submission)
        with open("/data/submission_history.json", "w") as f:
            json.dump(history, f, indent=2)
        vol.commit()
        return JSONResponse({"status": "ok", "count": len(columns), "columns": columns})

    @web.get("/latest")
    async def latest():
        """Read the latest submission — Claude polls this endpoint."""
        try:
            with open("/data/latest_submission.json") as f:
                return JSONResponse(json.load(f))
        except FileNotFoundError:
            return JSONResponse({"status": "no_submissions"})

    return web
