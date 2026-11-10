"""Document classification for user-uploaded PDFs.

Hybrid approach: rule-based keyword matching + text signals. Returns
confidence and allows 'other/unknown' classification. Never assumes
every PDF belongs to a known category.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.config.logging_config import get_logger
from rag.config.settings import settings
from rag.documents.schemas import DocumentClassification
from rag.ingestion.pdf_extractor import extract_pdf
from rag.ingestion.text_cleaner import clean_text

logger = get_logger("classifier")


@dataclass
class ClassifiedDocument:
    document_type: str
    confidence: float
    method: str
    reasons: list[str]
    extracted_text: str


# Keyword signals per category (lowercase). Weights reflect specificity.
CATEGORY_KEYWORDS = {
    "aadhaar": {
        "keywords": ["aadhaar", "uidai", "enrolment", "enrollment", "virtual id", "vid"],
        "weight": 1.0,
    },
    "pan": {
        "keywords": ["income tax", "permanent account number", "pan", "govt of india"],
        "weight": 0.9,
    },
    "gst": {
        "keywords": ["gstin", "goods and services tax", "gst registration", "gst return"],
        "weight": 1.0,
    },
    "udyam": {
        "keywords": ["udyam", "msme", "udyam registration", "ministry of msme"],
        "weight": 1.0,
    },
    "business_registration": {
        "keywords": [
            "certificate of incorporation", "memorandum of association",
            "partnership deed", "registration certificate", "registrar of companies",
            "roc", "llp",
        ],
        "weight": 0.85,
    },
    "address_proof": {
        "keywords": [
            "utility bill", "electricity bill", "water bill", "telephone bill",
            "property tax", "rent agreement", "lease",
        ],
        "weight": 0.75,
    },
    "bank_statement": {
        "keywords": [
            "bank statement", "account statement", "passbook", "branch",
            "ifsc", "account number", "balance",
        ],
        "weight": 0.8,
    },
}

KNOWN_CATEGORIES = set(CATEGORY_KEYWORDS.keys())


def _score_category(text_lower: str, category: str, info: dict) -> float:
    score = 0.0
    matched: list[str] = []
    for kw in info["keywords"]:
        if kw in text_lower:
            score += info["weight"]
            matched.append(kw)
    return score, matched


def classify_document(
    *,
    file_path: str | Path,
    text: str | None = None,
) -> ClassifiedDocument:
    """Classify a document using rule-based keyword matching.

    Args:
        file_path: Path to the PDF.
        text: Pre-extracted text (if None, text is extracted from PDF).

    Returns:
        ClassifiedDocument with type, confidence, method, reasons.
    """
    if text is None:
        try:
            extraction = extract_pdf(file_path, min_chars_for_text=1)
            text = "\n".join(p.text for p in extraction.pages)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Text extraction failed during classification: %s", exc)
            text = ""

    cleaned = clean_text(text)
    text_lower = cleaned.lower()

    best_category = "other/unknown"
    best_score = 0.0
    best_reasons: list[str] = []

    for category, info in CATEGORY_KEYWORDS.items():
        score, matched = _score_category(text_lower, category, info)
        if score > best_score:
            best_score = score
            best_category = category
            best_reasons = matched

    # Normalize confidence: cap based on score; multiple signals => higher
    confidence = min(best_score / 3.0, 1.0)
    if best_category == "other/unknown":
        confidence = 0.0
        best_reasons = ["No category-specific keywords detected"]

    method = "rule_based"
    if confidence >= 0.5:
        confidence = round(confidence, 2)
    else:
        confidence = round(confidence, 2)
        best_category = "other/unknown"
        confidence = 0.0
        best_reasons = ["Confidence below threshold; classified as other/unknown"]

    logger.info(
        "Classified document as %s (confidence=%s)", best_category, confidence
    )

    return ClassifiedDocument(
        document_type=best_category,
        confidence=confidence,
        method=method,
        reasons=best_reasons,
        extracted_text=cleaned,
    )


def classification_to_schema(classified: ClassifiedDocument) -> DocumentClassification:
    return DocumentClassification(
        document_type=classified.document_type,
        confidence=classified.confidence,
        method=classified.method,
        reasons=classified.reasons,
    )
