"""Orchestration package for SarkarSetu AI.

Coordinates AI services, conversation memory, intent detection,
entity extraction, and clarification management into a single
end-to-end conversational workflow.
"""

from app.services.orchestrator.orchestrator import SarkarSetuOrchestrator

__all__ = ["SarkarSetuOrchestrator"]
