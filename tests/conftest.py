"""Keep unit tests independent of paid APIs and model update checks.

Model tests still run the real cached models. Full API evaluation belongs
to main.py, not the unit-test suite launched by check_lab.py.
"""
import pytest


@pytest.fixture(autouse=True)
def offline_unit_tests(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setattr("config.OPENAI_API_KEY", "")
    monkeypatch.setattr("src.m5_enrichment.OPENAI_API_KEY", "")
