"""Scheme Recommendations API router.

Provides authenticated endpoints for personalized scheme recommendations:
- POST /api/v1/recommendations - Get personalized scheme recommendations
- GET /api/v1/recommendations - List cached recommendations
- GET /api/v1/recommendations/{recommendation_id} - Get recommendation details
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationResponse,
    RecommendationRequest,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
from app.services.eligibility_engine.rule_registry import RuleRegistry
from app.services.ownership import OwnershipService, ResourceNotFoundError

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


async def get_eligibility_engine(
    db: AsyncSession = Depends(get_db),
) -> EligibilityEngine:
    """Dependency to get EligibilityEngine instance."""
    rule_registry = RuleRegistry(db)
    return EligibilityEngine(
        registry=rule_registry,
        evaluator=RuleEvaluator(),
    )


async def get_ownership_service(
    db: AsyncSession = Depends(get_db),
) -> OwnershipService:
    """Dependency to get OwnershipService instance."""
    return OwnershipService(db)


@router.post(
    "/",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalized scheme recommendations",
    description=(
        "Evaluate eligibility for government schemes based on the user's "
        "business profile and return personalized recommendations with "
        "eligibility status, explanations, and required documents."
    ),
)
async def get_recommendations(
    request: RecommendationRequest,
    eligibility_engine: EligibilityEngine = Depends(get_eligibility_engine),
    ownership: OwnershipService = Depends(get_ownership_service),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationResponse:
    """Get personalized scheme recommendations for a business profile.

    - Validates business profile ownership
    - Evaluates eligibility for all registered schemes
    - Returns ranked recommendations with explanations
    - Identifies missing information and required documents
    - Persists recommendations for later retrieval
    """
    # Validate business profile ownership
    try:
        await ownership.get_user_business_profile(current_user.id, request.business_profile_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        )

    # Get business profile for attributes
    from app.models import BusinessProfile
    from sqlalchemy import select

    result = await eligibility_engine.registry.db.execute(
        select(BusinessProfile).where(BusinessProfile.id == request.business_profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        )

    # Build business attributes from profile
    business_attributes = _build_business_attributes(profile)

    # Determine which schemes to evaluate
    scheme_names = _get_applicable_schemes(profile, request.service_filter)

    recommendations = []
    missing_info_fields = set()
    persisted_recommendations = []

    for scheme_name in scheme_names:
        try:
            from app.services.eligibility import EligibilityAssessmentRequest

            assessment_request = EligibilityAssessmentRequest(
                user_id=current_user.id,
                business_profile_id=request.business_profile_id,
                scheme_name=scheme_name,
                registration_type=scheme_name,
                business_attributes=business_attributes,
                missing_information=[],
                context={
                    "trigger": "recommendation",
                    "profile_id": str(request.business_profile_id),
                },
            )

            assessment = await eligibility_engine.evaluate(assessment_request)

            # Build recommendation
            recommendation = _build_recommendation(
                scheme_name=scheme_name,
                assessment=assessment,
                business_attributes=business_attributes,
                profile=profile,
            )
            recommendations.append(recommendation)

            # Persist recommendation to database
            from app.models import Recommendation
            import uuid

            persisted_rec = Recommendation(
                id=uuid.uuid4(),
                business_profile_id=request.business_profile_id,
                user_id=current_user.id,
                category=recommendation.scheme.category,
                title=recommendation.scheme.name,
                description=recommendation.scheme.description,
                recommendation_status="generated",
                eligibility_status=recommendation.eligibility_status,
                explanation=recommendation.explanation,
                evidence={
                    "matched_rules": recommendation.matched_rules,
                    "failed_rules": recommendation.failed_rules,
                    "required_documents": recommendation.required_documents,
                    "official_sources": recommendation.official_sources,
                    "missing_information": recommendation.missing_information,
                },
            )
            eligibility_engine.registry.db.add(persisted_rec)
            persisted_recommendations.append(persisted_rec)

            # Track missing information
            if assessment.missing_information:
                missing_info_fields.update(assessment.missing_information)

        except Exception as e:
            # Log but continue with other schemes
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Eligibility evaluation failed for {scheme_name}: {e}")

    # Commit all persisted recommendations
    if persisted_recommendations:
        await eligibility_engine.registry.db.commit()
        for rec in persisted_recommendations:
            await eligibility_engine.registry.db.refresh(rec)

    # Sort: eligible first, then potentially_eligible, then needs_info, then ineligible
    priority_order = {"eligible": 0, "potentially_eligible": 1, "needs_info": 2, "ineligible": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.eligibility_status, 4))

    return RecommendationResponse(
        business_profile_id=request.business_profile_id,
        total_schemes_evaluated=len(recommendations),
        eligible_count=sum(1 for r in recommendations if r.eligibility_status == "eligible"),
        potentially_eligible_count=sum(1 for r in recommendations if r.eligibility_status == "potentially_eligible"),
        needs_info_count=sum(1 for r in recommendations if r.eligibility_status == "needs_info"),
        ineligible_count=sum(1 for r in recommendations if r.eligibility_status == "ineligible"),
        recommendations=recommendations,
        missing_information=sorted(list(missing_info_fields)),
    )


@router.get(
    "/",
    response_model=RecommendationListResponse,
    summary="List cached recommendations",
    description="List previously generated recommendations for the user's business profiles.",
)
async def list_recommendations(
    business_profile_id: UUID | None = None,
    eligibility_engine: EligibilityEngine = Depends(get_eligibility_engine),
    ownership: OwnershipService = Depends(get_ownership_service),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationListResponse:
    """List cached recommendations for the user."""
    from app.models import BusinessProfile, Recommendation
    from app.schemas.recommendation import RecommendationDetail, SchemeDetail
    from sqlalchemy import select

    query = select(Recommendation).where(Recommendation.user_id == current_user.id)
    if business_profile_id:
        # Validate ownership
        try:
            await ownership.get_user_business_profile(current_user.id, business_profile_id)
        except ResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found",
            )
        query = query.where(Recommendation.business_profile_id == business_profile_id)

    query = query.order_by(Recommendation.created_at.desc())
    result = await eligibility_engine.registry.db.execute(query)
    recommendations = list(result.scalars().all())

    # Convert stored recommendations to full response format
    response_items = []
    for rec in recommendations:
        evidence = rec.evidence or {}
        scheme_detail = SchemeDetail(
            id=str(rec.id),
            name=rec.title,
            full_name=rec.title,
            category=rec.category,
            ministry="Government of India",
            description=rec.description,
            official_url=evidence.get("official_sources", [{}])[0].get("url", "") if evidence else "",
        )
        response_items.append(RecommendationResponse(
            business_profile_id=rec.business_profile_id or rec.id,
            total_schemes_evaluated=1,
            eligible_count=1 if rec.eligibility_status == "eligible" else 0,
            potentially_eligible_count=1 if rec.eligibility_status == "potentially_eligible" else 0,
            needs_info_count=1 if rec.eligibility_status == "needs_info" else 0,
            ineligible_count=1 if rec.eligibility_status == "ineligible" else 0,
            recommendations=[RecommendationDetail(
                scheme=scheme_detail,
                eligibility_status=rec.eligibility_status,
                explanation=rec.explanation or "",
                required_documents=evidence.get("required_documents", []) if evidence else [],
                missing_information=evidence.get("missing_information", []) if evidence else [],
                official_sources=evidence.get("official_sources", []) if evidence else [],
                matched_rules=evidence.get("matched_rules", []) if evidence else [],
                failed_rules=evidence.get("failed_rules", []) if evidence else [],
            )],
            missing_information=evidence.get("missing_information", []) if evidence else [],
        ))

    return RecommendationListResponse(
        items=response_items,
        total=len(response_items),
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Get recommendation details",
    description="Get detailed information about a specific recommendation.",
)
async def get_recommendation(
    recommendation_id: UUID,
    eligibility_engine: EligibilityEngine = Depends(get_eligibility_engine),
    ownership: OwnershipService = Depends(get_ownership_service),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationResponse:
    """Get a specific recommendation by ID."""
    from app.models import Recommendation
    from sqlalchemy import select

    result = await eligibility_engine.registry.db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id,
        )
    )
    recommendation = result.scalar_one_or_none()

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    # Convert to response model
    from app.schemas.recommendation import RecommendationDetail, SchemeDetail

    scheme_detail = SchemeDetail(
        id=str(recommendation.id),
        name=recommendation.title,
        full_name=recommendation.title,
        category=recommendation.category,
        ministry="Government of India",
        description=recommendation.description,
        official_url=recommendation.evidence.get("official_sources", [{}])[0].get("url", "") if recommendation.evidence else "",
    )

    return RecommendationResponse(
        business_profile_id=recommendation.business_profile_id or recommendation_id,
        total_schemes_evaluated=1,
        eligible_count=1 if recommendation.eligibility_status == "eligible" else 0,
        potentially_eligible_count=1 if recommendation.eligibility_status == "potentially_eligible" else 0,
        needs_info_count=1 if recommendation.eligibility_status == "needs_info" else 0,
        ineligible_count=1 if recommendation.eligibility_status == "ineligible" else 0,
        recommendations=[RecommendationDetail(
            scheme=scheme_detail,
            eligibility_status=recommendation.eligibility_status,
            explanation=recommendation.explanation or "",
            required_documents=recommendation.evidence.get("required_documents", []) if recommendation.evidence else [],
            missing_information=recommendation.evidence.get("missing_information", []) if recommendation.evidence else [],
            official_sources=recommendation.evidence.get("official_sources", []) if recommendation.evidence else [],
            matched_rules=recommendation.evidence.get("matched_rules", []) if recommendation.evidence else [],
            failed_rules=recommendation.evidence.get("failed_rules", []) if recommendation.evidence else [],
        )],
        missing_information=recommendation.evidence.get("missing_information", []) if recommendation.evidence else [],
    )


def _build_business_attributes(profile: "BusinessProfile") -> dict[str, str]:
    """Build business attributes dictionary from profile."""
    attrs = {
        "business_name": profile.business_name,
        "business_type": profile.business_type,
        "industry": profile.industry,
        "state": profile.state,
        "district": profile.district,
        "business_structure": profile.business_structure,
        "business_stage": profile.business_stage,
    }

    if profile.annual_turnover is not None:
        attrs["annual_turnover"] = str(profile.annual_turnover)
    if profile.employee_count is not None:
        attrs["employee_count"] = str(profile.employee_count)
    if profile.city:
        attrs["city"] = profile.city
    if profile.pincode:
        attrs["pincode"] = profile.pincode
    if profile.udyam_number:
        attrs["udyam_number"] = profile.udyam_number
    if profile.gstin:
        attrs["gstin"] = profile.gstin
    if profile.date_of_establishment:
        attrs["establishment_date"] = profile.date_of_establishment.isoformat()
    if profile.products_services:
        attrs["products_services"] = ", ".join(profile.products_services)
    if profile.operating_mode:
        attrs["operating_mode"] = profile.operating_mode
    if profile.sales_channels:
        attrs["sales_channels"] = ", ".join(profile.sales_channels)
    if profile.woman_owned is not None:
        attrs["woman_owned"] = str(profile.woman_owned).lower()

    return attrs


def _get_applicable_schemes(profile: "BusinessProfile", service_filter: str | None) -> list[str]:
    """Determine which schemes to evaluate based on profile and filter."""
    # Default schemes applicable to most businesses
    all_schemes = [
        "udyam_registration",
        "gst_registration",
        "pmegp",
        "cgtmse",
        "pm_svanidhi",
        "standup_india",
        "msme_champions",
        "lean_manufacturing",
        "digital_msme",
        "incubation_scheme",
    ]

    if service_filter:
        return [s for s in all_schemes if service_filter.lower() in s.lower()]

    # Filter based on business profile
    applicable = []
    for scheme in all_schemes:
        if _is_scheme_applicable(scheme, profile):
            applicable.append(scheme)

    return applicable


def _is_scheme_applicable(scheme: str, profile: "BusinessProfile") -> bool:
    """Check if a scheme is applicable to the business profile."""
    # Udyam registration - all MSMEs
    if scheme == "udyam_registration":
        return True

    # GST registration - based on turnover
    if scheme == "gst_registration":
        # All businesses should check GST
        return True

    # PMEGP - new projects, manufacturing/service
    if scheme == "pmegp":
        return profile.business_stage in ("Idea", "Startup")

    # CGTMSE - micro and small enterprises
    if scheme == "cgtmse":
        return True

    # PM SVANidhi - street vendors
    if scheme == "pm_svanidhi":
        return profile.business_type.lower() in ("retail", "street_vendor", "hawkers")

    # Stand-Up India - SC/ST/women entrepreneurs
    if scheme == "standup_india":
        return profile.woman_owned is True

    # MSME Champions - existing MSMEs
    if scheme == "msme_champions":
        return profile.udyam_number is not None

    # Lean Manufacturing - manufacturing businesses
    if scheme == "lean_manufacturing":
        return "manufactur" in profile.business_type.lower() or "manufactur" in profile.industry.lower()

    # Digital MSME - all businesses
    if scheme == "digital_msme":
        return True

    # Incubation - startups
    if scheme == "incubation_scheme":
        return profile.business_stage in ("Idea", "Startup")

    return True


def _build_recommendation(
    scheme_name: str,
    assessment: Any,
    business_attributes: dict[str, str],
    profile: "BusinessProfile",
) -> "RecommendationDetail":
    """Build a recommendation detail from eligibility assessment."""
    from app.schemas.recommendation import RecommendationDetail, SchemeDetail

    # Get scheme details
    scheme_detail = _get_scheme_detail(scheme_name)

    # Determine eligibility status
    eligibility_status = assessment.assessment_status.value if hasattr(assessment.assessment_status, "value") else str(assessment.assessment_status)

    # Build explanation
    explanation = _build_explanation(scheme_name, assessment, business_attributes)

    # Get required documents
    required_documents = _get_required_documents(scheme_name, assessment)

    # Get official sources
    official_sources = _get_official_sources(scheme_name)

    return RecommendationDetail(
        scheme=scheme_detail,
        eligibility_status=eligibility_status,
        explanation=explanation,
        required_documents=required_documents,
        missing_information=assessment.missing_information if hasattr(assessment, "missing_information") else [],
        official_sources=official_sources,
        matched_rules=[rule.rule_name for rule in assessment.matched_rules] if hasattr(assessment, "matched_rules") else [],
        failed_rules=[rule.rule_name for rule in assessment.failed_rules] if hasattr(assessment, "failed_rules") else [],
    )


def _get_scheme_detail(scheme_name: str) -> "SchemeDetail":
    """Get scheme metadata."""
    from app.schemas.recommendation import SchemeDetail

    schemes = {
        "udyam_registration": SchemeDetail(
            id="udyam_registration",
            name="Udyam Registration",
            full_name="Udyam Registration - MSME Certification",
            category="Central",
            ministry="Ministry of MSME, Government of India",
            description="Official MSME registration providing access to priority lending, subsidies, tax benefits, and government tender preferences.",
            official_url="https://udyamregistration.gov.in",
        ),
        "gst_registration": SchemeDetail(
            id="gst_registration",
            name="GST Registration",
            full_name="Goods and Services Tax Registration",
            category="Central",
            ministry="Central Board of Indirect Taxes and Customs (CBIC)",
            description="Mandatory registration for businesses exceeding turnover threshold. Enables input tax credit and interstate supply.",
            official_url="https://www.gst.gov.in",
        ),
        "pmegp": SchemeDetail(
            id="pmegp",
            name="PMEGP",
            full_name="Prime Minister's Employment Generation Programme",
            category="Central",
            ministry="Ministry of MSME / KVIC",
            description="Subsidy up to 35% (rural) / 25% (urban) on project cost for new micro enterprises. Max ₹25L manufacturing, ₹10L service.",
            official_url="https://www.kvic.org.in/pmegp",
        ),
        "cgtmse": SchemeDetail(
            id="cgtmse",
            name="CGTMSE",
            full_name="Credit Guarantee Fund Trust for Micro and Small Enterprises",
            category="Banking",
            ministry="Ministry of MSME / SIDBI",
            description="Collateral-free loans up to ₹2Cr for micro and small enterprises through member lending institutions.",
            official_url="https://www.cgtmse.in",
        ),
        "pm_svanidhi": SchemeDetail(
            id="pm_svanidhi",
            name="PM SVANidhi",
            full_name="PM Street Vendor's AtmaNirbhar Nidhi",
            category="Central",
            ministry="Ministry of Housing and Urban Affairs",
            description="Micro credit facility up to ₹50,000 for street vendors with interest subsidy and digital transaction incentives.",
            official_url="https://pmsvanidhi.mohua.gov.in",
        ),
        "standup_india": SchemeDetail(
            id="standup_india",
            name="Stand-Up India",
            full_name="Stand-Up India Scheme",
            category="Central",
            ministry="Department of Financial Services",
            description="Bank loans between ₹10L and ₹1Cr to SC/ST and/or women entrepreneurs for greenfield projects.",
            official_url="https://www.standupmitra.in",
        ),
        "msme_champions": SchemeDetail(
            id="msme_champions",
            name="MSME Champions",
            full_name="MSME Champions Scheme",
            category="Central",
            ministry="Ministry of MSME",
            description="Support for technology upgradation, quality certification, and market access for existing MSMEs.",
            official_url="https://champions.gov.in",
        ),
        "lean_manufacturing": SchemeDetail(
            id="lean_manufacturing",
            name="Lean Manufacturing",
            full_name="Lean Manufacturing Competitiveness Scheme for MSMEs",
            category="Central",
            ministry="Ministry of MSME",
            description="Financial assistance for implementing lean manufacturing techniques to improve productivity and reduce waste.",
            official_url="https://msme.gov.in/schemes/lean-manufacturing",
        ),
        "digital_msme": SchemeDetail(
            id="digital_msme",
            name="Digital MSME",
            full_name="Digital MSME Scheme",
            category="Central",
            ministry="Ministry of MSME",
            description="Support for digital adoption including ERP, CRM, e-commerce, and cloud solutions for MSMEs.",
            official_url="https://msme.gov.in/schemes/digital-msme",
        ),
        "incubation_scheme": SchemeDetail(
            id="incubation_scheme",
            name="Incubation Support",
            full_name="Support for Entrepreneurial and Managerial Development of MSMEs through Incubators",
            category="Central",
            ministry="Ministry of MSME",
            description="Funding and mentorship support for innovative ideas through approved business incubators.",
            official_url="https://msme.gov.in/schemes/incubation",
        ),
    }

    return schemes.get(scheme_name, SchemeDetail(
        id=scheme_name,
        name=scheme_name.replace("_", " ").title(),
        full_name=scheme_name.replace("_", " ").title(),
        category="Other",
        ministry="Government of India",
        description="Government scheme for MSMEs.",
        official_url="https://www.myscheme.gov.in",
    ))


def _build_explanation(
    scheme_name: str,
    assessment: Any,
    business_attributes: dict[str, str],
) -> str:
    """Build human-readable explanation for the recommendation."""
    status = assessment.assessment_status.value if hasattr(assessment.assessment_status, "value") else str(assessment.assessment_status)

    explanations = {
        "eligible": f"Your business meets all eligibility criteria for {scheme_name.replace('_', ' ').title()}.",
        "potentially_eligible": f"Your business appears to meet most criteria for {scheme_name.replace('_', ' ').title()}, but some information is missing for full verification.",
        "needs_info": f"Cannot determine eligibility for {scheme_name.replace('_', ' ').title()} - additional information is required.",
        "ineligible": f"Your business does not currently meet the eligibility criteria for {scheme_name.replace('_', ' ').title()}.",
    }

    base = explanations.get(status, f"Assessment completed for {scheme_name.replace('_', ' ').title()}.")

    # Add context about matched/failed rules
    if hasattr(assessment, "matched_rules") and assessment.matched_rules:
        matched_names = [r.rule_name for r in assessment.matched_rules]
        base += f" Met criteria: {', '.join(matched_names)}."

    if hasattr(assessment, "failed_rules") and assessment.failed_rules:
        failed_names = [r.rule_name for r in assessment.failed_rules]
        base += f" Unmet criteria: {', '.join(failed_names)}."

    # Add missing information
    if hasattr(assessment, "missing_information") and assessment.missing_information:
        base += f" Missing: {', '.join(assessment.missing_information)}."

    return base


def _get_required_documents(scheme_name: str, assessment: Any) -> list[str]:
    """Get required documents for a scheme based on assessment."""
    base_documents = {
        "udyam_registration": ["Aadhaar Card", "PAN Card", "Business Address Proof", "Bank Account Details"],
        "gst_registration": ["PAN Card", "Aadhaar Card", "Business Registration Certificate", "Address Proof", "Bank Statement"],
        "pmegp": ["Aadhaar Card", "PAN Card", "Project Report", "Caste Certificate (if applicable)", "Rural: Gram Panchayat NOC"],
        "cgtmse": ["Business Registration", "Project Report", "Financial Projections", "KYC Documents"],
        "pm_svanidhi": ["Aadhaar Card", "Vendor Certificate", "Bank Account Details"],
        "standup_india": ["Caste Certificate", "Aadhaar Card", "PAN Card", "Project Report", "Bank Statements"],
        "msme_champions": ["Udyam Registration", "GST Registration", "Quality Certificates"],
        "lean_manufacturing": ["Udyam Registration", "Business Plan", "Implementation Proposal"],
        "digital_msme": ["Udyam Registration", "GST Registration", "Digital Adoption Plan"],
        "incubation_scheme": ["Business Idea Proposal", "Incubator Acceptance Letter", "Team Details"],
    }

    return base_documents.get(scheme_name, ["Business Registration", "PAN Card", "Aadhaar Card"])


def _get_official_sources(scheme_name: str) -> list[dict[str, str]]:
    """Get official source references for a scheme."""
    sources = {
        "udyam_registration": [
            {"title": "Udyam Registration Portal", "url": "https://udyamregistration.gov.in", "authority": "Ministry of MSME"},
        ],
        "gst_registration": [
            {"title": "GST Portal", "url": "https://www.gst.gov.in", "authority": "CBIC"},
        ],
        "pmegp": [
            {"title": "PMEGP Guidelines", "url": "https://www.kvic.org.in/pmegp", "authority": "KVIC / Ministry of MSME"},
        ],
        "cgtmse": [
            {"title": "CGTMSE Official Site", "url": "https://www.cgtmse.in", "authority": "SIDBI / Ministry of MSME"},
        ],
        "pm_svanidhi": [
            {"title": "PM SVANidhi Portal", "url": "https://pmsvanidhi.mohua.gov.in", "authority": "Ministry of Housing and Urban Affairs"},
        ],
        "standup_india": [
            {"title": "Stand-Up India Portal", "url": "https://www.standupmitra.in", "authority": "Department of Financial Services"},
        ],
    }

    default = [
        {"title": "myScheme Portal", "url": "https://www.myscheme.gov.in", "authority": "Government of India"},
    ]

    return sources.get(scheme_name, default)