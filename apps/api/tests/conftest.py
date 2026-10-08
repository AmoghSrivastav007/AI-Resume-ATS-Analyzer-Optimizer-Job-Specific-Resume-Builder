"""
Pytest configuration and fixtures for Resume ATS Analyzer tests.

This file contains shared fixtures and configuration used across all tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from config import Settings


@pytest.fixture
def mock_settings():
    """Mock Settings object with test configuration."""
    settings = Mock(spec=Settings)
    settings.supabase_url = "https://test.supabase.co"
    settings.supabase_anon_key = "test-anon-key"
    settings.supabase_service_role_key = "test-service-key"
    settings.supabase_jwt_secret = "test-jwt-secret"
    settings.anthropic_api_key = "test-anthropic-key"
    settings.anthropic_haiku_model = "claude-haiku-4-5-20251001"
    settings.anthropic_sonnet_model = "claude-sonnet-4-5-20250929"
    settings.cors_origin_list = ["http://localhost:3000"]
    return settings


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = MagicMock()
    
    # Mock table operations
    client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    client.table.return_value.insert.return_value.execute.return_value.data = []
    client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
    
    # Mock storage operations
    client.storage.from_.return_value.upload.return_value = {"path": "test/path.pdf"}
    client.storage.from_.return_value.download.return_value = b"test file content"
    client.storage.from_.return_value.remove.return_value = {"message": "deleted"}
    
    return client


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_resume_id():
    """Sample resume ID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_version_id():
    """Sample version ID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_resume_data(sample_user_id, sample_resume_id, sample_version_id):
    """
    Sample resume data structure for testing.
    Mimics the structure returned from database queries.
    """
    return {
        "resume_id": sample_resume_id,
        "user_id": sample_user_id,
        "version_id": sample_version_id,
        "version_number": 1,
        "original_filename": "John_Doe_Resume.pdf",
        "created_at": datetime.utcnow().isoformat(),
        "sections": [
            {
                "id": str(uuid4()),
                "section_type": "contact",
                "title": "Contact Information",
                "sort_order": 0,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "text",
                        "content": {
                            "text": "John Doe\nEmail: john@example.com\nPhone: (555) 123-4567"
                        },
                        "order": 0
                    }
                ]
            },
            {
                "id": str(uuid4()),
                "section_type": "experience",
                "title": "Work Experience",
                "sort_order": 1,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "experience",
                        "content": {
                            "company": "Tech Corp",
                            "title": "Software Engineer",
                            "start_date": "2020-01-01",
                            "end_date": "2023-12-31",
                            "description": "Developed web applications using Python and React."
                        },
                        "order": 0
                    }
                ]
            },
            {
                "id": str(uuid4()),
                "section_type": "education",
                "title": "Education",
                "sort_order": 2,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "education",
                        "content": {
                            "institution": "University of Technology",
                            "degree": "Bachelor of Science in Computer Science",
                            "start_date": "2016-09-01",
                            "end_date": "2020-05-31"
                        },
                        "order": 0
                    }
                ]
            },
            {
                "id": str(uuid4()),
                "section_type": "skills",
                "title": "Skills",
                "sort_order": 3,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "skills",
                        "content": {
                            "text": "Python, JavaScript, React, FastAPI, PostgreSQL"
                        },
                        "order": 0
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_resume_data_minimal(sample_user_id, sample_resume_id, sample_version_id):
    """Minimal resume data for testing edge cases."""
    return {
        "resume_id": sample_resume_id,
        "user_id": sample_user_id,
        "version_id": sample_version_id,
        "version_number": 1,
        "original_filename": "Minimal_Resume.pdf",
        "created_at": datetime.utcnow().isoformat(),
        "sections": [
            {
                "id": str(uuid4()),
                "section_type": "contact",
                "title": "Contact",
                "sort_order": 0,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "text",
                        "content": {"text": "Jane Doe"},
                        "order": 0
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_resume_data_with_unicode(sample_user_id, sample_resume_id, sample_version_id):
    """Resume data with Unicode characters for testing."""
    return {
        "resume_id": sample_resume_id,
        "user_id": sample_user_id,
        "version_id": sample_version_id,
        "version_number": 1,
        "original_filename": "José_García_Resume.pdf",
        "created_at": datetime.utcnow().isoformat(),
        "sections": [
            {
                "id": str(uuid4()),
                "section_type": "contact",
                "title": "Información de Contacto",
                "sort_order": 0,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "text",
                        "content": {
                            "text": "José García\nEmail: josé@example.com\n中文: 测试"
                        },
                        "order": 0
                    }
                ]
            },
            {
                "id": str(uuid4()),
                "section_type": "skills",
                "title": "Habilidades",
                "sort_order": 1,
                "blocks": [
                    {
                        "id": str(uuid4()),
                        "type": "skills",
                        "content": {
                            "text": "Python, JavaScript, Español 🚀"
                        },
                        "order": 0
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    client = MagicMock()
    
    # Mock messages.create response
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            type="tool_use",
            name="extract_resume",
            input={
                "personal_info": {"name": "John Doe", "email": "john@example.com"},
                "experience": [{"company": "Tech Corp", "title": "Software Engineer"}],
                "education": [{"institution": "University", "degree": "BS Computer Science"}],
                "skills": ["Python", "JavaScript"]
            }
        )
    ]
    client.messages.create.return_value = mock_response
    
    return client


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests."""
    yield
    # Cleanup happens automatically with pytest


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
