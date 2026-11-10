"""Local knowledge base for Indian MSME and business-related government schemes.

This module provides a structured, maintainable knowledge base that the
LocalFallbackProvider uses when Gemini is unavailable. All information
is sourced from official Indian government websites.

Each scheme entry contains:
- name: Scheme name
- description: Plain-language description
- eligibility: Who is eligible
- benefits: Key benefits
- required_documents: List of required documents
- application_procedure: How to apply
- official_url: Official government application URL
- official_source: Issuing authority
- last_verified_date: Date information was last verified
- keywords: Search keywords for matching
- category: Scheme category (registration, loan, subsidy, compliance, etc.)

KEEP THIS FILE SEPARATE FROM APPLICATION LOGIC so it can be updated
independently when government rules change.

DO NOT invent eligibility requirements, financial limits, benefits,
deadlines, or URLs. If information is uncertain, mark it as such.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any
import re


@dataclass
class SchemeEntry:
    """A single government scheme entry."""

    name: str
    description: str
    eligibility: str
    benefits: str
    required_documents: list[str]
    application_procedure: str
    official_url: str
    official_source: str
    last_verified_date: str
    keywords: list[str]
    category: str
    confidence_base: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "eligibility": self.eligibility,
            "benefits": self.benefits,
            "required_documents": self.required_documents,
            "application_procedure": self.application_procedure,
            "official_url": self.official_url,
            "issuing_authority": self.official_source,
            "official_url_field": self.official_url,
            "official_source_field": self.official_source,
            "last_verified_date": self.last_verified_date,
            "category": self.category,
            "confidence": self.confidence_base,
        }


# ---------------------------------------------------------------------------
# Knowledge base entries
# ---------------------------------------------------------------------------

SCHEMES: dict[str, SchemeEntry] = {}

# 1. Udyam Registration
SCHEMES["udyam_registration"] = SchemeEntry(
    name="Udyam Registration",
    description=(
        "Udyam Registration is the government registration for Micro, Small "
        "and Medium Enterprises (MSMEs) in India. It provides a unique "
        "identity and recognition number to MSMEs."
    ),
    eligibility=(
        "Any micro, small or medium enterprise as defined under the MSMED "
        "Act, 2006 can register. Classification is based on investment in "
        "plant and machinery or equipment and annual turnover."
    ),
    benefits=(
        "Access to collateral-free loans under CGTMSE, subsidies, easier "
        "bank loans, priority sector lending, and various government "
        "tenders reserved for MSMEs."
    ),
    required_documents=[
        "Aadhaar number of the proprietor/partner/director",
        "PAN card",
        "Business address proof",
        "Bank account details",
        "Investment and turnover details",
    ],
    application_procedure=(
        "Visit udyamregistration.gov.in, enter Aadhaar and PAN details, "
        "fill in enterprise information, submit self-declaration, and "
        "receive the Udyam Registration Number (URN) with e-certificate."
    ),
    official_url="https://udyamregistration.gov.in",
    official_source="Ministry of MSME, Government of India",
    last_verified_date="2024-06-01",
    keywords=[
        "udyam",
        "msme registration",
        "micro small medium enterprise",
        "udyam registration number",
        "urn",
        "msme certificate",
    ],
    category="registration",
    confidence_base=0.95,
)

# 2. PMEGP
SCHEMES["pmegp"] = SchemeEntry(
    name="PMEGP (Prime Minister's Employment Generation Programme)",
    description=(
        "PMEGP is a credit-linked subsidy programme for setting up new "
        "micro-enterprises in the non-farm sector, implemented through "
        "KVIC, state KVIC directorates, and district industries centres."
    ),
    eligibility=(
        "Any individual above 18 years of age. For projects above Rs. 10 "
        "lakh (manufacturing) or Rs. 5 lakh (service), education qualification "
        "of at least 8th pass is required. Self-help groups, charitable trusts, "
        "and cooperative societies are also eligible."
    ),
    benefits=(
        "Margin money subsidy of 15% to 35% of the project cost (up to "
        "Rs. 50 lakh for manufacturing, Rs. 20 lakh for service/business). "
        "Subsidy is higher for special categories and rural areas."
    ),
    required_documents=[
        "Project report",
        "Aadhaar card",
        "PAN card",
        "Caste certificate (if applicable)",
        "Education qualification certificate",
        "Bank account details",
        "Rent agreement or ownership proof of premises",
    ],
    application_procedure=(
        "Apply online at kvic.gov.in/pmegp or through the district "
        "industries centre. Submit project report and documents. "
        "Applications are forwarded to banks for loan sanction and "
        "subsidy claim."
    ),
    official_url="https://www.kvic.gov.in/pmegp",
    official_source="Khadi and Village Industries Commission (KVIC), Ministry of MSME",
    last_verified_date="2024-05-15",
    keywords=[
        "pmegp",
        "prime minister employment generation programme",
        "kvic",
        "self employment",
        "micro enterprise loan subsidy",
    ],
    category="subsidy",
    confidence_base=0.90,
)

# 3. MUDRA Loans
SCHEMES["mudra"] = SchemeEntry(
    name="MUDRA Loans (Micro Units Development and Refinance Agency)",
    description=(
        "MUDRA provides loans to non-corporate, non-farm small/micro "
        "enterprises through banks, NBFCs, and MFIs. Loans are "
        "categorized as Shishu, Kishor, and Tarun."
    ),
    eligibility=(
        "Small businesses, micro-enterprises, startups, and entrepreneurs "
        "in trading, manufacturing, services, or agriculture-related "
        "activities. No minimum credit score required for Shishu loans."
    ),
    benefits=(
        "Loans up to Rs. 10 lakh without collateral. Three categories: "
        "Shishu (up to Rs. 50,000), Kishor (Rs. 50,001 to Rs. 5 lakh), "
        "and Tarun (Rs. 5 lakh to Rs. 10 lakh)."
    ),
    required_documents=[
        "Business plan",
        "Aadhaar card",
        "PAN card",
        "Business address proof",
        "Bank statements",
        "Quotation for machinery/equipment (if applicable)",
    ],
    application_procedure=(
        "Apply through any bank, NBFC, or MFI that is a MUDRA lending "
        "institution. Submit application with business plan and documents. "
        "Loan sanctioned based on business viability and repayment capacity."
    ),
    official_url="https://www.mudra.org.in",
    official_source="Micro Units Development and Refinance Agency (MUDRA), Ministry of Finance",
    last_verified_date="2024-04-01",
    keywords=[
        "mudra",
        "mudra loan",
        "shishu",
        "kishor",
        "tarun",
        "micro units development refinance agency",
        "small business loan",
    ],
    category="loan",
    confidence_base=0.90,
)

# 4. Stand-Up India
SCHEMES["standup_india"] = SchemeEntry(
    name="Stand-Up India",
    description=(
        "Stand-Up India facilitates bank loans between Rs. 10 lakh and "
        "Rs. 1 crore to at least one Scheduled Caste/Scheduled Tribe "
        "borrower and at least one woman borrower per bank branch for "
        "setting up a greenfield enterprise."
    ),
    eligibility=(
        "SC/ST and/or women entrepreneurs above 18 years of age. "
        "Enterprise must be in manufacturing, services, trading, or "
        "agriculture-related activities. Existing businesses are not "
        "eligible (greenfield only)."
    ),
    benefits=(
        "Bank loans from Rs. 10 lakh to Rs. 1 crore. Composite loan "
        "(term loan + working capital) available. Repayment up to 7 "
        "years with moratorium up to 18 months."
    ),
    required_documents=[
        "Project report",
        "Aadhaar card",
        "PAN card",
        "Caste certificate (for SC/ST applicants)",
        "Bank account details",
        "Business premises proof",
        "Training certificate (EDP, if applicable)",
    ],
    application_procedure=(
        "Apply through standupmitra.in or any bank branch. Submit project "
        "proposal and documents. Bank conducts due diligence and sanctions "
        "loan based on eligibility."
    ),
    official_url="https://www.standupmitra.in",
    official_source="Department of Financial Services, Ministry of Finance",
    last_verified_date="2024-05-01",
    keywords=[
        "stand up india",
        "standup india",
        "sc st entrepreneur",
        "woman entrepreneur",
        "greenfield enterprise",
        "rs 10 lakh rs 1 crore loan",
    ],
    category="loan",
    confidence_base=0.90,
)

# 5. Startup India
SCHEMES["startup_india"] = SchemeEntry(
    name="Startup India",
    description=(
        "Startup India is an initiative to promote and support startups "
        "in India through tax benefits, easier compliance, funding support, "
        "and incubation ecosystem."
    ),
    eligibility=(
        "Entity incorporated as a private limited company, registered "
        "partnership firm, or limited liability partnership. Turnover "
        "should not exceed Rs. 100 crore in any financial year. Entity "
        "should be working towards innovation, development, or improvement "
        "of products/processes/services."
    ),
    benefits=(
        "Tax exemption under Section 80-IAC, self-certification compliance, "
        "easier public procurement norms, access to Fund of Funds for "
        "Startups, and startup patent support."
    ),
    required_documents=[
        "Certificate of incorporation/registration",
        "PAN card",
        "Aadhaar of directors/partners",
        "Brief description of innovation/business",
        "Pitch deck or presentation",
        "Recommendation letter from incubator (optional)",
    ],
    application_procedure=(
        "Register at startupindia.gov.in. Create profile, submit application "
        "with incorporation documents and business description. DPIIT "
        "reviews and issues recognition certificate if eligible."
    ),
    official_url="https://www.startupindia.gov.in",
    official_source="Department for Promotion of Industry and Internal Trade (DPIIT)",
    last_verified_date="2024-04-15",
    keywords=[
        "startup india",
        "dpiit",
        "startup recognition",
        "tax exemption section 80-iac",
        "innovation startup",
        "fund of funds for startups",
    ],
    category="registration",
    confidence_base=0.90,
)

# 6. CGTMSE
SCHEMES["cgtmse"] = SchemeEntry(
    name="CGTMSE (Credit Guarantee Fund Trust for Micro and Small Enterprises)",
    description=(
        "CGTMSE provides collateral-free credit guarantee cover for loans "
        "extended to micro and small enterprises by eligible lending "
        "institutions."
    ),
    eligibility=(
        "Micro and small enterprises engaged in manufacturing or service "
        "activities. Loan amount up to Rs. 5 crore. Existing and new "
        "enterprises are eligible."
    ),
    benefits=(
        "Collateral-free loans up to Rs. 5 crore. Credit guarantee cover "
        "up to 85% for micro enterprises and 75% for small enterprises. "
        "Reduced collateral requirements for banks."
    ),
    required_documents=[
        "Loan application form",
        "Project report",
        "Udyam Registration certificate",
        "Aadhaar card",
        "PAN card",
        "Bank account statements",
        "Security documents (if any)",
    ],
    application_procedure=(
        "Approach any eligible bank or financial institution. Mention "
        "CGTMSE coverage in the loan application. The lending institution "
        "obtains guarantee cover from CGTMSE after loan sanction."
    ),
    official_url="https://www.cgtmse.in",
    official_source="Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE), SIDBI/Ministry of MSME",
    last_verified_date="2024-05-01",
    keywords=[
        "cgtmse",
        "credit guarantee fund trust",
        "collateral free loan",
        "micro small enterprise loan guarantee",
        "rs 5 crore loan",
    ],
    category="loan",
    confidence_base=0.90,
)

# 7. GST Registration
SCHEMES["gst_registration"] = SchemeEntry(
    name="GST Registration",
    description=(
        "Goods and Services Tax (GST) registration is mandatory for "
        "businesses whose aggregate turnover exceeds the threshold limit "
        "or who make inter-state supplies."
    ),
    eligibility=(
        "Businesses with aggregate turnover exceeding Rs. 20 lakh "
        "(Rs. 10 lakh for special category states). Inter-state suppliers, "
        "e-commerce operators, and casual taxable persons must register "
        "regardless of turnover."
    ),
    benefits=(
        "Legal recognition as a supplier, ability to collect GST from "
        "customers, input tax credit on purchases, and compliance with "
        "indirect tax law."
    ),
    required_documents=[
        "PAN card of business/applicant",
        "Aadhaar card",
        "Business registration proof (partnership deed, incorporation certificate)",
        "Address proof of principal place of business",
        "Bank account details",
        "Digital signature (for companies/LLPs)",
        "Photograph of proprietor/partners/directors",
    ],
    application_procedure=(
        "Apply online at gst.gov.in through the GST portal. Fill Form GST "
        "REG-01 with business details and upload documents. Receive GSTIN "
        "after verification by the GST officer."
    ),
    official_url="https://www.gst.gov.in",
    official_source="Central Board of Indirect Taxes and Customs (CBIC), Ministry of Finance",
    last_verified_date="2024-06-15",
    keywords=[
        "gst",
        "gst registration",
        "goods and services tax",
        "gstin",
        "cbic",
        "gst threshold turnover",
    ],
    category="registration",
    confidence_base=0.95,
)

# 8. MSME Classification
SCHEMES["msme_classification"] = SchemeEntry(
    name="MSME Classification Criteria",
    description=(
        "MSMEs are classified based on investment in plant and machinery "
        "or equipment and annual turnover, as notified under the MSMED "
        "Act, 2006 (as revised)."
    ),
    eligibility=(
        "All enterprises engaged in manufacturing or production, "
        "preservation, or processing of goods, or providing/services."
    ),
    benefits=(
        "Determines eligibility for various government schemes, subsidies, "
        "priority sector lending, and MSME-specific benefits."
    ),
    required_documents=[
        "Investment details in plant and machinery/equipment",
        "Annual turnover details",
        "Audited financial statements (if applicable)",
    ],
    application_procedure=(
        "Classification is self-declared during Udyam Registration based "
        "on investment and turnover figures. No separate application needed."
    ),
    official_url="https://udyamregistration.gov.in",
    official_source="Ministry of MSME, Government of India",
    last_verified_date="2024-07-01",
    keywords=[
        "msme classification",
        "micro small medium enterprise definition",
        "investment limit msme",
        "turnover limit msme",
        "msmed act 2006",
    ],
    category="compliance",
    confidence_base=0.95,
)

# 9. Government Subsidies for Small Businesses
SCHEMES["government_subsidies"] = SchemeEntry(
    name="Government Subsidies for Small Businesses",
    description=(
        "Various central and state government schemes provide subsidies "
        "for capital investment, technology upgradation, marketing, and "
        "interest subvention to small businesses."
    ),
    eligibility=(
        "Varies by scheme. Generally, registered MSMEs, small manufacturers, "
        "and service providers are eligible. Specific criteria depend on "
        "the individual subsidy scheme."
    ),
    benefits=(
        "Capital subsidy, interest subvention on loans, technology "
        "upgradation assistance, marketing support, and reimbursement of "
        "certification costs."
    ),
    required_documents=[
        "Udyam Registration certificate",
        "Project report",
        "Quotations for machinery/equipment",
        "Bank sanction letter",
        "Audited accounts",
    ],
    application_procedure=(
        "Identify the relevant subsidy scheme, prepare project report, "
        "apply through the concerned ministry/department or nodal agency "
        "with required documents. Claims are processed after verification."
    ),
    official_url="https://msme.gov.in",
    official_source="Ministry of MSME, Government of India",
    last_verified_date="2024-05-15",
    keywords=[
        "subsidy",
        "capital subsidy",
        "interest subvention",
        "technology upgradation fund",
        "government subsidy small business",
        "msme subsidy scheme",
    ],
    category="subsidy",
    confidence_base=0.80,
)

# 10. Basic Business Compliance and Documentation
SCHEMES["business_compliance"] = SchemeEntry(
    name="Basic Business Compliance and Documentation",
    description=(
        "Overview of common compliance requirements for small businesses "
        "in India, including registrations, licenses, and periodic filings."
    ),
    eligibility=(
        "All registered business entities operating in India."
    ),
    benefits=(
        "Helps businesses avoid penalties, maintain legal status, and "
        "qualify for government schemes and bank loans."
    ),
    required_documents=[
        "PAN card",
        "Aadhaar card",
        "Business registration certificate",
        "GST registration certificate (if applicable)",
        "Shop and Establishment Act registration",
        "Trade license (if applicable)",
    ],
    application_procedure=(
        "Obtain PAN and Aadhaar, register the business entity, apply for "
        "GST registration if turnover exceeds threshold, obtain local "
        "trade license, and file periodic returns (GST, income tax)."
    ),
    official_url="https://msme.gov.in",
    official_source="Ministry of MSME, Government of India",
    last_verified_date="2024-06-01",
    keywords=[
        "business compliance",
        "business documentation",
        "trade license",
        "shop establishment act",
        "gst compliance",
        "income tax filing",
        "annual compliance",
    ],
    category="compliance",
    confidence_base=0.85,
)


class LocalKnowledgeBase:
    """In-memory knowledge base of government schemes.

    Provides methods to retrieve scheme information by keyword matching.
    All data is static and loaded from the SCHEMES dictionary.
    """

    def __init__(self) -> None:
        self._schemes = SCHEMES
        self._keyword_index = self._build_keyword_index()

    def _build_keyword_index(self) -> dict[str, list[str]]:
        """Build an inverted index from keywords to scheme IDs."""
        index: dict[str, list[str]] = {}
        for scheme_id, scheme in self._schemes.items():
            for keyword in scheme.keywords:
                index.setdefault(keyword.lower(), []).append(scheme_id)
            # Also index the scheme name words
            for word in scheme.name.lower().split():
                index.setdefault(word, []).append(scheme_id)
            # Index category
            index.setdefault(scheme.category, []).append(scheme_id)
        return index

    def get_all_schemes(self) -> list[SchemeEntry]:
        """Return all scheme entries."""
        return list(self._schemes.values())

    def get_scheme(self, scheme_id: str) -> SchemeEntry | None:
        """Return a scheme by its ID."""
        return self._schemes.get(scheme_id)

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search the knowledge base for relevant schemes.

        Uses keyword matching with confidence scoring. Exact phrase
        matches (scheme name) score higher than keyword matches.

        Args:
            query: User search query.
            limit: Maximum number of results to return.

        Returns:
            Dictionary with matched schemes, confidence, and match type.
            Returns empty matched_schemes if no results found.
        """
        if not query or not query.strip():
            return {
                "matched_schemes": [],
                "confidence": 0.0,
                "match_type": "none",
            }

        query_lower = query.lower().strip()
        query_words = [w for w in re.split(r"\s+", query_lower) if w]

        scheme_scores: dict[str, float] = {}
        matched_keywords: dict[str, list[str]] = {}

        # Check for exact scheme name match
        for scheme_id, scheme in self._schemes.items():
            scheme_name_lower = scheme.name.lower()
            if scheme_name_lower in query_lower:
                scheme_scores[scheme_id] = 1.0
                matched_keywords[scheme_id] = [scheme.name]

        # Keyword matching
        for word in query_words:
            if word in self._keyword_index:
                for scheme_id in self._keyword_index[word]:
                    if scheme_id not in scheme_scores:
                        scheme_scores[scheme_id] = 0.0
                    scheme_scores[scheme_id] += 0.15
                    matched_keywords.setdefault(scheme_id, []).append(word)

        # Boost scores based on keyword density
        for scheme_id in scheme_scores:
            base = self._schemes[scheme_id].confidence_base
            score = min(scheme_scores[scheme_id], 1.0)
            scheme_scores[scheme_id] = score * base

        # Sort by score descending
        ranked = sorted(scheme_scores.items(), key=lambda x: x[1], reverse=True)

        matched_schemes: list[dict[str, Any]] = []
        for scheme_id, score in ranked[:limit]:
            scheme = self._schemes[scheme_id]
            scheme_dict = scheme.to_dict()
            scheme_dict["confidence"] = round(score, 2)
            scheme_dict["matched_keywords"] = matched_keywords.get(scheme_id, [])
            matched_schemes.append(scheme_dict)

        # Determine match type
        if matched_schemes:
            top_score = matched_schemes[0]["confidence"]
            match_type = "exact" if top_score >= 0.9 else "keyword"
        else:
            match_type = "none"

        return {
            "matched_schemes": matched_schemes,
            "confidence": matched_schemes[0]["confidence"] if matched_schemes else 0.0,
            "match_type": match_type,
            "total_found": len(matched_schemes),
        }

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Retrieve relevant schemes from the knowledge base.

        Async wrapper around `search` for compatibility with the
        provider interface.

        Args:
            query: User search query.
            limit: Maximum number of results to return.

        Returns:
            Dictionary with matched schemes, confidence, and match type.
        """
        return self.search(query, limit=limit)


# Module-level singleton
_knowledge_base: LocalKnowledgeBase | None = None


def get_knowledge_base() -> LocalKnowledgeBase:
    """Return the singleton LocalKnowledgeBase instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = LocalKnowledgeBase()
    return _knowledge_base


__all__ = [
    "SchemeEntry",
    "LocalKnowledgeBase",
    "SCHEMES",
    "get_knowledge_base",
]
