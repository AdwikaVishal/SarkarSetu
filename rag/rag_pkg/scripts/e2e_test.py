"""End-to-end test of the RAG provider integration (simulates backend agent flow)."""

import asyncio
import sys

sys.path.insert(0, r"C:\Users\Saatvika Reddy\SarkarSetu")

from rag.integration.knowledge_provider import RagKnowledgeProvider
from rag.agents.document_agent import process_document
from rag.document_matching.matcher import match_documents_to_requirements


async def main():
    provider = RagKnowledgeProvider()  # backend RetrievalSource schema not importable here
    print("=== E2E: retrieve via RagKnowledgeProvider ===")
    for q in [
        "Udyam registration requirements Aadhaar PAN",
        "GST registration threshold goods services",
        "MSME subsidy scheme PMEGP CGTMSE eligibility",
        "zzz irrelevant query about pizza recipes and movies",
        "",
    ]:
        r = await provider.retrieve(q, user_id="u1", conversation_id="c1", limit=5)
        print(f"\nQUERY: {q[:60]!r}")
        print(f"  results={len(r)}")
        for s in r[:3]:
            print(
                f"   - source_id={s.get('source_id')} "
                f"page={s.get('page_or_section')} "
                f"score={s.get('retrieval_score')} "
                f"url={s.get('source_url')}"
            )
            excerpt = str(s.get("relevant_excerpt") or "")
            print(f"     excerpt: {excerpt[:110]}")

    print("\n=== E2E: Document Agent process_document ===")
    import fitz, tempfile
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    p = tmp / "gst.pdf"
    d = fitz.open()
    d.new_page().insert_text(
        (72, 72),
        "GST Registration Certificate\nGSTIN: 22AAAAA0000A1Z5\nLegal Name: Example Biz Pvt Ltd\nAddress: 123 MG Road, Bengaluru 560001",
        fontsize=10,
    )
    d.save(str(p))
    d.close()
    pd = process_document(file_path=str(p), business_context={}, service_type="gst_registration")
    print("  document_type:", pd["document_type"])
    print("  classification_confidence:", pd["classification_confidence"])
    print("  validation_status:", pd["validation_status"])
    print("  page_count:", pd["page_count"])
    fields = {
        k: (v.get("value"), v.get("confidence")) for k, v in pd["extracted_fields"].items()
    }
    print("  extracted_fields:", fields)

    print("\n=== E2E: Document matching ===")
    extracted = [
        {
            "document_id": "D1",
            "document_type": "pan",
            "classification_confidence": 0.9,
            "extraction_errors": [],
            "extracted_fields": {
                "pan_identifier": {"value": "ABCDE1234F", "confidence": 0.9}
            },
            "validation_status": "validated",
        },
        {
            "document_id": "D2",
            "document_type": "aadhaar",
            "classification_confidence": 0.85,
            "extraction_errors": [],
            "extracted_fields": {},
            "validation_status": "validated",
        },
    ]
    required = [
        {"name": "PAN card", "category": "pan", "mandatory": True},
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": True},
        {"name": "Bank statement", "category": "bank_statement", "mandatory": False},
    ]
    m = match_documents_to_requirements(extracted, required, service="gst_registration")
    print("  overall_status:", m["overall_status"])
    print("  available:", len(m["available_documents"]))
    print("  missing:", len(m["missing_documents"]))
    print("  missing names:", [x["name"] for x in m["missing_documents"]])
    print("  coverage:", m["checklist_coverage"])


asyncio.run(main())
