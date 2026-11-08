"""Workflow registry for SarkarSetu AI.

Manages registration, retrieval, and service-type-based resolution of
specialized workflows. Provides dependency injection support and
avoids hardcoded workflow instantiation inside the orchestrator.
"""

import logging

from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import (
    ClarificationService,
)
from app.services.conversation.conversation_service import (
    ConversationService,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.retrieval import GovernmentKnowledgeProvider

from .base import BaseWorkflow
from .discovery import DiscoveryWorkflow
from .gst import GSTRegistrationWorkflow
from .msme_schemes import MSMESchemeDiscoveryWorkflow
from .udyam import UdyamRegistrationWorkflow

logger = logging.getLogger(__name__)

# Mapping of service type values to workflow class names
SERVICE_TYPE_TO_WORKFLOW: dict[str, str] = {
    # Discovery workflows
    "government_scheme_discovery": "DiscoveryWorkflow",
    "subsidy_discovery": "DiscoveryWorkflow",
    "loan_discovery": "DiscoveryWorkflow",
    "registration_discovery": "DiscoveryWorkflow",
    # Udyam registration workflows
    "udyam_registration": "UdyamRegistrationWorkflow",
    "udyam_eligibility": "UdyamRegistrationWorkflow",
    # GST registration workflows
    "gst_registration": "GSTRegistrationWorkflow",
    "gst_applicability": "GSTRegistrationWorkflow",
    # MSME scheme discovery workflows
    "msme_schemes": "MSMESchemeDiscoveryWorkflow",
    "scheme_eligibility": "MSMESchemeDiscoveryWorkflow",
}

# Mapping of workflow name to class
WORKFLOW_NAME_TO_CLASS: dict[str, type[BaseWorkflow]] = {
    "DiscoveryWorkflow": DiscoveryWorkflow,
    "UdyamRegistrationWorkflow": UdyamRegistrationWorkflow,
    "GSTRegistrationWorkflow": GSTRegistrationWorkflow,
    "MSMESchemeDiscoveryWorkflow": MSMESchemeDiscoveryWorkflow,
}


class WorkflowRegistry:
    """Registry for specialized workflows.

    Provides:
    - Workflow registration and retrieval by service type
    - Service-type-to-workflow resolution
    - Safe rejection of unsupported service types
    - Dependency injection support
    """

    def __init__(
        self,
        ai_service: AIService,
        conversation_service: ConversationService,
        clarification_service: ClarificationService,
        eligibility_engine: EligibilityEngine,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
    ) -> None:
        self.ai_service = ai_service
        self.conversation_service = conversation_service
        self.clarification_service = clarification_service
        self.eligibility_engine = eligibility_engine
        self.retrieval_provider = retrieval_provider
        self._workflows: dict[str, BaseWorkflow] = {}
        self._register_default_workflows()

    def _register_default_workflows(self) -> None:
        """Register all built-in workflows with shared dependencies."""
        self.register(
            "DiscoveryWorkflow",
            DiscoveryWorkflow(
                ai_service=self.ai_service,
                conversation_service=self.conversation_service,
                clarification_service=self.clarification_service,
                eligibility_engine=self.eligibility_engine,
                retrieval_provider=self.retrieval_provider,
            ),
        )
        self.register(
            "UdyamRegistrationWorkflow",
            UdyamRegistrationWorkflow(
                ai_service=self.ai_service,
                conversation_service=self.conversation_service,
                clarification_service=self.clarification_service,
                eligibility_engine=self.eligibility_engine,
                retrieval_provider=self.retrieval_provider,
            ),
        )
        self.register(
            "GSTRegistrationWorkflow",
            GSTRegistrationWorkflow(
                ai_service=self.ai_service,
                conversation_service=self.conversation_service,
                clarification_service=self.clarification_service,
                eligibility_engine=self.eligibility_engine,
                retrieval_provider=self.retrieval_provider,
            ),
        )
        self.register(
            "MSMESchemeDiscoveryWorkflow",
            MSMESchemeDiscoveryWorkflow(
                ai_service=self.ai_service,
                conversation_service=self.conversation_service,
                clarification_service=self.clarification_service,
                eligibility_engine=self.eligibility_engine,
                retrieval_provider=self.retrieval_provider,
            ),
        )

    def register(
        self,
        service_type: str,
        workflow: BaseWorkflow,
    ) -> None:
        """Register a workflow for a service type.

        Args:
            service_type: Service type identifier.
            workflow: Workflow instance to register.
        """
        self._workflows[service_type] = workflow
        logger.info(
            "Workflow registered",
            extra={
                "service_type": service_type,
                "workflow_name": workflow.name,
            },
        )

    def get(
        self,
        service_type: str,
    ) -> BaseWorkflow | None:
        """Retrieve a workflow by service type.

        Args:
            service_type: Service type identifier.

        Returns:
            Workflow instance, or None if not found.
        """
        return self._workflows.get(service_type)

    def resolve_from_service_type(
        self,
        service_type: str | None,
    ) -> BaseWorkflow | None:
        """Resolve a workflow from a service type.

        Args:
            service_type: Service type identifier.

        Returns:
            Workflow instance, or None if not found.
        """
        if not service_type:
            return None

        workflow_name = SERVICE_TYPE_TO_WORKFLOW.get(service_type)
        if not workflow_name:
            return None

        return self.get(workflow_name)

    def get_supported_service_types(
        self,
    ) -> dict[str, str]:
        """Get the full service type to workflow mapping.

        Returns:
            Dictionary mapping service type identifiers to workflow names.
        """
        return dict(SERVICE_TYPE_TO_WORKFLOW)

    def is_service_type_supported(
        self,
        service_type: str | None,
    ) -> bool:
        """Check if a service type is supported by any registered workflow.

        Args:
            service_type: Service type identifier.

        Returns:
            True if a workflow supports the service type, False otherwise.
        """
        return self.resolve_from_service_type(service_type) is not None

    def list_workflow_types(
        self,
    ) -> list[str]:
        """List all registered workflow service types.

        Returns:
            List of service type identifiers.
        """
        return list(self._workflows.keys())
