"""Tests for simulator-side LLM environment overrides."""

from saas_bench.config import BenchmarkConfig
from saas_bench.server_entry import _apply_simulator_llm_config


SIMULATOR_LLM_ENV_VARS = (
    "SAAS_SOCIAL_POST_LLM_PROVIDER",
    "SAAS_SOCIAL_POST_LLM_MODEL",
    "SAAS_ENTERPRISE_LLM_PROVIDER",
    "SAAS_ENTERPRISE_LLM_MODEL",
)


def test_simulator_llm_env_absent_uses_exact_defaults(monkeypatch):
    for env_var in SIMULATOR_LLM_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)

    config = BenchmarkConfig()

    assert config.social_post_llm_provider == "bedrock"
    assert config.social_post_llm_model == "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    assert config.enterprise_llm_provider == "bedrock"
    assert config.enterprise_llm_model == "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def test_simulator_llm_env_overrides_config_and_session_payload(monkeypatch):
    monkeypatch.setenv("SAAS_SOCIAL_POST_LLM_PROVIDER", "openai")
    monkeypatch.setenv("SAAS_SOCIAL_POST_LLM_MODEL", "local-vllm-social")
    monkeypatch.setenv("SAAS_ENTERPRISE_LLM_PROVIDER", "openai")
    monkeypatch.setenv("SAAS_ENTERPRISE_LLM_MODEL", "local-vllm-enterprise")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    config = BenchmarkConfig()

    assert config.social_post_llm_provider == "openai"
    assert config.social_post_llm_model == "local-vllm-social"
    assert config.enterprise_llm_provider == "openai"
    assert config.enterprise_llm_model == "local-vllm-enterprise"

    assert _apply_simulator_llm_config(config) == {
        "social_post_llm_provider": "openai",
        "social_post_llm_model": "local-vllm-social",
        "enterprise_llm_provider": "openai",
        "enterprise_llm_model": "local-vllm-enterprise",
    }
