"""Rule loader for eligibility engine.

Loads validated, explicitly approved rule definitions into the rule
registry. Rule definitions are immutable once approved - the loader
rejects duplicate versions and prevents silent overwrites.
"""

import logging
from uuid import UUID

from app.models.eligibility_rule import (
    EligibilityRule,
    EligibilityRuleSet,
)
from app.schemas.eligibility_rule import RuleCreateRequest

logger = logging.getLogger(__name__)


class RuleLoader:
    """Loads and validates rule definitions for the eligibility engine.

    Provides methods to convert RuleCreateRequest objects into
    database model instances. Does not persist directly - the
    registry handles persistence.
    """

    def __init__(self) -> None:
        self._loaded_rule_sets: dict[str, EligibilityRuleSet] = {}

    def load_rule_set(
        self,
        request: RuleCreateRequest,
        created_by: UUID | None = None,
    ) -> EligibilityRuleSet:
        """Load a rule set from a creation request into a model instance.

        Validates that the rule set does not already exist in memory
        (by rule_set_id + version) to prevent silent overwrites.

        Args:
            request: Validated rule creation request.
            created_by: Optional identifier of the user creating the rule set.

        Returns:
            An EligibilityRuleSet model instance (not yet persisted).

        Raises:
            ValueError: If a rule set with the same ID and version
                has already been loaded.
        """
        cache_key = f"{request.rule_set_id}:{request.version}"
        if cache_key in self._loaded_rule_sets:
            raise ValueError(
                f"Rule set {request.rule_set_id} version {request.version} "
                "already exists. Versions are immutable once loaded."
            )

        rule_set = EligibilityRuleSet(
            rule_set_id=request.rule_set_id,
            version=request.version,
            scheme_id=request.scheme_id,
            scheme_name=request.scheme_name,
            description=request.description,
            jurisdiction=request.jurisdiction,
            issuing_authority=request.issuing_authority,
            source_title=request.source_title,
            source_url=request.source_url,
            source_section=request.source_section,
            publication_date=request.publication_date,
            effective_from=request.effective_from,
            effective_until=request.effective_until,
            approval_status="draft",
            created_by=created_by,
        )

        for condition in request.rules:
            rule = EligibilityRule(
                rule_id=condition.rule_id,
                description=condition.description,
                field=condition.field,
                operator=condition.operator.value,
                expected_value=condition.expected_value,
                mandatory=condition.mandatory,
                priority=condition.priority,
                source_reference=condition.source_reference,
                failure_message=condition.failure_message,
            )
            rule_set.rules.append(rule)

        self._loaded_rule_sets[cache_key] = rule_set
        logger.info(
            "Rule set loaded",
            extra={
                "rule_set_id": request.rule_set_id,
                "version": request.version,
                "rule_count": len(request.rules),
            },
        )
        return rule_set

    def get_loaded_rule_set(
        self,
        rule_set_id: str,
        version: str,
    ) -> EligibilityRuleSet | None:
        """Retrieve a loaded rule set by ID and version.

        Args:
            rule_set_id: Stable rule set identifier.
            version: Rule set version.

        Returns:
            The rule set model instance, or None if not loaded.
        """
        return self._loaded_rule_sets.get(f"{rule_set_id}:{version}")

    def list_loaded_rule_sets(self) -> list[EligibilityRuleSet]:
        """List all loaded rule sets.

        Returns:
            List of loaded EligibilityRuleSet instances.
        """
        return list(self._loaded_rule_sets.values())

    def clear_loaded_rule_sets(self) -> None:
        """Clear all loaded rule sets (primarily for testing)."""
        self._loaded_rule_sets.clear()
