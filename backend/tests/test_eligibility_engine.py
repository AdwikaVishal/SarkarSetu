"""Eligibility engine tests for Prompt 10.

Tests rule evaluator, status aggregation, engine behavior, and
eligibility agent integration.

Rule evaluator and engine tests run without a database.
Registry and assessment service tests require TEST_DATABASE_URL.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.models.eligibility_rule import (
    EligibilityRule,
    EligibilityRuleSet,
)
from app.schemas.eligibility_rule import (
    AssessmentStatus,
    ConditionOutcome,
    RuleCreateRequest,
    RuleOperator,
)
from app.services.eligibility import (
    EligibilityAssessmentRequest,
    EligibilityAssessmentResult,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
from app.services.eligibility_engine.rule_registry import RuleRegistry


# Module-level mock registry for engine tests (avoids async def in fixture issues)
class _MockRegistry:
    async def get_approved_rule_set(self, *args, **kwargs):
        return None


# ---------------------------------------------------------------------------
# Rule evaluator tests
# ---------------------------------------------------------------------------


class TestRuleEvaluatorOperators:
    """Tests for every supported rule operator."""

    @pytest.fixture
    def evaluator(self) -> RuleEvaluator:
        return RuleEvaluator()

    def _make_rule(
        self,
        field: str,
        operator: str,
        expected_value: Any,
        mandatory: bool = False,
        rule_id: str = "rule-1",
        priority: int = 0,
    ) -> EligibilityRule:
        return EligibilityRule(
            id=uuid4(),
            rule_set_id=uuid4(),
            rule_id=rule_id,
            description=f"Test rule: {field} {operator} {expected_value}",
            field=field,
            operator=operator,
            expected_value=expected_value,
            mandatory=mandatory,
            priority=0,
        )

    # EQUALS / NOT_EQUALS
    def test_equals_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "EQUALS", "Karnataka")
        result = evaluator.evaluate_rule(rule, {"state": "Karnataka"})
        assert result.outcome == ConditionOutcome.PASS

    def test_equals_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "EQUALS", "Karnataka")
        result = evaluator.evaluate_rule(rule, {"state": "Maharashtra"})
        assert result.outcome == ConditionOutcome.FAIL

    def test_equals_unknown(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "EQUALS", "Karnataka")
        result = evaluator.evaluate_rule(rule, {})
        assert result.outcome == ConditionOutcome.UNKNOWN

    def test_not_equals_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "NOT_EQUALS", "Karnataka")
        result = evaluator.evaluate_rule(rule, {"state": "Maharashtra"})
        assert result.outcome == ConditionOutcome.PASS

    def test_not_equals_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "NOT_EQUALS", "Karnataka")
        result = evaluator.evaluate_rule(rule, {"state": "Karnataka"})
        assert result.outcome == ConditionOutcome.FAIL

    # GREATER_THAN / GREATER_THAN_OR_EQUAL
    def test_greater_than_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("annual_turnover", "GREATER_THAN", 1000000)
        result = evaluator.evaluate_rule(rule, {"annual_turnover": 2000000})
        assert result.outcome == ConditionOutcome.PASS

    def test_greater_than_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("annual_turnover", "GREATER_THAN", 1000000)
        result = evaluator.evaluate_rule(rule, {"annual_turnover": 500000})
        assert result.outcome == ConditionOutcome.FAIL

    def test_greater_than_equal_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("employee_count", "GREATER_THAN_OR_EQUAL", 10)
        result = evaluator.evaluate_rule(rule, {"employee_count": 10})
        assert result.outcome == ConditionOutcome.PASS

    def test_greater_than_equal_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("employee_count", "GREATER_THAN_OR_EQUAL", 10)
        result = evaluator.evaluate_rule(rule, {"employee_count": 9})
        assert result.outcome == ConditionOutcome.FAIL

    def test_greater_than_unknown(self, evaluator: RuleEvaluator):
        rule = self._make_rule("annual_turnover", "GREATER_THAN", 1000000)
        result = evaluator.evaluate_rule(rule, {})
        assert result.outcome == ConditionOutcome.UNKNOWN

    # LESS_THAN / LESS_THAN_OR_EQUAL
    def test_less_than_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("employee_count", "LESS_THAN", 100)
        result = evaluator.evaluate_rule(rule, {"employee_count": 50})
        assert result.outcome == ConditionOutcome.PASS

    def test_less_than_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("employee_count", "LESS_THAN", 100)
        result = evaluator.evaluate_rule(rule, {"employee_count": 200})
        assert result.outcome == ConditionOutcome.FAIL

    def test_less_than_equal_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("annual_turnover", "LESS_THAN_OR_EQUAL", 2000000)
        result = evaluator.evaluate_rule(rule, {"annual_turnover": 2000000})
        assert result.outcome == ConditionOutcome.PASS

    def test_less_than_equal_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("annual_turnover", "LESS_THAN_OR_EQUAL", 2000000)
        result = evaluator.evaluate_rule(rule, {"annual_turnover": 3000000})
        assert result.outcome == ConditionOutcome.FAIL

    # IN / NOT_IN
    def test_in_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "IN", ["Karnataka", "Maharashtra", "Tamil Nadu"])
        result = evaluator.evaluate_rule(rule, {"state": "Karnataka"})
        assert result.outcome == ConditionOutcome.PASS

    def test_in_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "IN", ["Karnataka", "Maharashtra"])
        result = evaluator.evaluate_rule(rule, {"state": "Delhi"})
        assert result.outcome == ConditionOutcome.FAIL

    def test_not_in_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "NOT_IN", ["Karnataka", "Maharashtra"])
        result = evaluator.evaluate_rule(rule, {"state": "Delhi"})
        assert result.outcome == ConditionOutcome.PASS

    def test_not_in_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("state", "NOT_IN", ["Karnataka", "Maharashtra"])
        result = evaluator.evaluate_rule(rule, {"state": "Karnataka"})
        assert result.outcome == ConditionOutcome.FAIL

    # CONTAINS
    def test_contains_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("products_services", "CONTAINS", "manufacturing")
        result = evaluator.evaluate_rule(
            rule, {"products_services": "manufacturing, textiles"}
        )
        assert result.outcome == ConditionOutcome.PASS

    def test_contains_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("products_services", "CONTAINS", "manufacturing")
        result = evaluator.evaluate_rule(rule, {"products_services": "textiles"})
        assert result.outcome == ConditionOutcome.FAIL

    # IS_TRUE / IS_FALSE
    def test_is_true_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("is_registered", "IS_TRUE", True)
        result = evaluator.evaluate_rule(rule, {"is_registered": True})
        assert result.outcome == ConditionOutcome.PASS

    def test_is_true_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("is_registered", "IS_TRUE", True)
        result = evaluator.evaluate_rule(rule, {"is_registered": False})
        assert result.outcome == ConditionOutcome.FAIL

    def test_is_false_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("is_foreign", "IS_FALSE", False)
        result = evaluator.evaluate_rule(rule, {"is_foreign": False})
        assert result.outcome == ConditionOutcome.PASS

    def test_is_false_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("is_foreign", "IS_FALSE", False)
        result = evaluator.evaluate_rule(rule, {"is_foreign": True})
        assert result.outcome == ConditionOutcome.FAIL

    # IS_PRESENT / IS_MISSING
    def test_is_present_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("gstin", "IS_PRESENT", True)
        result = evaluator.evaluate_rule(rule, {"gstin": "29ABCDE1234F1Z5"})
        assert result.outcome == ConditionOutcome.PASS

    def test_is_present_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("gstin", "IS_PRESENT", True)
        result = evaluator.evaluate_rule(rule, {})
        assert result.outcome == ConditionOutcome.FAIL

    def test_is_missing_pass(self, evaluator: RuleEvaluator):
        rule = self._make_rule("gstin", "IS_MISSING", True)
        result = evaluator.evaluate_rule(rule, {})
        assert result.outcome == ConditionOutcome.PASS

    def test_is_missing_fail(self, evaluator: RuleEvaluator):
        rule = self._make_rule("gstin", "IS_MISSING", True)
        result = evaluator.evaluate_rule(rule, {"gstin": "29ABCDE1234F1Z5"})
        assert result.outcome == ConditionOutcome.FAIL

    def test_evaluate_rules_sorted_by_priority(self, evaluator: RuleEvaluator):
        rules = [
            self._make_rule("field_a", "EQUALS", "a", rule_id="rule-b", priority=2),
            self._make_rule("field_b", "EQUALS", "b", rule_id="rule-a", priority=1),
        ]
        input_data = {"field_a": "a", "field_b": "b"}
        results = evaluator.evaluate_rules(rules, input_data)
        assert results[0].rule_id == "rule-a"
        assert results[1].rule_id == "rule-b"


# ---------------------------------------------------------------------------
# Status aggregation tests
# ---------------------------------------------------------------------------


class TestStatusAggregation:
    """Tests for eligibility status aggregation policy."""

    @pytest.fixture
    def engine(
        self,
    ) -> EligibilityEngine:
        # Use a mock registry that returns no rule sets (engine handles None)
        return EligibilityEngine(registry=_MockRegistry())

    @pytest.fixture
    def rule_set(self) -> EligibilityRuleSet:
        return EligibilityRuleSet(
            id=uuid4(),
            rule_set_id="test_scheme",
            version="1.0.0",
            scheme_name="Test Scheme",
            approval_status="approved",
        )

    def _make_mandatory_rule(
        self,
        field: str,
        operator: str,
        expected_value: Any,
        rule_id: str = "rule-1",
    ) -> EligibilityRule:
        return EligibilityRule(
            id=uuid4(),
            rule_set_id=uuid4(),
            rule_id=rule_id,
            description=f"Test: {field} {operator} {expected_value}",
            field=field,
            operator=operator,
            expected_value=expected_value,
            mandatory=True,
            priority=0,
        )

    def _make_optional_rule(
        self,
        field: str,
        operator: str,
        expected_value: Any,
        rule_id: str = "rule-2",
    ) -> EligibilityRule:
        return EligibilityRule(
            id=uuid4(),
            rule_set_id=uuid4(),
            rule_id=rule_id,
            description=f"Optional: {field} {operator} {expected_value}",
            field=field,
            operator=operator,
            expected_value=expected_value,
            mandatory=False,
            priority=1,
        )

    def test_all_mandatory_pass(self, engine: EligibilityEngine, rule_set: EligibilityRuleSet):
        rules = [
            self._make_mandatory_rule("state", "EQUALS", "Karnataka"),
            self._make_mandatory_rule("employee_count", "GREATER_THAN_OR_EQUAL", 10),
        ]
        input_data = {"state": "Karnataka", "employee_count": 50}
        results = engine.evaluator.evaluate_rules(rules, input_data)
        status, missing = engine._aggregate_status(results)
        assert status == AssessmentStatus.ELIGIBLE
        assert missing == []

    def test_mandatory_fail(self, engine: EligibilityEngine, rule_set: EligibilityRuleSet):
        rules = [
            self._make_mandatory_rule("state", "EQUALS", "Karnataka"),
        ]
        input_data = {"state": "Maharashtra"}
        results = engine.evaluator.evaluate_rules(rules, input_data)
        status, missing = engine._aggregate_status(results)
        assert status == AssessmentStatus.INELIGIBLE
        assert missing == []

    def test_mandatory_unknown(self, engine: EligibilityEngine, rule_set: EligibilityRuleSet):
        rules = [
            self._make_mandatory_rule("annual_turnover", "GREATER_THAN", 1000000),
        ]
        input_data = {}
        results = engine.evaluator.evaluate_rules(rules, input_data)
        status, missing = engine._aggregate_status(results)
        assert status == AssessmentStatus.NEEDS_INFORMATION
        assert "annual_turnover" in missing

    def test_optional_unknown(self, engine: EligibilityEngine, rule_set: EligibilityRuleSet):
        rules = [
            self._make_mandatory_rule("state", "EQUALS", "Karnataka"),
            self._make_optional_rule("gstin", "IS_PRESENT", True),
        ]
        input_data = {"state": "Karnataka"}
        results = engine.evaluator.evaluate_rules(rules, input_data)
        status, missing = engine._aggregate_status(results)
        assert status == AssessmentStatus.POTENTIALLY_ELIGIBLE
        assert missing == []

    def test_mixed_mandatory_pass_optional_fail(self, engine: EligibilityEngine, rule_set: EligibilityRuleSet):
        rules = [
            self._make_mandatory_rule("state", "EQUALS", "Karnataka"),
            self._make_optional_rule("employee_count", "LESS_THAN", 5),
        ]
        input_data = {"state": "Karnataka", "employee_count": 50}
        results = engine.evaluator.evaluate_rules(rules, input_data)
        status, missing = engine._aggregate_status(results)
        assert status == AssessmentStatus.POTENTIALLY_ELIGIBLE
        assert missing == []


# ---------------------------------------------------------------------------
# EligibilityAssessmentResult model tests
# ---------------------------------------------------------------------------


class TestEligibilityAssessmentResult:
    """Tests for the EligibilityAssessmentResult model."""

    def test_result_creation(self):
        result = EligibilityAssessmentResult(
            user_id=uuid4(),
            scheme_name="Test Scheme",
            assessment_status="eligible",
            rule_set_version="1.0.0",
        )
        assert result.assessment_id is not None
        assert result.user_id is not None
        assert result.assessment_status == "eligible"
        assert result.rule_set_version == "1.0.0"
        assert result.result_data == {}
        assert result.missing_information == []
        assert result.evidence_references == []
        assert result.warnings == []
        assert result.condition_results == []


# ---------------------------------------------------------------------------
# Request validation tests
# ---------------------------------------------------------------------------


class TestAssessmentRequest:
    """Tests for EligibilityAssessmentRequest validation."""

    def test_request_creation(self):
        request = EligibilityAssessmentRequest(
            user_id=uuid4(),
            scheme_name="Test Scheme",
        )
        assert request.user_id is not None
        assert request.scheme_name == "Test Scheme"
        assert request.business_attributes == {}
        assert request.missing_information == []
        assert request.request_id is not None


# ---------------------------------------------------------------------------
# Engine protocol compliance tests
# ---------------------------------------------------------------------------


class TestEngineProtocol:
    """Tests that EligibilityEngine implements EligibilityEvaluator protocol."""

    @pytest.fixture
    def engine(
        self,
    ) -> EligibilityEngine:
        registry = MagicMock()
        registry.get_approved_rule_set = MagicMock(return_value=None)
        return EligibilityEngine(registry=registry)

    @pytest.mark.asyncio
    async def test_engine_implements_evaluate(self):
        class _TestRegistry:
            async def get_approved_rule_set(self, *args, **kwargs):
                return None

        engine = EligibilityEngine(registry=_TestRegistry())
        request = EligibilityAssessmentRequest(
            user_id=uuid4(),
            scheme_name="NonExistent Scheme",
        )
        result = await engine.evaluate(request)
        assert result.assessment_status == "unverified"
        assert result.rule_set_version == "none"
        assert "official verification" in result.warnings[0].lower()


# ---------------------------------------------------------------------------
# Rule registry tests (require database)
# ---------------------------------------------------------------------------


class TestRuleRegistry:
    """Tests for RuleRegistry (require PostgreSQL via TEST_DATABASE_URL)."""

    @pytest.mark.asyncio
    async def test_register_and_retrieve(
        self,
        db_session,
    ):
        from app.services.eligibility_engine.rule_loader import RuleLoader
        from uuid import uuid4

        registry = RuleRegistry(db_session)
        loader = RuleLoader()

        request = RuleCreateRequest(
            rule_set_id="test_scheme",
            version="1.0.0",
            scheme_name="Test Scheme",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            rules=[
                {
                    "rule_id": "rule-1",
                    "description": "State must be Karnataka",
                    "field": "state",
                    "operator": "EQUALS",
                    "expected_value": "Karnataka",
                    "mandatory": True,
                    "priority": 0,
                }
            ],
        )

        rule_set = loader.load_rule_set(request, created_by=None)
        persisted = await registry.register_rule_set(rule_set)

        assert persisted.rule_set_id == "test_scheme"
        assert persisted.version == "1.0.0"
        assert len(persisted.rules) == 1

        # Retrieve
        retrieved = await registry.get_rule_set("test_scheme", "1.0.0")
        assert retrieved is not None
        assert retrieved.rule_set_id == "test_scheme"
        assert retrieved.version == "1.0.0"
        assert len(retrieved.rules) == 1

    @pytest.mark.asyncio
    async def test_reject_duplicate_version(
        self,
        db_session,
    ):
        from app.services.eligibility_engine.rule_loader import RuleLoader

        registry = RuleRegistry(db_session)
        loader = RuleLoader()

        request = RuleCreateRequest(
            rule_set_id="test_scheme",
            version="1.0.0",
            scheme_name="Test Scheme",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            rules=[
                {
                    "rule_id": "rule-1",
                    "description": "Test rule",
                    "field": "state",
                    "operator": "EQUALS",
                    "expected_value": "Karnataka",
                    "mandatory": True,
                    "priority": 0,
                }
            ],
        )

        rule_set = loader.load_rule_set(request, created_by=None)
        await registry.register_rule_set(rule_set)

        # Try to register again with a new loader instance
        loader2 = RuleLoader()
        rule_set2 = loader2.load_rule_set(request, created_by=None)
        with pytest.raises(ValueError, match="already exists"):
            await registry.register_rule_set(rule_set2)

    @pytest.mark.asyncio
    async def test_approve_rule_set(
        self,
        db_session,
    ):
        from app.services.eligibility_engine.rule_loader import RuleLoader

        registry = RuleRegistry(db_session)
        loader = RuleLoader()

        request = RuleCreateRequest(
            rule_set_id="test_scheme",
            version="1.0.0",
            scheme_name="Test Scheme",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            rules=[
                {
                    "rule_id": "rule-1",
                    "description": "Test rule",
                    "field": "state",
                    "operator": "EQUALS",
                    "expected_value": "Karnataka",
                    "mandatory": True,
                    "priority": 0,
                }
            ],
        )

        rule_set = loader.load_rule_set(request, created_by=None)
        await registry.register_rule_set(rule_set)

        # Approve
        approved = await registry.approve_rule_set("test_scheme", "1.0.0", None)
        assert approved is not None
        assert approved.approval_status == "approved"
        assert approved.approved_by is None
        assert approved.approved_at is not None

    @pytest.mark.asyncio
    async def test_get_approved_rule_set(
        self,
        db_session,
    ):
        from app.services.eligibility_engine.rule_loader import RuleLoader

        registry = RuleRegistry(db_session)
        loader = RuleLoader()

        request = RuleCreateRequest(
            rule_set_id="test_scheme",
            version="1.0.0",
            scheme_name="Test Scheme",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            rules=[
                {
                    "rule_id": "rule-1",
                    "description": "Test rule",
                    "field": "state",
                    "operator": "EQUALS",
                    "expected_value": "Karnataka",
                    "mandatory": True,
                    "priority": 0,
                }
            ],
        )

        rule_set = loader.load_rule_set(request, created_by=None)
        await registry.register_rule_set(rule_set)
        await registry.approve_rule_set("test_scheme", "1.0.0", None)

        # Get approved
        retrieved = await registry.get_approved_rule_set("test_scheme")
        assert retrieved is not None
        assert retrieved.approval_status == "approved"
        assert retrieved.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_retire_rule_set(
        self,
        db_session,
    ):
        from app.services.eligibility_engine.rule_loader import RuleLoader

        registry = RuleRegistry(db_session)
        loader = RuleLoader()

        request = RuleCreateRequest(
            rule_set_id="test_scheme",
            version="1.0.0",
            scheme_name="Test Scheme",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            rules=[
                {
                    "rule_id": "rule-1",
                    "description": "Test rule",
                    "field": "state",
                    "operator": "EQUALS",
                    "expected_value": "Karnataka",
                    "mandatory": True,
                    "priority": 0,
                }
            ],
        )

        rule_set = loader.load_rule_set(request, created_by=None)
        await registry.register_rule_set(rule_set)
        await registry.approve_rule_set("test_scheme", "1.0.0", None)

        # Retire
        retired = await registry.retire_rule_set("test_scheme", "1.0.0")
        assert retired is not None
        assert retired.approval_status == "retired"

        # Should not be returned by get_approved_rule_set
        not_found = await registry.get_approved_rule_set("test_scheme")
        assert not_found is None