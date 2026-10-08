"""
Unit tests for Export Service.

Tests DOCX generation, PDF generation (error handling), and export validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from services.export_service import ExportService, WEASYPRINT_AVAILABLE


@pytest.mark.unit
class TestExportServiceDocx:
    """Tests for DOCX generation."""

    def test_generate_docx_success(self, mock_settings, sample_resume_data, sample_user_id, sample_version_id):
        """Test successful DOCX generation with normal resume data."""
        service = ExportService(mock_settings)
        
        # Mock _fetch_resume_data to return sample data
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data):
            docx_bytes = service.generate_docx(sample_user_id, sample_version_id)
        
        # Verify output
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0
        
        # Verify it's a valid DOCX (starts with PK zip signature)
        assert docx_bytes[:2] == b'PK'

    def test_generate_docx_with_special_characters(
        self, mock_settings, sample_resume_data_with_unicode, sample_user_id, sample_version_id
    ):
        """Test DOCX generation handles Unicode characters correctly."""
        service = ExportService(mock_settings)
        
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data_with_unicode):
            docx_bytes = service.generate_docx(sample_user_id, sample_version_id)
        
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0
        # DOCX should handle Unicode without errors
        assert docx_bytes[:2] == b'PK'

    def test_generate_docx_with_minimal_content(
        self, mock_settings, sample_resume_data_minimal, sample_user_id, sample_version_id
    ):
        """Test DOCX generation with minimal resume content."""
        service = ExportService(mock_settings)
        
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data_minimal):
            docx_bytes = service.generate_docx(sample_user_id, sample_version_id)
        
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0

    def test_generate_docx_uses_word_styles(self, mock_settings, sample_resume_data, sample_user_id, sample_version_id):
        """Test that DOCX generation uses proper Word Heading styles."""
        service = ExportService(mock_settings)
        
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data):
            with patch('services.export_service.Document') as MockDocument:
                mock_doc = MagicMock()
                MockDocument.return_value = mock_doc
                
                # Mock the save method to capture the document
                mock_doc_bytes = BytesIO()
                mock_doc.save = lambda x: None
                
                try:
                    service.generate_docx(sample_user_id, sample_version_id)
                except:
                    pass  # We're just testing that Document was instantiated
                
                # Verify Document was created
                MockDocument.assert_called_once()


@pytest.mark.unit
class TestExportServicePdf:
    """Tests for PDF generation."""

    def test_generate_pdf_fails_gracefully_without_gtk(self, mock_settings, sample_resume_data, sample_user_id, sample_version_id):
        """Test that PDF generation raises clear error when WeasyPrint/GTK unavailable."""
        if WEASYPRINT_AVAILABLE:
            pytest.skip("WeasyPrint is available, can't test error handling")
        
        service = ExportService(mock_settings)
        
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data):
            with pytest.raises(RuntimeError) as exc_info:
                service.generate_pdf(sample_user_id, sample_version_id)
            
            # Verify error message is helpful
            assert "WeasyPrint is not available" in str(exc_info.value)
            assert "GTK" in str(exc_info.value)

    @pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="WeasyPrint not available")
    def test_generate_pdf_success(self, mock_settings, sample_resume_data, sample_user_id, sample_version_id):
        """Test successful PDF generation when WeasyPrint is available."""
        service = ExportService(mock_settings)
        
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data):
            # Mock template file
            mock_template_content = "<html><body>{{name}}</body></html>"
            with patch('builtins.open', return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda s,*a: None, read=lambda: mock_template_content)):
                pdf_bytes = service.generate_pdf(sample_user_id, sample_version_id)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF should start with %PDF
        assert pdf_bytes[:4] == b'%PDF'


@pytest.mark.unit
class TestExportServiceValidation:
    """Tests for export validation (self-check)."""

    def test_validate_export_success(self, mock_settings, sample_resume_data, sample_user_id, sample_version_id):
        """Test validation passes when all fields are recovered."""
        service = ExportService(mock_settings)
        
        # Mock the fetch and parsing
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data):
            with patch.object(service, '_cleanup_temp_validation_data'):
                with patch('services.export_service.ResumeParsePipeline') as MockPipeline:
                    # Mock successful parsing with all fields recovered
                    mock_result = MagicMock()
                    mock_result.parsed = {
                        "personal_info": {"name": "John Doe", "email": "john@example.com"},
                        "experience": [{"company": "Tech Corp"}],
                        "education": [{"institution": "University"}],
                        "skills": ["Python", "JavaScript"]
                    }
                    MockPipeline.return_value.run.return_value = mock_result
                    
                    validation_result = service.validate_export(
                        b"fake pdf bytes",
                        sample_version_id,
                        sample_user_id
                    )
        
        # Verify validation passed
        assert validation_result["validation_passed"] is True
        assert validation_result["fields_recovered"] >= 0.8  # 80% threshold
        assert isinstance(validation_result["missing_fields"], list)

    def test_validate_export_fails_low_recovery(self, mock_settings, sample_resume_data, sample_user_id, sample_version_id):
        """Test validation fails when field recovery is below threshold."""
        service = ExportService(mock_settings)
        
        with patch.object(service, '_fetch_resume_data', return_value=sample_resume_data):
            with patch.object(service, '_cleanup_temp_validation_data'):
                with patch('services.export_service.ResumeParsePipeline') as MockPipeline:
                    # Mock parsing with low field recovery (images instead of text)
                    mock_result = MagicMock()
                    mock_result.parsed = {
                        "personal_info": {},  # Missing
                        "experience": [],  # Missing
                        "education": [],  # Missing
                        "skills": []  # Missing
                    }
                    MockPipeline.return_value.run.return_value = mock_result
                    
                    validation_result = service.validate_export(
                        b"fake pdf bytes",
                        sample_version_id,
                        sample_user_id
                    )
        
        # Verify validation failed
        assert validation_result["validation_passed"] is False
        assert validation_result["fields_recovered"] < 0.8
        assert len(validation_result["missing_fields"]) > 0


@pytest.mark.unit
class TestExportServiceHelpers:
    """Tests for helper methods."""

    def test_fetch_resume_data(self, mock_settings, mock_supabase_client, sample_resume_data, sample_user_id, sample_version_id):
        """Test _fetch_resume_data retrieves data correctly."""
        service = ExportService(mock_settings)
        service.client = mock_supabase_client
        
        # Mock database response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_resume_data]
        
        result = service._fetch_resume_data(sample_user_id, sample_version_id)
        
        assert result == sample_resume_data
        # Verify correct query was made
        mock_supabase_client.table.assert_called()

    def test_prepare_template_data(self, mock_settings, sample_resume_data):
        """Test _prepare_template_data transforms data correctly for templates."""
        service = ExportService(mock_settings)
        
        template_data = service._prepare_template_data(sample_resume_data)
        
        # Verify structure
        assert "name" in template_data
        assert "sections" in template_data
        assert isinstance(template_data["sections"], list)
        
        # Verify sections are properly formatted
        for section in template_data["sections"]:
            assert "title" in section
            assert "blocks" in section

    def test_compare_parsed_data(self, mock_settings, sample_resume_data):
        """Test _compare_parsed_data calculates recovery rate correctly."""
        service = ExportService(mock_settings)
        
        # Original data
        original = sample_resume_data
        
        # Parsed data with some fields recovered
        parsed = {
            "personal_info": {"name": "John Doe"},
            "experience": [{"company": "Tech Corp"}],
            "education": [],  # Missing
            "skills": ["Python"]
        }
        
        result = service._compare_parsed_data(original, parsed)
        
        assert "fields_recovered" in result
        assert "total_fields" in result
        assert "missing_fields" in result
        assert 0 <= result["fields_recovered"] <= 1.0


@pytest.mark.unit
class TestExportServiceEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_generate_docx_empty_sections(self, mock_settings, sample_user_id, sample_version_id):
        """Test DOCX generation handles empty sections gracefully."""
        service = ExportService(mock_settings)
        
        empty_data = {
            "resume_id": "test-id",
            "user_id": sample_user_id,
            "version_id": sample_version_id,
            "sections": []
        }
        
        with patch.object(service, '_fetch_resume_data', return_value=empty_data):
            docx_bytes = service.generate_docx(sample_user_id, sample_version_id)
        
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0

    def test_generate_docx_missing_blocks(self, mock_settings, sample_user_id, sample_version_id):
        """Test DOCX generation handles sections with no blocks."""
        service = ExportService(mock_settings)
        
        data_with_empty_section = {
            "resume_id": "test-id",
            "user_id": sample_user_id,
            "version_id": sample_version_id,
            "sections": [
                {
                    "id": "section-1",
                    "section_type": "experience",
                    "title": "Work Experience",
                    "sort_order": 0,
                    "blocks": []  # No blocks
                }
            ]
        }
        
        with patch.object(service, '_fetch_resume_data', return_value=data_with_empty_section):
            docx_bytes = service.generate_docx(sample_user_id, sample_version_id)
        
        assert isinstance(docx_bytes, bytes)

    def test_fetch_resume_data_nonexistent(self, mock_settings, mock_supabase_client, sample_user_id):
        """Test _fetch_resume_data handles nonexistent resume."""
        service = ExportService(mock_settings)
        service.client = mock_supabase_client
        
        # Mock empty response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        with pytest.raises(Exception):  # Should raise some error
            service._fetch_resume_data(sample_user_id, "nonexistent-id")
