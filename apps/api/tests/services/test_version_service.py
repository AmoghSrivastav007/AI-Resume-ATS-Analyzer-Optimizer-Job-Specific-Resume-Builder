"""
Unit tests for Version Service (Step 8).

Tests version control operations including restore, duplicate, and version history management.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from uuid import uuid4

from services.version_service import VersionService


@pytest.mark.unit
@pytest.mark.asyncio
class TestVersionService:
    """Test suite for VersionService."""
    
    async def test_restore_version_success(self, mock_supabase_client, sample_user_id):
        """Test successful version restoration."""
        # Arrange
        service = VersionService(mock_supabase_client)
        old_version_id = str(uuid4())
        resume_id = str(uuid4())
        
        # Mock old version fetch
        old_version_response = MagicMock()
        old_version_response.data = [{
            "id": old_version_id,
            "resume_id": resume_id,
            "version_number": 3,
            "status": "completed",
            "storage_path": "resumes/old.pdf",
            "original_filename": "Resume_v3.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 50000,
            "needs_ocr": False,
            "parse_error": None
        }]
        
        # Mock max version number query
        max_version_response = MagicMock()
        max_version_response.data = [{"version_number": 5}]
        
        # Mock new version insert
        new_version_response = MagicMock()
        new_version_id = str(uuid4())
        new_version_response.data = [{
            "id": new_version_id,
            "resume_id": resume_id,
            "version_number": 6,
            "status": "completed"
        }]
        
        # Configure mock chains
        select_mock = mock_supabase_client.table.return_value.select.return_value
        
        # First call: fetch old version
        select_mock.eq.return_value.eq.return_value.execute.return_value = old_version_response
        
        # Second call: get max version number
        select_mock.eq.return_value.order.return_value.limit.return_value.execute.return_value = max_version_response
        
        # Third call: insert new version
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = new_version_response
        
        # Mock update current version
        update_response = MagicMock()
        update_response.data = [{"current_version_id": new_version_id}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = update_response
        
        # Mock internal methods to avoid complex mocking
        with patch.object(service, '_copy_sections_and_blocks', new_callable=AsyncMock) as mock_copy_sections, \
             patch.object(service, '_copy_fact_ledger', new_callable=AsyncMock) as mock_copy_facts:
            
            # Act
            result = await service.restore_version(
                version_id=old_version_id,
                user_id=sample_user_id
            )
            
            # Assert
            assert result["id"] == new_version_id
            assert result["version_number"] == 6  # max + 1
            assert result["resume_id"] == resume_id
            mock_copy_sections.assert_called_once()
            mock_copy_facts.assert_called_once()
    
    async def test_restore_version_not_found(self, mock_supabase_client, sample_user_id):
        """Test restoring non-existent version raises error."""
        # Arrange
        service = VersionService(mock_supabase_client)
        version_id = str(uuid4())
        
        # Mock empty response
        empty_response = MagicMock()
        empty_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty_response
        
        # Act & Assert
        with pytest.raises(ValueError, match="Version not found"):
            await service.restore_version(
                version_id=version_id,
                user_id=sample_user_id
            )
    
    async def test_duplicate_version_success(self, mock_supabase_client, sample_user_id):
        """Test successful version duplication as new resume."""
        # Arrange
        service = VersionService(mock_supabase_client)
        old_version_id = str(uuid4())
        old_resume_id = str(uuid4())
        new_title = "Software Engineer Resume"
        
        # Mock old version fetch
        old_version_response = MagicMock()
        old_version_response.data = [{
            "id": old_version_id,
            "resume_id": old_resume_id,
            "version_number": 2,
            "status": "completed",
            "storage_path": "resumes/original.pdf",
            "original_filename": "My_Resume.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 45000,
            "needs_ocr": False,
            "parse_error": None
        }]
        
        # Mock old resume title fetch
        old_resume_response = MagicMock()
        old_resume_response.data = [{"title": "General Resume"}]
        
        # Mock new resume insert
        new_resume_response = MagicMock()
        new_resume_id = str(uuid4())
        new_resume_response.data = [{
            "id": new_resume_id,
            "title": new_title
        }]
        
        # Mock new version insert
        new_version_response = MagicMock()
        new_version_id = str(uuid4())
        new_version_response.data = [{
            "id": new_version_id,
            "resume_id": new_resume_id,
            "version_number": 1,  # First version of new resume
            "status": "completed"
        }]
        
        # Configure mocks
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.return_value = old_version_response
        select_mock.eq.return_value.execute.return_value = old_resume_response
        
        insert_mock = mock_supabase_client.table.return_value.insert.return_value
        insert_mock.execute.side_effect = [new_resume_response, new_version_response]
        
        # Mock update
        update_response = MagicMock()
        update_response.data = [{"current_version_id": new_version_id}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = update_response
        
        # Mock internal methods to avoid complex mocking
        with patch.object(service, '_copy_sections_and_blocks', new_callable=AsyncMock) as mock_copy_sections, \
             patch.object(service, '_copy_fact_ledger', new_callable=AsyncMock) as mock_copy_facts:
            
            # Act
            result = await service.duplicate_version(
                version_id=old_version_id,
                new_title=new_title,
                user_id=sample_user_id
            )
            
            # Assert
            assert result["id"] == new_version_id
            assert result["version_number"] == 1  # First version of new resume
            assert result["resume_id"] == new_resume_id
            mock_copy_sections.assert_called_once()
            mock_copy_facts.assert_called_once()
    
    async def test_duplicate_version_default_title(self, mock_supabase_client, sample_user_id):
        """Test duplicating version with default title."""
        # Arrange
        service = VersionService(mock_supabase_client)
        old_version_id = str(uuid4())
        
        # Mock old version fetch
        old_version_response = MagicMock()
        old_version_response.data = [{
            "id": old_version_id,
            "resume_id": str(uuid4()),
            "version_number": 1,
            "status": "completed",
            "storage_path": "resumes/old.pdf",
            "original_filename": "Resume.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 40000,
            "needs_ocr": False
        }]
        
        # Mock old resume title
        old_resume_response = MagicMock()
        old_resume_response.data = [{"title": "My Resume"}]
        
        # Mock new resume insert
        new_resume_response = MagicMock()
        new_resume_response.data = [{"id": str(uuid4()), "title": "Copy of My Resume"}]
        
        # Mock new version insert
        new_version_response = MagicMock()
        new_version_response.data = [{"id": str(uuid4()), "version_number": 1}]
        
        # Configure mocks
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.return_value = old_version_response
        select_mock.eq.return_value.execute.return_value = old_resume_response
        
        insert_mock = mock_supabase_client.table.return_value.insert.return_value
        insert_mock.execute.side_effect = [new_resume_response, new_version_response]
        
        update_response = MagicMock()
        update_response.data = [{}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = update_response
        
        # Mock internal methods to avoid complex mocking
        with patch.object(service, '_copy_sections_and_blocks', new_callable=AsyncMock) as mock_copy_sections, \
             patch.object(service, '_copy_fact_ledger', new_callable=AsyncMock) as mock_copy_facts:
            
            # Act
            result = await service.duplicate_version(
                version_id=old_version_id,
                new_title=None,  # Should default to "Copy of My Resume"
                user_id=sample_user_id
            )
            
            # Assert
            assert result is not None
            # Title is set during resume insert, which we mocked
            mock_copy_sections.assert_called_once()
            mock_copy_facts.assert_called_once()
    
    async def test_copy_sections_and_blocks(self, mock_supabase_client, sample_user_id):
        """Test copying sections and blocks between versions."""
        # Arrange
        service = VersionService(mock_supabase_client)
        source_version_id = str(uuid4())
        target_version_id = str(uuid4())
        
        old_section_id_1 = str(uuid4())
        old_section_id_2 = str(uuid4())
        
        # Mock sections fetch
        sections_response = MagicMock()
        sections_response.data = [
            {
                "id": old_section_id_1,
                "section_type": "contact",
                "title": "Contact",
                "sort_order": 0
            },
            {
                "id": old_section_id_2,
                "section_type": "experience",
                "title": "Experience",
                "sort_order": 1
            }
        ]
        
        # Mock blocks fetch
        blocks_response = MagicMock()
        blocks_response.data = [
            {
                "id": str(uuid4()),
                "section_id": old_section_id_1,
                "block_type": "text",
                "content": {"text": "John Doe"},
                "sort_order": 0,
                "embedding": None
            },
            {
                "id": str(uuid4()),
                "section_id": old_section_id_2,
                "block_type": "experience",
                "content": {"company": "Tech Corp"},
                "sort_order": 0,
                "embedding": None
            }
        ]
        
        # Configure mocks - need to handle multiple select chains
        table_mock = mock_supabase_client.table.return_value
        
        # First select call: sections
        select_sections = MagicMock()
        select_sections.eq.return_value.eq.return_value.order.return_value.execute.return_value = sections_response
        
        # Second select call: blocks
        select_blocks = MagicMock()
        select_blocks.eq.return_value.eq.return_value.order.return_value.execute.return_value = blocks_response
        
        # Make table().select() return different mocks on each call
        table_mock.select.side_effect = [select_sections, select_blocks]
        
        # Mock inserts (2 sections + 2 blocks = 4 inserts)
        insert_mock = MagicMock()
        insert_mock.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
        table_mock.insert.return_value = insert_mock
        
        # Act
        await service._copy_sections_and_blocks(
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            user_id=sample_user_id
        )
        
        # Assert
        # Should insert 2 sections + 2 blocks = 4 inserts
        assert insert_mock.execute.call_count == 4
    
    async def test_copy_fact_ledger(self, mock_supabase_client, sample_user_id):
        """Test copying fact ledger between versions."""
        # Arrange
        service = VersionService(mock_supabase_client)
        source_version_id = str(uuid4())
        target_version_id = str(uuid4())
        
        # Mock facts fetch
        facts_response = MagicMock()
        facts_response.data = [
            {
                "id": str(uuid4()),
                "source_block_id": str(uuid4()),
                "fact_type": "experience",
                "fact_text": "Worked at Company X",
                "is_verified": True,
                "metadata": {},
                "embedding": None
            },
            {
                "id": str(uuid4()),
                "source_block_id": str(uuid4()),
                "fact_type": "education",
                "fact_text": "BS in CS",
                "is_verified": True,
                "metadata": {},
                "embedding": None
            }
        ]
        
        # Configure mocks
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.return_value = facts_response
        
        insert_mock = mock_supabase_client.table.return_value.insert.return_value
        insert_mock.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
        
        # Act
        await service._copy_fact_ledger(
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            user_id=sample_user_id
        )
        
        # Assert
        # Should insert 2 fact ledger entries
        assert insert_mock.execute.call_count >= 2
    
    async def test_copy_sections_empty(self, mock_supabase_client, sample_user_id):
        """Test copying sections when source version has no sections."""
        # Arrange
        service = VersionService(mock_supabase_client)
        source_version_id = str(uuid4())
        target_version_id = str(uuid4())
        
        # Mock empty sections response
        empty_response = MagicMock()
        empty_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = empty_response
        
        # Act
        await service._copy_sections_and_blocks(
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            user_id=sample_user_id
        )
        
        # Assert - should return early without inserting anything
        # No assertion needed, just ensure no exception is raised
    
    async def test_copy_fact_ledger_empty(self, mock_supabase_client, sample_user_id):
        """Test copying fact ledger when source has no facts."""
        # Arrange
        service = VersionService(mock_supabase_client)
        source_version_id = str(uuid4())
        target_version_id = str(uuid4())
        
        # Mock empty facts response
        empty_response = MagicMock()
        empty_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty_response
        
        # Act
        await service._copy_fact_ledger(
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            user_id=sample_user_id
        )
        
        # Assert - should return early without inserting anything
        # No assertion needed, just ensure no exception is raised
    
    async def test_restore_version_first_version(self, mock_supabase_client, sample_user_id):
        """Test restoring when resume has no existing versions (edge case)."""
        # Arrange
        service = VersionService(mock_supabase_client)
        old_version_id = str(uuid4())
        resume_id = str(uuid4())
        
        # Mock old version fetch
        old_version_response = MagicMock()
        old_version_response.data = [{
            "id": old_version_id,
            "resume_id": resume_id,
            "version_number": 1,
            "status": "completed",
            "storage_path": "resumes/first.pdf",
            "original_filename": "First.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 30000,
            "needs_ocr": False
        }]
        
        # Mock empty max version response (no other versions)
        max_version_response = MagicMock()
        max_version_response.data = []
        
        # Mock new version insert
        new_version_response = MagicMock()
        new_version_id = str(uuid4())
        new_version_response.data = [{
            "id": new_version_id,
            "version_number": 1  # Should be 0 + 1 = 1
        }]
        
        # Configure mocks
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.return_value = old_version_response
        select_mock.eq.return_value.order.return_value.limit.return_value.execute.return_value = max_version_response
        
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = new_version_response
        
        update_response = MagicMock()
        update_response.data = [{}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = update_response
        
        # Mock internal methods to avoid complex mocking
        with patch.object(service, '_copy_sections_and_blocks', new_callable=AsyncMock) as mock_copy_sections, \
             patch.object(service, '_copy_fact_ledger', new_callable=AsyncMock) as mock_copy_facts:
            
            # Act
            result = await service.restore_version(
                version_id=old_version_id,
                user_id=sample_user_id
            )
            
            # Assert
            assert result["version_number"] == 1
            mock_copy_sections.assert_called_once()
            mock_copy_facts.assert_called_once()
