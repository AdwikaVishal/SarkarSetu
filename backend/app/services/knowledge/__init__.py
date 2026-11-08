"""Government knowledge retrieval package.

Provides a concrete implementation of the GovernmentKnowledgeProvider protocol
for retrieving official government documents and scheme information.

Components:
- Provider: Concrete implementation of GovernmentKnowledgeProtocol
- Retriever: Retrieval logic with fixture-backed development data
- QueryBuilder: Query normalization
- SourceValidator: Source validation rules
- Reranker: Ranking and reranking
- CitationBuilder: Citation construction
- FallbackProvider: Unavailable provider wrapper

Note: The default provider is a development-only fixture-backed implementation.
It is clearly marked as development-only and must not be used in production
without replacement by Saatvika's RAG implementation.
"""

from app.services.knowledge.citation_builder import CitationBuilder
from app.services.knowledge.provider import (
    FixtureKnowledgeProvider,
    get_fixture_provider,
)
from app.services.knowledge.retriever import Retriever
from app.services.knowledge.source_validator import SourceValidator

__all__ = [
    "FixtureKnowledgeProvider",
    "get_fixture_provider",
    "Retriever",
    "SourceValidator",
    "CitationBuilder",
]
