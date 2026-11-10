"""Tests for embedding generation."""

from __future__ import annotations

import pytest

from rag.embeddings.embedder import Embedder, EmbeddingError


@pytest.fixture
def embedder():
    return Embedder()


def test_generate_embedding_valid_text(embedder):
    vec = embedder.generate_embedding("Udyam registration requirements")
    assert isinstance(vec, list)
    assert len(vec) == embedder.dimension == 384
    assert all(isinstance(x, float) for x in vec)


def test_generate_embedding_empty_text(embedder):
    vec = embedder.generate_embedding("")
    assert len(vec) == embedder.dimension
    assert all(x == 0.0 for x in vec)

    vec2 = embedder.generate_embedding("   ")
    assert len(vec2) == embedder.dimension


def test_generate_embeddings_batch(embedder):
    texts = [
        "Udyam registration requirements",
        "GST registration threshold",
        "MSME subsidy scheme eligibility",
    ]
    vecs = embedder.generate_embeddings(texts)
    assert len(vecs) == 3
    for vec in vecs:
        assert len(vec) == embedder.dimension


def test_generate_embeddings_empty_list(embedder):
    assert embedder.generate_embeddings([]) == []


def test_model_loaded(embedder):
    assert embedder.model_loaded is True
    assert embedder.load_error is None


def test_query_embedding(embedder):
    vec = embedder.generate_query_embedding("What is MSME classification?")
    assert len(vec) == embedder.dimension
