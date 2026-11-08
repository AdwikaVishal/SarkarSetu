"""Field mapper for document intelligence.

Maps extracted document fields to business profile fields and detects conflicts.
"""

from typing import Any

from app.models.business import BusinessProfile
from app.services.document_intelligence.document_errors import ProvenanceError
from app.services.document_intelligence.schemas import (
    FieldConflict,
    FieldType,
    NormalizedField,
)

# Mapping from FieldType to BusinessProfile attribute names
FIELD_TYPE_TO_PROFILE_ATTR = {
    FieldType.BUSINESS_NAME: "business_name",
    FieldType.LEGAL_NAME: "business_name",  # May map to same field
    FieldType.PAN: "pan_number",  # Note: BusinessProfile doesn't have pan_number yet
    FieldType.GSTIN: "gstin",
    FieldType.UDYAM_NUMBER: "udyam_number",
    FieldType.BUSINESS_ADDRESS: "address",  # Note: BusinessProfile doesn't have address field
    FieldType.PINCODE: "pincode",
    FieldType.STATE: "state",
    FieldType.CITY: "city",
    FieldType.ESTABLISHMENT_DATE: "date_of_establishment",
    FieldType.BUSINESS_ACTIVITY: "products_services",  # Closest match
    FieldType.OWNERSHIP_DETAILS: "woman_owned",  # Closest match - partial
}


# Fields that are supported for direct profile update
SUPPORTED_PROFILE_FIELDS = {
    "business_name",
    "gstin",
    "udyam_number",
    "pincode",
    "state",
    "city",
    "date_of_establishment",
    "woman_owned",
}


class FieldMapper:
    """Maps extracted fields to business profile and detects conflicts."""

    def __init__(self) -> None:
        self.field_to_attr = FIELD_TYPE_TO_PROFILE_ATTR

    def get_profile_attribute(self, field_type: FieldType) -> str | None:
        """Get the business profile attribute name for a field type."""
        return self.field_to_attr.get(field_type)

    def is_supported_for_update(self, field_type: FieldType) -> bool:
        """Check if a field type can be used to update the business profile."""
        attr = self.get_profile_attribute(field_type)
        return attr in SUPPORTED_PROFILE_FIELDS if attr else False

    def extract_profile_value(
        self, profile: BusinessProfile, field_type: FieldType
    ) -> Any:
        """Extract current value from business profile for a field type."""
        attr = self.get_profile_attribute(field_type)
        if not attr:
            return None
        return getattr(profile, attr, None)

    def detect_conflicts(
        self,
        profile: BusinessProfile,
        normalized_fields: list[NormalizedField],
    ) -> list[FieldConflict]:
        """Detect conflicts between profile values and normalized extracted fields.

        Args:
            profile: The business profile to compare against.
            normalized_fields: Normalized fields from document extraction.

        Returns:
            List of detected conflicts.
        """
        conflicts = []

        for field in normalized_fields:
            if not self.is_supported_for_update(field.field_type):
                continue

            existing_value = self.extract_profile_value(profile, field.field_type)

            # Skip if no existing value (no conflict)
            if existing_value is None:
                continue

            # Normalize both for comparison
            existing_str = str(existing_value).strip()
            extracted_str = field.value.strip()

            # Skip if values match (case-insensitive for strings)
            if existing_str.lower() == extracted_str.lower():
                continue

            # Determine conflict reason
            if field.field_type in (FieldType.PAN, FieldType.GSTIN, FieldType.UDYAM_NUMBER):
                conflict_reason = "identifier_mismatch"
                severity = "high"
            elif field.field_type in (FieldType.STATE, FieldType.CITY, FieldType.PINCODE):
                conflict_reason = "address_mismatch"
                severity = "medium"
            elif field.field_type == FieldType.BUSINESS_NAME:
                conflict_reason = "name_mismatch"
                severity = "high"
            elif field.field_type == FieldType.ESTABLISHMENT_DATE:
                conflict_reason = "date_mismatch"
                severity = "medium"
            else:
                conflict_reason = "value_mismatch"
                severity = "medium"

            conflict = FieldConflict(
                field_type=field.field_type,
                existing_value=existing_str,
                extracted_value=field.source_field_raw_value,
                normalized_value=field.value,
                confidence=field.confidence,
                conflict_reason=conflict_reason,
                source_document_id=field.source_document_id,
                severity=severity,
            )
            conflicts.append(conflict)

        return conflicts

    def get_update_candidates(
        self,
        profile: BusinessProfile,
        normalized_fields: list[NormalizedField],
        conflicts: list[FieldConflict],
    ) -> list[NormalizedField]:
        """Get fields that can be used to update the profile (no conflicts).

        Args:
            profile: Business profile.
            normalized_fields: Normalized extracted fields.
            conflicts: Previously detected conflicts.

        Returns:
            List of fields safe to update.
        """
        conflicted_types = {c.field_type for c in conflicts}
        candidates = []

        for field in normalized_fields:
            if not self.is_supported_for_update(field.field_type):
                continue
            if field.field_type in conflicted_types:
                continue
            if not field.format_valid:
                continue
            if field.verified:
                # Only verified fields can be auto-applied
                candidates.append(field)

        return candidates

    def prepare_profile_updates(
        self,
        profile: BusinessProfile,
        fields: list[NormalizedField],
    ) -> dict[str, Any]:
        """Prepare dictionary of profile attribute updates.

        Args:
            profile: Business profile (for reference).
            fields: Normalized fields to apply.

        Returns:
            Dictionary mapping attribute names to new values.
        """
        updates: dict[str, Any] = {}

        for field in fields:
            attr = self.get_profile_attribute(field.field_type)
            if not attr:
                continue

            # Special handling for certain fields
            if field.field_type == FieldType.ESTABLISHMENT_DATE:
                # Convert ISO date string to datetime
                try:
                    from datetime import datetime
                    updates[attr] = datetime.fromisoformat(field.value)
                except ValueError:
                    continue
            elif field.field_type == FieldType.OWNERSHIP_DETAILS:
                # Parse ownership details - for now just set woman_owned if mentioned
                if "woman" in field.value.lower() and "owned" in field.value.lower():
                    updates["woman_owned"] = True
            else:
                updates[attr] = field.value

        return updates

    def validate_provenance_rules(
        self,
        field: NormalizedField,
        profile: BusinessProfile,
    ) -> None:
        """Validate that provenance rules are respected for a field.

        Args:
            field: The normalized field.
            profile: The business profile.

        Raises:
            ProvenanceError: If provenance rules are violated.
        """
        existing_value = self.extract_profile_value(profile, field.field_type)

        if existing_value is not None and field.provenance == "UNKNOWN":
            # Cannot silently overwrite existing profile data with UNKNOWN provenance
            raise ProvenanceError(
                f"Cannot overwrite existing {field.field_type.value} with unverified data",
                field_type=field.field_type.value,
                context={
                    "existing_value": str(existing_value),
                    "extracted_value": field.value,
                },
            )

        if not field.format_valid and field.field_type in (
            FieldType.PAN,
            FieldType.GSTIN,
            FieldType.UDYAM_NUMBER,
            FieldType.PINCODE,
        ):
            # Invalid format for identifiers - cannot be used
            raise ProvenanceError(
                f"Invalid format for {field.field_type.value}: {field.value}",
                field_type=field.field_type.value,
                context={"value": field.value, "format_valid": field.format_valid},
            )
