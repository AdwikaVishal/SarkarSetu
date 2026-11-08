"""Tests for model imports and metadata registration - run without database."""
from app.database.base import Base
from app.models import (
    BusinessProfile,
    Conversation,
    EligibilityResult,
    Message,
    Recommendation,
    Roadmap,
    RoadmapTask,
    UploadedDocument,
    User,
)


class TestModelImports:
    """Tests for model imports and metadata registration."""

    def test_all_models_imported(self) -> None:
        """Test that all models can be imported."""
        models = [
            User,
            BusinessProfile,
            Conversation,
            Message,
            Recommendation,
            EligibilityResult,
            UploadedDocument,
            Roadmap,
            RoadmapTask,
        ]

        for model in models:
            assert hasattr(model, '__tablename__')
            assert hasattr(model, 'id')

    def test_metadata_registration(self) -> None:
        """Test that all models are registered in Base.metadata."""
        table_names = set(Base.metadata.tables.keys())
        expected_tables = {
            'users',
            'business_profiles',
            'conversations',
            'messages',
            'recommendations',
            'eligibility_results',
            'uploaded_documents',
            'roadmaps',
            'roadmap_tasks',
        }

        for table in expected_tables:
            assert table in table_names, f"Table {table} not registered in metadata"
