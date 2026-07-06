"""Regression tests for agent social-post judge failure visibility."""

import json

from saas_bench import customer_llm, database
from saas_bench.database import add_agent_social_post


class _FakeCustomerSimulator:
    social_post_client = object()

    def _log_cost(self, *_args, **_kwargs):  # pragma: no cover - failure path must not log cost
        raise AssertionError("judge failures should not log LLM cost")


def test_agent_social_post_judge_failure_logs_stderr_and_preserves_zero_effect(
    make_initialized_sim,
    monkeypatch,
    capsys,
):
    conn, sim, config = make_initialized_sim()
    sim.customer_simulator = _FakeCustomerSimulator()
    sim.current_day = 1

    post_id = add_agent_social_post(
        conn,
        day=0,
        content="Launching a developer-first reliability initiative today.",
    )

    monkeypatch.setattr(database, "get_discovered_groups", lambda _conn: ["S1"])

    def fail_judge(*_args, **_kwargs):
        raise RuntimeError("judge service unavailable")

    monkeypatch.setattr(customer_llm, "judge_agent_social_post", fail_judge)

    sim._process_agent_social_posts(config={})

    captured = capsys.readouterr()
    assert "[sim] agent post judge LLM failed" in captured.err
    assert f"post_id={post_id}" in captured.err
    assert "group_id=S1" in captured.err
    assert f"provider={config.social_post_llm_provider}" in captured.err
    assert f"model={config.social_post_llm_model}" in captured.err
    assert "client=object" in captured.err
    assert "RuntimeError: judge service unavailable" in captured.err

    row = conn.execute(
        """
        SELECT effect_by_group, reasoning_by_group
        FROM agent_social_media_posts
        WHERE agent_post_id = ?
        """,
        (post_id,),
    ).fetchone()
    assert json.loads(row["effect_by_group"]) == {"S1": 0.0}
    assert json.loads(row["reasoning_by_group"]) == {}
