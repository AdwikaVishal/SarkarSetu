"""Rule evaluator for eligibility engine.

Evaluates individual rule conditions deterministically against
business input data. Supports a fixed set of operators - no
arbitrary code execution or expression evaluation.

Condition outcomes:
- PASS: The condition is satisfied.
- FAIL: The condition is definitively not satisfied.
- UNKNOWN: The input data is insufficient to evaluate.
- NOT_APPLICABLE: The condition does not apply to this input.
"""

import logging
from typing import Any

from app.models.eligibility_rule import EligibilityRule
from app.schemas.eligibility_rule import (
    ConditionOutcome,
    ConditionResult,
    RuleOperator,
)

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Deterministic rule condition evaluator.

    Evaluates individual eligibility rules against business input
    data using a fixed set of comparison operators. All evaluation
    is deterministic - same inputs always produce same outputs.
    """

    def __init__(self) -> None:
        self._operator_handlers: dict[str, Any] = {
            RuleOperator.EQUALS.value: self._eval_equals,
            RuleOperator.NOT_EQUALS.value: self._eval_not_equals,
            RuleOperator.GREATER_THAN.value: self._eval_greater_than,
            RuleOperator.GREATER_THAN_OR_EQUAL.value: self._eval_greater_than_or_equal,
            RuleOperator.LESS_THAN.value: self._eval_less_than,
            RuleOperator.LESS_THAN_OR_EQUAL.value: self._eval_less_than_or_equal,
            RuleOperator.IN.value: self._eval_in,
            RuleOperator.NOT_IN.value: self._eval_not_in,
            RuleOperator.CONTAINS.value: self._eval_contains,
            RuleOperator.IS_TRUE.value: self._eval_is_true,
            RuleOperator.IS_FALSE.value: self._eval_is_false,
            RuleOperator.IS_PRESENT.value: self._eval_is_present,
            RuleOperator.IS_MISSING.value: self._eval_is_missing,
        }

    def evaluate_rule(
        self,
        rule: EligibilityRule,
        input_data: dict[str, Any],
    ) -> ConditionResult:
        """Evaluate a single rule condition against input data.

        Args:
            rule: The rule condition to evaluate.
            input_data: Dictionary of business attribute values.

        Returns:
            ConditionResult with the evaluation outcome.
        """
        actual_value = input_data.get(rule.field)

        # Handle IS_MISSING and IS_PRESENT specially - they don't
        # need an expected value comparison
        if rule.operator == RuleOperator.IS_MISSING.value:
            outcome = ConditionOutcome.PASS if actual_value is None else ConditionOutcome.FAIL
        elif rule.operator == RuleOperator.IS_PRESENT.value:
            outcome = ConditionOutcome.PASS if actual_value is not None else ConditionOutcome.FAIL
        else:
            handler = self._operator_handlers.get(rule.operator)
            if handler is None:
                logger.warning(
                    "Unknown operator",
                    extra={"operator": rule.operator, "rule_id": rule.rule_id},
                )
                outcome = ConditionOutcome.UNKNOWN
            else:
                try:
                    outcome = handler(actual_value, rule.expected_value)
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "Operator evaluation error",
                        extra={
                            "operator": rule.operator,
                            "rule_id": rule.rule_id,
                            "error": str(exc),
                        },
                    )
                    outcome = ConditionOutcome.UNKNOWN

        return ConditionResult(
            rule_id=rule.rule_id,
            description=rule.description,
            field=rule.field,
            operator=RuleOperator(rule.operator),
            expected_value=rule.expected_value,
            actual_value=actual_value,
            outcome=outcome,
            mandatory=rule.mandatory,
            source_reference=rule.source_reference,
            failure_message=rule.failure_message,
        )

    def evaluate_rules(
        self,
        rules: list[EligibilityRule],
        input_data: dict[str, Any],
    ) -> list[ConditionResult]:
        """Evaluate a list of rule conditions against input data.

        Rules are evaluated in priority order (lower numbers first).

        Args:
            rules: List of rule conditions to evaluate.
            input_data: Dictionary of business attribute values.

        Returns:
            List of ConditionResult objects, one per rule.
        """
        sorted_rules = sorted(rules, key=lambda r: (r.priority, r.rule_id))
        return [self.evaluate_rule(rule, input_data) for rule in sorted_rules]

    # ------------------------------------------------------------------
    # Operator handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _eval_equals(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None:
            return ConditionOutcome.UNKNOWN
        return ConditionOutcome.PASS if actual == expected else ConditionOutcome.FAIL

    @staticmethod
    def _eval_not_equals(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None:
            return ConditionOutcome.UNKNOWN
        return ConditionOutcome.PASS if actual != expected else ConditionOutcome.FAIL

    @staticmethod
    def _eval_greater_than(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None or expected is None:
            return ConditionOutcome.UNKNOWN
        try:
            return (
                ConditionOutcome.PASS
                if float(actual) > float(expected)
                else ConditionOutcome.FAIL
            )
        except (TypeError, ValueError):
            return ConditionOutcome.UNKNOWN

    @staticmethod
    def _eval_greater_than_or_equal(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None or expected is None:
            return ConditionOutcome.UNKNOWN
        try:
            return (
                ConditionOutcome.PASS
                if float(actual) >= float(expected)
                else ConditionOutcome.FAIL
            )
        except (TypeError, ValueError):
            return ConditionOutcome.UNKNOWN

    @staticmethod
    def _eval_less_than(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None or expected is None:
            return ConditionOutcome.UNKNOWN
        try:
            return (
                ConditionOutcome.PASS
                if float(actual) < float(expected)
                else ConditionOutcome.FAIL
            )
        except (TypeError, ValueError):
            return ConditionOutcome.UNKNOWN

    @staticmethod
    def _eval_less_than_or_equal(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None or expected is None:
            return ConditionOutcome.UNKNOWN
        try:
            return (
                ConditionOutcome.PASS
                if float(actual) <= float(expected)
                else ConditionOutcome.FAIL
            )
        except (TypeError, ValueError):
            return ConditionOutcome.UNKNOWN

    @staticmethod
    def _eval_in(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None:
            return ConditionOutcome.UNKNOWN
        if not isinstance(expected, list):
            return ConditionOutcome.UNKNOWN
        return ConditionOutcome.PASS if actual in expected else ConditionOutcome.FAIL

    @staticmethod
    def _eval_not_in(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None:
            return ConditionOutcome.UNKNOWN
        if not isinstance(expected, list):
            return ConditionOutcome.UNKNOWN
        return ConditionOutcome.PASS if actual not in expected else ConditionOutcome.FAIL

    @staticmethod
    def _eval_contains(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None or expected is None:
            return ConditionOutcome.UNKNOWN
        if isinstance(actual, str) and isinstance(expected, str):
            return ConditionOutcome.PASS if expected in actual else ConditionOutcome.FAIL
        if isinstance(actual, list):
            return ConditionOutcome.PASS if expected in actual else ConditionOutcome.FAIL
        return ConditionOutcome.UNKNOWN

    @staticmethod
    def _eval_is_true(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None:
            return ConditionOutcome.UNKNOWN
        return ConditionOutcome.PASS if actual is True else ConditionOutcome.FAIL

    @staticmethod
    def _eval_is_false(actual: Any, expected: Any) -> ConditionOutcome:
        if actual is None:
            return ConditionOutcome.UNKNOWN
        return ConditionOutcome.PASS if actual is False else ConditionOutcome.FAIL

    @staticmethod
    def _eval_is_present(actual: Any, expected: Any) -> ConditionOutcome:
        return ConditionOutcome.PASS if actual is not None else ConditionOutcome.FAIL

    @staticmethod
    def _eval_is_missing(actual: Any, expected: Any) -> ConditionOutcome:
        return ConditionOutcome.PASS if actual is None else ConditionOutcome.FAIL
