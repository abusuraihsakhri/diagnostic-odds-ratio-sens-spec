"""The mock adapter must not impersonate unimplemented model providers."""
import pytest
from agents.llm_factory import LLMFactory


def test_mock_explicitly_disclaims_validation():
    text = LLMFactory.create("mock").invoke("Explain this result")
    assert "No model inference or clinical validation" in text


def test_unimplemented_providers_fail_clearly():
    for provider in ("openai", "claude", "ollama", "unknown"):
        with pytest.raises(ValueError, match="not implemented"):
            LLMFactory.create(provider)
