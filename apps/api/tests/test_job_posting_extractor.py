import pytest
from unittest.mock import Mock, patch

from models.job_posting import JobDescriptionExtraction
from services.job_posting_extractor import extract_job_description, extract_text_from_file


class TestJobPostingExtractor:
    def test_extract_text_from_txt(self):
        """Test extracting text from plain text file."""
        content = b"Senior Backend Engineer\nPython, Django, PostgreSQL"
        text = extract_text_from_file(content, "text/plain")
        
        assert "Senior Backend Engineer" in text
        assert "Python" in text

    def test_extract_text_from_pdf(self):
        """Test that PDF extraction calls fitz correctly."""
        # This is a basic structure test since we need a real PDF for full test
        with pytest.raises(Exception):
            # Empty bytes will fail PDF parsing
            extract_text_from_file(b"", "application/pdf")

    def test_extract_text_unsupported_type(self):
        """Test that unsupported file types raise error."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text_from_file(b"test", "image/png")

    @patch("services.job_posting_extractor.anthropic.Anthropic")
    def test_extract_job_description_structure(self, mock_anthropic):
        """Test that extraction returns proper structure."""
        # Mock the Anthropic API response
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_response = Mock()
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "extract_job_description"
        mock_tool_use.input = {
            "title": "Senior Backend Engineer",
            "company": "TechCorp",
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "preferred_skills": ["AWS", "Docker"],
            "responsibilities": ["Design APIs", "Write tests"],
            "education": ["Bachelor's in CS"],
            "experience_years": "5+ years",
            "certifications": [],
            "domain_knowledge": ["E-commerce"],
            "competency_signals": ["Problem solving"],
        }
        mock_response.content = [mock_tool_use]
        mock_client.messages.create.return_value = mock_response
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.anthropic_api_key = "test_key"
        mock_settings.anthropic_haiku_model = "claude-3-haiku-20240307"
        
        # Test extraction
        result = extract_job_description("Job description text", mock_settings)
        
        assert isinstance(result, JobDescriptionExtraction)
        assert result.title == "Senior Backend Engineer"
        assert "Python" in result.required_skills
        assert "AWS" in result.preferred_skills
        assert len(result.responsibilities) == 2

    def test_extract_job_description_no_api_key(self):
        """Test that missing API key raises error."""
        mock_settings = Mock()
        mock_settings.anthropic_api_key = None
        mock_settings.anthropic_haiku_model = "claude-3-haiku-20240307"
        
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY is missing"):
            extract_job_description("Job text", mock_settings)

    def test_extract_job_description_no_model(self):
        """Test that missing model name raises error."""
        mock_settings = Mock()
        mock_settings.anthropic_api_key = "test_key"
        mock_settings.anthropic_haiku_model = None
        
        with pytest.raises(RuntimeError, match="ANTHROPIC_HAIKU_MODEL is missing"):
            extract_job_description("Job text", mock_settings)


class TestJobDescriptionCategories:
    """Test that different requirement types are properly distinguished."""
    
    def test_required_vs_preferred_distinction(self):
        """Test that required and preferred skills are separate."""
        extraction = JobDescriptionExtraction(
            title="Test Job",
            required_skills=["Python", "Django"],
            preferred_skills=["AWS", "Docker"],
            responsibilities=[],
            education=[],
            certifications=[],
            domain_knowledge=[],
            competency_signals=[],
        )
        
        assert "Python" in extraction.required_skills
        assert "Python" not in extraction.preferred_skills
        assert "AWS" in extraction.preferred_skills
        assert "AWS" not in extraction.required_skills

    def test_all_requirement_types_present(self):
        """Test that all 8 requirement types can be populated."""
        extraction = JobDescriptionExtraction(
            title="Test Job",
            required_skills=["Skill1"],
            preferred_skills=["Skill2"],
            responsibilities=["Responsibility1"],
            education=["Bachelor's"],
            experience_years="5+ years",
            certifications=["AWS Certified"],
            domain_knowledge=["Healthcare"],
            competency_signals=["Leadership"],
        )
        
        assert len(extraction.required_skills) == 1
        assert len(extraction.preferred_skills) == 1
        assert len(extraction.responsibilities) == 1
        assert len(extraction.education) == 1
        assert extraction.experience_years == "5+ years"
        assert len(extraction.certifications) == 1
        assert len(extraction.domain_knowledge) == 1
        assert len(extraction.competency_signals) == 1

    def test_empty_categories_allowed(self):
        """Test that categories can be empty."""
        extraction = JobDescriptionExtraction(
            title="Test Job",
            required_skills=[],
            preferred_skills=[],
            responsibilities=[],
            education=[],
            certifications=[],
            domain_knowledge=[],
            competency_signals=[],
        )
        
        assert extraction.title == "Test Job"
        assert len(extraction.required_skills) == 0
        assert extraction.experience_years is None
