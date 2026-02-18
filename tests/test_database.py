"""Tests for the database layer — verifies correct field name mapping."""

import json
import pytest

from src.storage.database import DatabaseManager
from src.storage.models import AnalysisReport


@pytest.fixture
def db():
    """In-memory SQLite DB for each test."""
    return DatabaseManager(database_url="sqlite:///:memory:")


def test_save_and_retrieve_report(db, sample_agent_state):
    """Critical regression: agent field names must match DB column names."""
    report_id = db.save_report(
        user_input=sample_agent_state["user_input"],
        decision="GO",
        full_state=sample_agent_state,
        execution_time=12.5,
    )
    assert isinstance(report_id, int)
    assert report_id > 0

    reports = db.get_reports(limit=10)
    assert len(reports) == 1
    r = reports[0]

    assert r.decision == "GO"
    assert r.user_input == sample_agent_state["user_input"]
    assert r.execution_time_seconds == 12.5

    # FIX REGRESSION: These must NOT be None — they were previously always None
    # because save_report used wrong keys like "market_report" instead of "market_analysis"
    assert r.market_analysis is not None, "market_analysis must be saved correctly"
    assert r.tech_analysis is not None, "tech_analysis must be saved correctly"
    assert r.risk_analysis is not None, "risk_analysis must be saved correctly"
    assert r.user_feedback_analysis is not None, "user_feedback_analysis must be saved correctly"


def test_statistics(db, sample_agent_state):
    db.save_report("idea 1", "GO", sample_agent_state)
    db.save_report("idea 2", "NO-GO", sample_agent_state)
    db.save_report("idea 3", "PIVOT", sample_agent_state)

    stats = db.get_statistics()
    assert stats["total_reports"] == 3
    assert stats["decisions"]["GO"] == 1
    assert stats["decisions"]["NO-GO"] == 1
    assert stats["decisions"]["PIVOT"] == 1


def test_filter_by_decision(db, sample_agent_state):
    db.save_report("idea 1", "GO", sample_agent_state)
    db.save_report("idea 2", "NO-GO", sample_agent_state)
    db.save_report("idea 3", "GO", sample_agent_state)

    go_reports = db.get_reports(decision_filter="GO")
    assert len(go_reports) == 2

    nogo_reports = db.get_reports(decision_filter="NO-GO")
    assert len(nogo_reports) == 1


def test_search_term_filter(db, sample_agent_state):
    state2 = {**sample_agent_state, "user_input": "blockchain NFT trading platform"}
    db.save_report(sample_agent_state["user_input"], "GO", sample_agent_state)
    db.save_report("blockchain NFT trading platform", "NO-GO", state2)

    results = db.get_reports(search_term="hydration")
    assert len(results) == 1
    assert "hydration" in results[0].user_input.lower()


def test_empty_database_returns_empty_list(db):
    reports = db.get_reports()
    assert reports == []


def test_to_dict_includes_all_fields(db, sample_agent_state):
    db.save_report("test idea", "GO", sample_agent_state)
    report = db.get_reports()[0]
    d = report.to_dict()

    expected_keys = [
        "id", "user_input", "timestamp", "decision",
        "confidence_score", "market_analysis", "tech_analysis",
        "risk_analysis", "user_feedback_analysis", "full_report",
        "execution_time_seconds", "model_name",
    ]
    for key in expected_keys:
        assert key in d, f"Missing key in to_dict(): {key}"
