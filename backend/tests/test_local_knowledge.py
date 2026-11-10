"""Tests for the local knowledge base."""

import pytest

from app.services.ai.local_knowledge import (
    LocalKnowledgeBase,
    SchemeEntry,
    get_knowledge_base,
    SCHEMES,
)


class TestSchemeEntry:
    """Tests for SchemeEntry dataclass."""

    def test_scheme_entry_to_dict(self):
        """Test SchemeEntry.to_dict returns all fields."""
        scheme = SchemeEntry(
            name="Test Scheme",
            description="A test scheme",
            eligibility="Anyone",
            benefits="Some benefits",
            required_documents=["Doc A", "Doc B"],
            application_procedure="Apply online",
            official_url="https://example.gov",
            official_source="Test Authority",
            last_verified_date="2024-01-01",
            keywords=["test", "scheme"],
            category="registration",
            confidence_base=0.9,
        )
        d = scheme.to_dict()
        assert d["name"] == "Test Scheme"
        assert d["description"] == "A test scheme"
        assert d["eligibility"] == "Anyone"
        assert d["benefits"] == "Some benefits"
        assert d["required_documents"] == ["Doc A", "Doc B"]
        assert d["application_procedure"] == "Apply online"
        assert d["official_url"] == "https://example.gov"
        assert d["category"] == "registration"
        assert d["confidence"] == 0.9


class TestLocalKnowledgeBase:
    """Tests for LocalKnowledgeBase."""

    def setup_method(self):
        self.kb = LocalKnowledgeBase()

    def test_get_all_schemes(self):
        """Test getting all schemes."""
        schemes = self.kb.get_all_schemes()
        assert len(schemes) == 10
        assert all(isinstance(s, SchemeEntry) for s in schemes)

    def test_get_scheme(self):
        """Test getting a specific scheme by ID."""
        scheme = self.kb.get_scheme("udyam_registration")
        assert scheme is not None
        assert scheme.name == "Udyam Registration"
        assert self.kb.get_scheme("nonexistent") is None

    def test_search_exact_match(self):
        """Test exact scheme name match."""
        result = self.kb.search("udyam registration")
        assert result["match_type"] == "exact"
        assert len(result["matched_schemes"]) > 0
        assert result["matched_schemes"][0]["name"] == "Udyam Registration"

    def test_search_keyword_match(self):
        """Test keyword-based matching."""
        result = self.kb.search("gst registration turnover")
        assert result["match_type"] in ("exact", "keyword")
        assert len(result["matched_schemes"]) > 0
        # GST registration should be highly ranked
        names = [s["name"] for s in result["matched_schemes"]]
        assert "GST Registration" in names

    def test_search_no_match(self):
        """Test search with no matching schemes."""
        result = self.kb.search("xyzzy quantum computing blockchain")
        assert result["match_type"] == "none"
        assert result["matched_schemes"] == []
        assert result["confidence"] == 0.0

    def test_search_empty_query(self):
        """Test search with empty query."""
        result = self.kb.search("")
        assert result["match_type"] == "none"
        assert result["matched_schemes"] == []

    def test_search_limit(self):
        """Test search respects limit parameter."""
        result = self.kb.search("business", limit=2)
        assert len(result["matched_schemes"]) <= 2

    def test_get_knowledge_base_singleton(self):
        """Test that get_knowledge_base returns a singleton."""
        kb1 = get_knowledge_base()
        kb2 = get_knowledge_base()
        assert kb1 is kb2

    def test_all_schemes_have_required_fields(self):
        """Test that all schemes have required fields populated."""
        for scheme_id, scheme in SCHEMES.items():
            assert scheme.name, f"{scheme_id}: missing name"
            assert scheme.description, f"{scheme_id}: missing description"
            assert scheme.eligibility, f"{scheme_id}: missing eligibility"
            assert scheme.benefits, f"{scheme_id}: missing benefits"
            assert scheme.required_documents, f"{scheme_id}: missing required_documents"
            assert scheme.application_procedure, f"{scheme_id}: missing application_procedure"
            assert scheme.official_url, f"{scheme_id}: missing official_url"
            assert scheme.official_source, f"{scheme_id}: missing official_source"
            assert scheme.last_verified_date, f"{scheme_id}: missing last_verified_date"
            assert scheme.keywords, f"{scheme_id}: missing keywords"
            assert scheme.category, f"{scheme_id}: missing category"


class TestKnowledgeBaseCoverage:
    """Tests that the knowledge base covers required topics."""

    def test_required_topics_covered(self):
        """Test that all 10 required topics are in the knowledge base."""
        required = [
            "udyam_registration",
            "pmegp",
            "mudra",
            "standup_india",
            "startup_india",
            "cgtmse",
            "gst_registration",
            "msme_classification",
            "government_subsidies",
            "business_compliance",
        ]
        for topic in required:
            assert topic in SCHEMES, f"Missing required topic: {topic}"

    def test_schemes_have_official_urls(self):
        """Test that all schemes have official government URLs."""
        for scheme_id, scheme in SCHEMES.items():
            assert scheme.official_url.startswith("http"), (
                f"{scheme_id}: official_url must be a valid URL"
            )
            assert ".gov.in" in scheme.official_url or ".in" in scheme.official_url, (
                f"{scheme_id}: official_url should be a government domain"
            )
