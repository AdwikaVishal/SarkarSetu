"""Tests for semantic retrieval."""

from __future__ import annotations

import os

import pytest

from rag.retrieval.engine import RetrievalEngine


@pytest.fixture
def engine():
    return RetrievalEngine()


def test_relevant_query_returns_results(engine):
    result = engine.retrieve_guidance(
        query="Udyam registration requirements Aadhaar PAN",
        business_context={},
        top_k=5,
    )
    assert result["retrieval_status"] in ("success", "conflicting_evidence")
    assert len(result["results"]) > 0
    assert result["results"][0]["similarity_score"] is not None
    assert result["results"][0]["source_id"] is not None


def test_results_have_source_metadata(engine):
    result = engine.retrieve_guidance(
        query="GST registration threshold goods",
        business_context={},
        top_k=5,
    )
    for item in result["results"]:
        assert item["source_id"] is not None
        assert item["document_title"] is not None
        assert item["authority"] is not None
        assert item["page_number"] is not None
        assert item["source_url"] is not None
        assert "verification_status" in item


def test_top_k_respected(engine):
    result = engine.retrieve_guidance(
        query="Udyam registration", business_context={}, top_k=2
    )
    assert len(result["results"]) <= 2


def test_empty_index_insufficient_evidence(monkeypatch):
    engine = RetrievalEngine()
    # Force an empty index that cannot be loaded from disk
    engine.index._index = None  # type: ignore[attr-defined]
    monkeypatch.setattr(engine.index, "load", lambda *a, **k: False)
    result = engine.retrieve_guidance(query="anything", top_k=5)
    assert result["retrieval_status"] == "insufficient_evidence"
    assert result["results"] == []
    assert result["citations"] == []


def test_empty_query_insufficient_evidence(engine):
    result = engine.retrieve_guidance(query="", top_k=5)
    assert result["retrieval_status"] == "insufficient_evidence"
