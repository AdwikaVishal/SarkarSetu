"""Specialized AI agents package for SarkarSetu AI.

Exports all agent classes and the agent registry.
"""

from app.services.agents.agent_registry import AgentRegistry
from app.services.agents.base import BaseAgent
from app.services.agents.compliance_agent import ComplianceAgent
from app.services.agents.discovery_agent import DiscoveryAgent
from app.services.agents.document_agent import DocumentAgent
from app.services.agents.eligibility_agent import EligibilityAgent

__all__ = [
    "BaseAgent",
    "DiscoveryAgent",
    "EligibilityAgent",
    "DocumentAgent",
    "ComplianceAgent",
    "AgentRegistry",
]
