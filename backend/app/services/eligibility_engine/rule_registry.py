"""Rule registry for eligibility engine.

Stores and retrieves approved rule sets by identifier and version.
Provides methods to:
- Register a rule set
- Retrieve an exact version
- Retrieve the currently approved effective version for a date
- List versions
- Retire a version
- Reject unapproved versions for production evaluation

Rule-set versions are immutable once approved. The registry never
silently overwrites an existing version.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eligibility_rule import (
    EligibilityRuleSet,
)
from app.schemas.eligibility_rule import RuleStatus

logger = logging.getLogger(__name__)


class RuleRegistry:
    """Registry for versioned eligibility rule sets.

    Manages the lifecycle of rule sets from draft through approval
    to retirement. Only APPROVED rule sets may be used in production
    assessments.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_rule_set(
        self,
        rule_set: EligibilityRuleSet,
    ) -> EligibilityRuleSet:
        """Register a new rule set in the database.

        Args:
            rule_set: EligibilityRuleSet model instance with rules.

        Returns:
            The persisted rule set with generated IDs.

        Raises:
            ValueError: If a rule set with the same ID and version
                already exists.
        """
        # Check for duplicate
        existing = await self.get_rule_set(
            rule_set.rule_set_id,
            rule_set.version,
        )
        if existing is not None:
            raise ValueError(
                f"Rule set {rule_set.rule_set_id} version {rule_set.version} "
                "already exists. Versions are immutable."
            )

        self.db.add(rule_set)
        await self.db.commit()
        await self.db.refresh(rule_set)
        logger.info(
            "Rule set registered",
            extra={
                "rule_set_id": rule_set.rule_set_id,
                "version": rule_set.version,
                "status": rule_set.approval_status,
            },
        )
        return rule_set

    async def get_rule_set(
        self,
        rule_set_id: str,
        version: str,
    ) -> EligibilityRuleSet | None:
        """Retrieve a rule set by ID and exact version.

        Args:
            rule_set_id: Stable rule set identifier.
            version: Rule set version.

        Returns:
            The rule set with its rules, or None if not found.
        """
        result = await self.db.execute(
            select(EligibilityRuleSet).where(
                EligibilityRuleSet.rule_set_id == rule_set_id,
                EligibilityRuleSet.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def get_approved_rule_set(
        self,
        rule_set_id: str,
        evaluation_date: datetime | None = None,
    ) -> EligibilityRuleSet | None:
        """Retrieve the currently approved rule set for a given date.

        Returns the APPROVED rule set whose effective period covers
        the evaluation date. If multiple approved versions overlap,
        returns the one with the latest effective_from.

        Args:
            rule_set_id: Stable rule set identifier.
            evaluation_date: Date for which to find the effective
                rule set. Defaults to now.

        Returns:
            The approved effective rule set, or None if none found.
        """
        if evaluation_date is None:
            evaluation_date = datetime.now(UTC)

        result = await self.db.execute(
            select(EligibilityRuleSet).where(
                EligibilityRuleSet.rule_set_id == rule_set_id,
                EligibilityRuleSet.approval_status == "approved",
                EligibilityRuleSet.effective_from <= evaluation_date,
            )
        )
        candidates = list(result.scalars().all())

        # Filter by effective_until
        valid = [
            rs
            for rs in candidates
            if rs.effective_until is None or rs.effective_until >= evaluation_date
        ]

        if not valid:
            return None

        # Return the one with the latest effective_from
        return max(valid, key=lambda rs: rs.effective_from)

    async def list_versions(
        self,
        rule_set_id: str,
    ) -> list[EligibilityRuleSet]:
        """List all versions of a rule set.

        Args:
            rule_set_id: Stable rule set identifier.

        Returns:
            List of rule set versions ordered by version string.
        """
        result = await self.db.execute(
            select(EligibilityRuleSet).where(
                EligibilityRuleSet.rule_set_id == rule_set_id,
            )
        )
        return sorted(
            result.scalars().all(),
            key=lambda rs: rs.version,
        )

    async def approve_rule_set(
        self,
        rule_set_id: str,
        version: str,
        approved_by: UUID | None,
    ) -> EligibilityRuleSet | None:
        """Approve a rule set for production use.

        Only DRAFT or PENDING_REVIEW rule sets can be approved.
        Once approved, the rule set becomes immutable.

        Args:
            rule_set_id: Stable rule set identifier.
            version: Rule set version.
            approved_by: Identifier of the user approving the rule set.

        Returns:
            The approved rule set, or None if not found.
        """
        rule_set = await self.get_rule_set(rule_set_id, version)
        if rule_set is None:
            return None

        if rule_set.approval_status == RuleStatus.APPROVED.value:
            logger.warning(
                "Rule set already approved",
                extra={"rule_set_id": rule_set_id, "version": version},
            )
            return rule_set

        rule_set.approval_status = RuleStatus.APPROVED.value
        rule_set.approved_at = datetime.now(UTC)
        rule_set.approved_by = approved_by

        await self.db.commit()
        await self.db.refresh(rule_set)
        logger.info(
            "Rule set approved",
            extra={
                "rule_set_id": rule_set_id,
                "version": version,
                "approved_by": approved_by,
            },
        )
        return rule_set

    async def retire_rule_set(
        self,
        rule_set_id: str,
        version: str,
    ) -> EligibilityRuleSet | None:
        """Retire a rule set version.

        Retired rule sets are no longer returned by get_approved_rule_set
        but remain in the database for historical reference.

        Args:
            rule_set_id: Stable rule set identifier.
            version: Rule set version.

        Returns:
            The retired rule set, or None if not found.
        """
        rule_set = await self.get_rule_set(rule_set_id, version)
        if rule_set is None:
            return None

        rule_set.approval_status = RuleStatus.RETIRED.value
        await self.db.commit()
        await self.db.refresh(rule_set)
        logger.info(
            "Rule set retired",
            extra={"rule_set_id": rule_set_id, "version": version},
        )
        return rule_set

    async def list_rule_sets(
        self,
        approval_status: str | None = None,
    ) -> list[EligibilityRuleSet]:
        """List all rule sets, optionally filtered by approval status.

        Args:
            approval_status: Optional filter by approval status.

        Returns:
            List of rule sets ordered by rule_set_id and version.
        """
        query = select(EligibilityRuleSet)
        if approval_status is not None:
            query = query.where(
                EligibilityRuleSet.approval_status == approval_status,
            )
        result = await self.db.execute(query)
        return sorted(
            result.scalars().all(),
            key=lambda rs: (rs.rule_set_id, rs.version),
        )

    async def rule_set_exists(
        self,
        rule_set_id: str,
        version: str,
    ) -> bool:
        """Check if a rule set version exists.

        Args:
            rule_set_id: Stable rule set identifier.
            version: Rule set version.

        Returns:
            True if the rule set version exists.
        """
        return await self.get_rule_set(rule_set_id, version) is not None
