"""Tests for the government knowledge retrieval provider.

Tests the FixtureKnowledgeProvider, Retriever, SourceValidator,
CitationBuilder, and integration with the AgentRegistry.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.schemas.agents import RetrievalSource
from app.services.knowledge.citation_builder import (
    CitationBuilder,
    build_citation_list,
    build_citation_summary,
)
from app.services.knowledge.provider import FixtureKnowledgeProvider
from app.services.knowledge.retriever import Retriever
from app.services.knowledge.source_validator import SourceValidator


# ---------------------------------------------------------------------------
# RetrievalSource tests
# ---------------------------------------------------------------------------


class TestRetrievalSource:
    """Tests for the RetrievalSource schema."""

    def test_retrieval_source_creation(self):
        """Test RetrievalSource creation with all fields."""
        source = RetrievalSource(
            document_id="doc_001",
            source_title="Test Document",
            issuing_authority="Test Authority",
            source_url="https://example.gov.in/doc",
            publication_date="2024-01-01",
            relevant_excerpt="Test excerpt",
            page_or_section="Section 1",
            retrieval_score=0.95,
            document_version="1.0",
        )
        assert source.document_id == "doc_001"
        assert source.source_title == "Test Document"
        assert source.issuing_authority == "Test Authority"
        assert source.retrieval_score == 0.95

    def test_retrieval_source_minimal(self):
        """Test RetrievalSource with only optional fields None."""
        source = RetrievalSource()
        assert source.document_id is None
        assert source.source_title is None
        assert source.retrieval_score is None


# ---------------------------------------------------------------------------
# Retriever tests
# ---------------------------------------------------------------------------


class TestRetriever:
    """Tests for the Retriever class."""

    @pytest.fixture
    def retriever(self) -> Retriever:
        return Retriever()

    def test_normalize_query(self, retriever: Retriever):
        """Test query normalization."""
        result = retriever.normalize_query("  Hello   World  ")
        assert result == "Hello World"

        result = retriever.normalize_query("")
        assert result == ""

        result = retriever.normalize_query("TEST Query")
        assert result == "TEST Query"

    def test_build_filters(self, retriever: Retriever):
        """Test filter building."""
        filters = retriever.build_filters("gst registration", None)
        assert "scheme_or_scheme" in filters
        assert "gst" in filters["scheme_or_scheme"]

        filters = retriever.build_filters("udyam registration", {"state": "karnataka"})
        assert filters["state"] == "karnataka"
        assert "udyam" in filters["scheme_or_scheme"]

    def test_retrieve_candidates(self, retriever: Retriever):
        """Test candidate retrieval."""
        results = retriever.retrieve_candidates("gst registration", {}, limit=5)
        assert len(results) > 0
        assert all("document_id" in r for r in results)
        assert all("retrieval_score" in r for r in results)
        assert all(0 <= r["retrieval_score"] <= 1 for r in results)

    def test_retrieve_candidates_empty_query(self, retriever: Retriever):
        """Test retrieval with empty query returns no results."""
        results = retriever.retrieve_candidates("", {}, limit=5)
        assert results == []

    def test_retrieve_candidates_filtered(self, retriever: Retriever):
        """Test retrieval with scheme filter."""
        results = retriever.retrieve_candidates(
            "registration", {"scheme_or_scheme": ["gst_registration"]}, limit=5
        )
        assert len(results) > 0
        for r in results:
            assert r["service_or_scheme"] == "gst_registration"

    def test_deduplicate(self, retriever: Retriever):
        """Test deduplication by document_id."""
        docs = [
            {"document_id": "doc_1", "retrieval_score": 0.9},
            {"document_id": "doc_1", "retrieval_score": 0.8},
            {"document_id": "doc_2", "retrieval_score": 0.7},
        ]
        result = retriever.deduplicate(docs)
        assert len(result) == 2
        assert result[0]["retrieval_score"] == 0.9  # Keeps highest score

    def test_rerank(self, retriever: Retriever):
        """Test reranking."""
        docs = [
            {"document_id": "doc_1", "retrieval_score": 0.5},
            {"document_id": "doc_2", "retrieval_score": 0.3},
        ]
        result = retriever.rerank(docs, "gst registration")
        assert len(result) == 2
        assert result[0]["retrieval_score"] >= result[1]["retrieval_score"]


# ---------------------------------------------------------------------------
# SourceValidator tests
# ---------------------------------------------------------------------------


class TestSourceValidator:
    """Tests for the SourceValidator class."""

    @pytest.fixture
    def validator(self) -> SourceValidator:
        return SourceValidator()

    def test_validate_official_source(self, validator: SourceValidator):
        """Test validation of an official government source."""
        doc = {
            "document_id": "doc_1",
            "source_title": "Test Doc",
            "issuing_authority": "Ministry of MSME, Government of India",
            "source_url": "https://udyamregistration.gov.in/doc",
            "relevant_excerpt": "Test excerpt",
        }
        result = validator.validate_sources([doc])
        assert result[0]["_validation_passed"] is True
        assert len(result[0]["_validation_warnings"]) == 0

    def test_validate_unofficial_authority(self, validator: SourceValidator):
        """Test validation with unofficial authority."""
        doc = {
            "document_id": "doc_1",
            "source_title": "Test Doc",
            "issuing_authority": "Private Company Ltd",
            "source_url": "https://private.com/doc",
            "relevant_excerpt": "Test excerpt",
        }
        result = validator.validate_sources([doc])
        assert result[0]["_is_official_authority"] is False
        assert len(result[0]["_validation_warnings"]) > 0

    def test_validate_unofficial_domain(self, validator: SourceValidator):
        """Test validation with unofficial domain."""
        doc = {
            "document_id": "doc_1",
            "source_title": "Test Doc",
            "issuing_authority": "Ministry of MSME",
            "source_url": "https://private.com/doc",
            "relevant_excerpt": "Test excerpt",
        }
        result = validator.validate_sources([doc])
        assert result[0]["_is_official_domain"] is False
        assert len(result[0]["_validation_warnings"]) > 0

    def test_validate_missing_fields(self, validator: SourceValidator):
        """Test validation with missing fields."""
        doc = {
            "document_id": "doc_1",
        }
        result = validator.validate_sources([doc])
        assert len(result[0]["_validation_warnings"]) > 0
        assert "source_title" in str(result[0]["_validation_warnings"])


# ---------------------------------------------------------------------------
# CitationBuilder tests
# ---------------------------------------------------------------------------


class TestCitationBuilder:
    """Tests for the CitationBuilder class."""

    @pytest.fixture
    def builder(self) -> CitationBuilder:
        return CitationBuilder()

    @pytest.fixture
    def sample_source(self) -> RetrievalSource:
        return RetrievalSource(
            document_id="doc_1",
            source_title="Test Document",
            issuing_authority="Ministry of MSME",
            source_url="https://example.gov.in/doc",
            publication_date="2024-01-01",
            relevant_excerpt="Test excerpt text",
            page_or_section="Section 2",
            retrieval_score=0.95,
            document_version="1.0",
        )

    def test_build_single(self, builder: CitationBuilder, sample_source: RetrievalSource):
        """Test building a single citation."""
        result = builder.build_sources([sample_source])
        assert len(result) == 1
        assert result[0].document_id == "doc_1"
        assert result[0].source_title == "Test Document"

    def test_build_citation_summary(self, builder: CitationBuilder, sample_source: RetrievalSource):
        """Test citation summary building."""
        summary = build_citation_summary(sample_source)
        assert "Test Document" in summary
        assert "Ministry of MSME" in summary

    def test_build_citation_list(self, builder: CitationBuilder, sample_source: RetrievalSource):
        """Test citation list building."""
        result = build_citation_list([sample_source])
        assert "1. Test Document" in result
        assert "Ministry of MSME" in result


# ---------------------------------------------------------------------------
# FixtureKnowledgeProvider tests
# ---------------------------------------------------------------------------


class TestFixtureKnowledgeProvider:
    """Tests for the FixtureKnowledgeProvider class."""

    @pytest.fixture
    def provider(self) -> FixtureKnowledgeProvider:
        return FixtureKnowledgeProvider(enabled=True)

    @pytest.fixture
    def disabled_provider(self) -> FixtureKnowledgeProvider:
        return FixtureKnowledgeProvider(enabled=False)

    @pytest.mark.asyncio
    async def test_retrieve_enabled(self, provider: FixtureKnowledgeProvider):
        """Test retrieval with provider enabled."""
        results = await provider.retrieve(
            "gst registration",
            user_id=uuid4(),
            conversation_id=uuid4(),
            limit=5,
        )
        assert len(results) > 0
        assert all(isinstance(s, RetrievalSource) for s in results)

    @pytest.mark.asyncio
    async def test_retrieve_disabled(self, disabled_provider: FixtureKnowledgeProvider):
        """Test retrieval with provider disabled."""
        results = await disabled_provider.retrieve(
            "gst registration",
            user_id=uuid4(),
            conversation_id=uuid4(),
            limit=5,
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, provider: FixtureKnowledgeProvider):
        """Test retrieval with filters."""
        results = await provider.retrieve(
            "gst registration",
            user_id=uuid4(),
            conversation_id=uuid4(),
            filters={"scheme_or_scheme": ["gst_registration"]},
            limit=5,
        )
        assert len(results) > 0
        for s in results:
            assert s.source_url is not None

    @pytest.mark.asyncio
    async def test_retrieve_empty_query(self, provider: FixtureKnowledgeProvider):
        """Test retrieval with empty query."""
        results = await provider.retrieve(
            "",
            user_id=uuid4(),
            conversation_id=uuid4(),
            limit=5,
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_returns_typed_objects(self, provider: FixtureKnowledgeProvider):
        """Test that retrieval returns typed RetrievalSource objects."""
        results = await provider.retrieve(
            "udyam registration",
            user_id=uuid4(),
            conversation_id=uuid4(),
            limit=3,
        )
        assert all(isinstance(s, RetrievalSource) for s in results)
        # Check that source metadata is preserved
        for s in results:
            assert s.document_id is not None
            assert s.source_title is not None


# ---------------------------------------------------------------------------
# Protocol compliance tests
# ---------------------------------------------------------------------------


class TestProtocolCompliance:
    """Tests that the provider implements the protocol correctly."""

    @pytest.mark.asyncio
    async def test_provider_implements_protocol(self):
        """Test that FixtureKnowledgeProvider implements GovernmentKnowledgeProvider."""
        from app.services.retrieval import GovernmentKnowledgeProvider

        provider = FixtureKnowledgeProvider()
        assert isinstance(provider, GovernmentKnowledgeProvider)

    @pytest.mark.asyncio
    async def test_provider_has_retrieve_method(self):
        """Test that provider has the required retrieve method."""
        provider = FixtureKnowledgeProvider()
        assert hasattr(provider, "retrieve")
        assert callable(provider.retrieve)
