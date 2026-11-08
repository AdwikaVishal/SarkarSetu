"""Tests for source registry and versioning."""

from __future__ import annotations

from rag.sources.source_metadata import SourceMetadata, SourceRegistry
from rag.sources.source_versioning import SourceChangeReport, SourceVersioning


def test_source_registry_add_and_get(tmp_path):
    registry = SourceRegistry(registry_path=tmp_path / "registry.jsonl")
    source = SourceMetadata(
        source_id="UDYAM_001",
        title="Udyam Registration Guidelines",
        authority="Ministry of MSME",
        source_url="https://udyamregistration.gov.in/",
        topic="udyam_registration",
    )
    registry.add(source)
    fetched = registry.get("UDYAM_001")
    assert fetched is not None
    assert fetched.title == "Udyam Registration Guidelines"
    assert fetched.source_url == "https://udyamregistration.gov.in/"
    assert registry.count() == 1


def test_source_registry_get_by_url(tmp_path):
    registry = SourceRegistry(registry_path=tmp_path / "registry2.jsonl")
    source = SourceMetadata(
        source_id="GST_001",
        title="GST Guidelines",
        authority="CBIC",
        source_url="https://www.gst.gov.in/",
        topic="gst",
    )
    registry.add(source)
    fetched = registry.get_by_url("https://www.gst.gov.in/")
    assert fetched is not None
    assert fetched.source_id == "GST_001"


def test_source_versioning_detects_first_seen(tmp_path):
    registry = SourceRegistry(registry_path=tmp_path / "registry3.jsonl")
    versioning = SourceVersioning(registry=registry)
    # No existing source; need a file to hash
    import hashlib

    file_path = tmp_path / "doc.pdf"
    file_path.write_bytes(b"content version one")
    report = versioning.check_changes("NEW_001", str(file_path))
    assert isinstance(report, SourceChangeReport)
    assert report.first_seen is True


def test_source_versioning_detects_change(tmp_path):
    registry = SourceRegistry(registry_path=tmp_path / "registry4.jsonl")
    versioning = SourceVersioning(registry=registry)
    file_path = tmp_path / "doc.pdf"

    # Record first ingestion
    file_path.write_bytes(b"version one")
    h1 = __import__("hashlib").sha256(b"version one").hexdigest()
    versioning.record_ingestion(
        source_id="CHG_001",
        source_url="https://example.gov.in/doc",
        content_hash=h1,
        file_path=str(file_path),
        title="Doc",
        authority="Auth",
        topic="gst",
    )

    # Change content
    file_path.write_bytes(b"version two different content")
    report = versioning.check_changes("CHG_001", str(file_path))
    assert report.changed is True
    assert report.previous_hash == h1
    assert report.action == "reingest"
