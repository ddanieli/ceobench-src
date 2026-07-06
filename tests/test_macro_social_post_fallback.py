"""Regression tests for macro social-post LLM fallback behavior."""

from copy import deepcopy

import pytest


def _normalize_rng_state(value):
    if isinstance(value, dict):
        return {key: _normalize_rng_state(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_rng_state(val) for val in value]
    if hasattr(value, "tolist"):
        return _normalize_rng_state(value.tolist())
    return value


def _assert_rng_state_unchanged(before, after):
    assert _normalize_rng_state(after) == _normalize_rng_state(before)


def _macro_result(sim, **overrides):
    result = {
        "type": "macro",
        "customer_id": sim._market_observer_id,
        "success": False,
        "text": None,
        "pmi": 44.2,
        "trend": "contraction",
        "macro_type": "publication",
    }
    result.update(overrides)
    return result


def _only_social_post(conn):
    return conn.execute(
        """
        SELECT sentiment, content, likes, shares, virality_score, influence_score
        FROM social_media_posts
        """
    ).fetchone()


def test_failed_macro_llm_result_inserts_template_post(make_initialized_sim):
    conn, sim, _config = make_initialized_sim()
    sim.current_day = 11
    macro_rng_state_before = deepcopy(sim._macro_rng.bit_generator.state)

    sim._process_social_post_results(
        [_macro_result(sim, success=False, text=None)],
        influence_cache={},
    )

    _assert_rng_state_unchanged(
        macro_rng_state_before, sim._macro_rng.bit_generator.state
    )

    row = _only_social_post(conn)
    assert row is not None
    assert row["content"]
    assert "44.2" in row["content"]
    assert any(
        term in row["content"].lower()
        for term in ("contraction", "weakness", "budgets")
    )
    assert row["sentiment"] == "negative"
    assert 20 <= row["likes"] < 110
    assert 6 <= row["shares"] < 40
    assert row["virality_score"] == pytest.approx(
        row["likes"] * 0.3 + row["shares"] * 0.7
    )
    assert row["influence_score"] == 0.0


def test_empty_macro_llm_text_inserts_non_empty_template_post(make_initialized_sim):
    conn, sim, _config = make_initialized_sim()
    sim.current_day = 12
    macro_rng_state_before = deepcopy(sim._macro_rng.bit_generator.state)

    sim._process_social_post_results(
        [
            _macro_result(
                sim,
                success=True,
                text="",
                pmi=56.7,
                trend="strong_expansion",
                macro_type="publication",
            )
        ],
        influence_cache={},
    )

    _assert_rng_state_unchanged(
        macro_rng_state_before, sim._macro_rng.bit_generator.state
    )

    row = _only_social_post(conn)
    assert row is not None
    assert row["content"]
    assert "56.7" in row["content"]
    assert any(
        term in row["content"].lower()
        for term in ("expansion", "surging", "firing")
    )
    assert row["sentiment"] == "positive"


def test_successful_macro_llm_text_is_preserved_without_macro_rng_draw(
    make_initialized_sim,
):
    conn, sim, _config = make_initialized_sim()
    sim.current_day = 13
    macro_rng_state_before = deepcopy(sim._macro_rng.bit_generator.state)
    llm_text = "LLM macro desk: holding steady while buyers watch the PMI print."

    sim._process_social_post_results(
        [
            _macro_result(
                sim,
                success=True,
                text=llm_text,
                pmi=50.1,
                trend="neutral",
                macro_type="publication",
            )
        ],
        influence_cache={},
    )

    _assert_rng_state_unchanged(
        macro_rng_state_before, sim._macro_rng.bit_generator.state
    )

    row = _only_social_post(conn)
    assert row is not None
    assert row["content"] == llm_text
    assert row["sentiment"] == "neutral"
