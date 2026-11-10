"""Tests for citation generation."""

from __future__ import annotations

from rag.retrieval.citations import build_citations


def test_build_citations_from_results():
    results = [
        {
            "chunk_id": "chunk_001",
            "source_id": "UDYAM_001",
            "document_title": "Udyam Registration Guidelines",
            "authority": "Ministry of MSME",
            "page_number": 3,
            "section": "Requirements",
            "source_url": "https://udyamregistration.gov.in/",
            "retrieved_at": "2026-01-01T00:00:00Z",
            "verification_status": "verified",
            "similarity_score": 0.82,
            "text": "Aadhaar number is required for Udyam registration.",
        }
    ]
    citations = build_citations(results)
    assert len(citations) == 1
    cit = citations[0]
    assert cit["citation_id"] == "CIT_001"
    assert cit["source_id"] == "UDYAM_001"
    assert cit["page_number"] == 3
    assert cit["source_url"] == "https://udyamregistration.gov.in/"
    assert cit["verification_status"] == "verified"
    assert cit["excerpt"] == results[0]["text"]


def test_citations_only_for_retrieved_chunks():
    results = [
        {
            "chunk_id": "chunk_001",
            "source_id": "SRC_A",
            "document_title": "Doc A",
            "authority": "Authority A",
            "page_number": 1,
            "section": None,
            "source_url": "https://example.gov.in/a",
            "retrieved_at": "2026-01-01T00:00:00Z",
            "verification_status": "verified",
            "similarity_score": 0.9,
            "text": "excerpt A",
        },
        {
            "chunk_id": "chunk_002",
            "source_id": "SRC_B",
            "document_title": "Doc B",
            "authority": "Authority B",
            "page_number": 5,
            "section": None,
            "source_url": "https://example.gov.in/b",
            "retrieved_at": "2026-01-01T00:00:00Z",
            "verification_status": "pending",
            "similarity_score": 0.7,
            "text": "excerpt B",
        },
    ]
    citations = build_citations(results)
    assert len(citations) == 2
    assert citations[0]["citation_id"] == "CIT_001"
    assert citations[1]["citation_id"] == "CIT_002"
    assert citations[1]["page_number"] == 5


def test_empty_results_no_citations():
    assert build_citations([]) == []
