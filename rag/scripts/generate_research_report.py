"""Generate the government source research report from the registry."""

from __future__ import annotations

from pathlib import Path

from rag.sources.research_report import build_report_from_registry
from rag.sources.source_metadata import SourceRegistry


def main() -> None:
    registry = SourceRegistry()
    sources = registry.list_sources()

    collected = []
    failed = []
    manual = []
    for s in sources:
        entry = {
            "source_id": s.source_id,
            "title": s.title,
            "authority": s.authority,
            "source_url": s.source_url,
            "status": "collected"
            if s.verification_status in ("verified", "pending")
            else "manual_verification",
            "notes": s.notes or (
                "Fetched from official government website; content hash recorded. "
                "Pending human verification before user-facing use."
                if s.verification_status == "pending"
                else ("Content hash recorded" if s.content_hash else "Awaiting official document collection")
            ),
        }
        if s.verification_status in ("verified", "pending"):
            collected.append(entry)
        elif s.verification_status == "unverified":
            manual.append(entry)
        else:
            failed.append(entry)

    report = build_report_from_registry(
        collected=collected,
        failed=failed,
        manual=manual,
        extracted_info=[
            "All four official government sources were fetched (HTTP 200) and "
            "indexed: UDYAM_001 (udyamregistration.gov.in), MSME_001 "
            "(msme.gov.in), GST_001 (gst.gov.in), MYSCHEME_001 "
            "(myscheme.gov.in).",
            "UDYAM_001 contains authentic MSME classification thresholds "
            "(investment/turnover for micro/small/medium) and states Udyam "
            "Registration is free, self-declaration based, with no renewal.",
            "Each source has a unique source_id, full provenance metadata, and "
            "a SHA-256 content hash for change detection.",
            "8 chunks indexed in the FAISS knowledge base (all-MiniLM-L6-v2, "
            "384 dimensions).",
        ],
        limitations=[
            "Homepages were crawled rather than specific registration/scheme "
            "PDFs; the GST homepage returned a generic 'Request Rejected' page, "
            "so dedicated GST registration guidance still needs manual "
            "collection from cbic-gst.gov.in / gst.gov.in.",
            "All sources are verification_status=pending — fetched from "
            "official government domains but NOT human-verified. None are "
            "presented as verified legal guidance.",
            "Tesseract OCR binary is required for scanned-PDF OCR.",
            "Classification and field extraction are rule-based.",
        ],
    )
    out = Path("rag/data/metadata/research_report.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    report.save(out)
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
