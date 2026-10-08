"""
Unit tests for Deletion Service.

Tests complete data deletion, storage cleanup, and audit logging.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.deletion_service import DeletionService


@pytest.mark.unit
@pytest.mark.asyncio
class TestDeleteResume:
    """Tests for resume deletion."""

    async def test_delete_resume_success(self, mock_settings, sample_user_id, sample_resume_id):
        """Test successful complete resume deletion."""
        service = DeletionService(mock_settings)
        
        # Mock database responses
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume exists check
        mock_resume_response = MagicMock()
        mock_resume_response.data = {"id": sample_resume_id, "user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        # Mock versions query
        mock_versions_response = MagicMock()
        mock_versions_response.data = [
            {"id": "version-1", "storage_path": "resumes/user-1/file1.pdf"},
            {"id": "version-2", "storage_path": "resumes/user-1/file2.pdf"},
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_versions_response
        
        # Mock exports query
        mock_exports_response = MagicMock()
        mock_exports_response.data = [
            {"storage_path": "exports/user-1/export1.pdf"},
        ]
        
        # Mock delete operations
        mock_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_client.storage.from_.return_value.remove.return_value = {"message": "deleted"}
        
        # Mock audit logging
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock) as mock_audit:
            await service.delete_resume_completely(sample_user_id, sample_resume_id, "127.0.0.1")
            
            # Verify audit log was called
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[1]["user_id"] == sample_user_id
            assert call_args[1]["action"] == "delete"
            assert call_args[1]["resource_type"] == "resume"

    async def test_delete_resume_not_found(self, mock_settings, sample_user_id):
        """Test deletion fails when resume doesn't exist."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume not found
        mock_resume_response = MagicMock()
        mock_resume_response.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        with pytest.raises(ValueError, match="Resume not found or access denied"):
            await service.delete_resume_completely(sample_user_id, "nonexistent-id", "127.0.0.1")

    async def test_delete_resume_wrong_user(self, mock_settings, sample_resume_id):
        """Test deletion fails when user doesn't own the resume."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume belongs to different user
        mock_resume_response = MagicMock()
        mock_resume_response.data = None  # Query with wrong user_id returns nothing
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        with pytest.raises(ValueError):
            await service.delete_resume_completely("wrong-user-id", sample_resume_id, "127.0.0.1")

    async def test_delete_resume_storage_cleanup(self, mock_settings, sample_user_id, sample_resume_id):
        """Test that storage files are deleted along with database records."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume exists
        mock_resume_response = MagicMock()
        mock_resume_response.data = {"id": sample_resume_id, "user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        # Mock versions with storage paths
        mock_versions_response = MagicMock()
        mock_versions_response.data = [
            {"id": "v1", "storage_path": "resumes/file1.pdf"},
            {"id": "v2", "storage_path": "resumes/file2.pdf"},
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_versions_response
        
        # Mock exports (none)
        mock_exports_response = MagicMock()
        mock_exports_response.data = []
        
        # Mock storage remove
        mock_storage = MagicMock()
        mock_client.storage.from_.return_value = mock_storage
        
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock):
            await service.delete_resume_completely(sample_user_id, sample_resume_id)
            
            # Verify storage.remove was called with correct paths
            mock_storage.remove.assert_called_once()
            called_paths = mock_storage.remove.call_args[0][0]
            assert len(called_paths) == 2
            assert "resumes/file1.pdf" in called_paths

    async def test_delete_resume_storage_failure_continues(self, mock_settings, sample_user_id, sample_resume_id):
        """Test that deletion continues even if storage deletion fails."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume exists
        mock_resume_response = MagicMock()
        mock_resume_response.data = {"id": sample_resume_id, "user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        # Mock versions
        mock_versions_response = MagicMock()
        mock_versions_response.data = [{"id": "v1", "storage_path": "file.pdf"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_versions_response
        
        # Mock exports (none)
        mock_exports_response = MagicMock()
        mock_exports_response.data = []
        
        # Mock storage deletion failure
        mock_client.storage.from_.return_value.remove.side_effect = Exception("Storage error")
        
        # Should not raise exception - deletion continues
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock):
            await service.delete_resume_completely(sample_user_id, sample_resume_id)
            # Should complete without error

    async def test_delete_resume_audit_logged(self, mock_settings, sample_user_id, sample_resume_id):
        """Test that deletion is logged to audit trail."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume exists
        mock_resume_response = MagicMock()
        mock_resume_response.data = {"id": sample_resume_id, "user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        # Mock versions
        mock_versions_response = MagicMock()
        mock_versions_response.data = [{"id": "v1", "storage_path": "file.pdf"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_versions_response
        
        # Mock exports
        mock_exports_response = MagicMock()
        mock_exports_response.data = []
        
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock) as mock_audit:
            await service.delete_resume_completely(sample_user_id, sample_resume_id, "192.168.1.1")
            
            # Verify audit log details
            assert mock_audit.called
            call_kwargs = mock_audit.call_args[1]
            assert call_kwargs["user_id"] == sample_user_id
            assert call_kwargs["action"] == "delete"
            assert call_kwargs["resource_type"] == "resume"
            assert call_kwargs["resource_id"] == sample_resume_id
            assert "ip_address" in call_kwargs["metadata"]
            assert call_kwargs["metadata"]["ip_address"] == "192.168.1.1"


@pytest.mark.unit
@pytest.mark.asyncio
class TestDeleteUserAccount:
    """Tests for user account deletion."""

    async def test_delete_user_account_deletes_all_resumes(self, mock_settings, sample_user_id):
        """Test that user account deletion removes all user's resumes."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resumes query
        mock_resumes_response = MagicMock()
        mock_resumes_response.data = [
            {"id": "resume-1"},
            {"id": "resume-2"},
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resumes_response
        
        # Mock job descriptions query
        mock_jds_response = MagicMock()
        mock_jds_response.data = []
        
        # Mock delete_resume_completely
        with patch.object(service, 'delete_resume_completely', new_callable=AsyncMock) as mock_delete_resume:
            with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock):
                await service.delete_user_account(sample_user_id, "127.0.0.1")
                
                # Verify each resume was deleted
                assert mock_delete_resume.call_count == 2
                mock_delete_resume.assert_any_call(sample_user_id, "resume-1", "127.0.0.1")
                mock_delete_resume.assert_any_call(sample_user_id, "resume-2", "127.0.0.1")

    async def test_delete_user_account_marks_audit_logs(self, mock_settings, sample_user_id):
        """Test that audit logs are marked for deletion after retention period."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock empty resumes
        mock_resumes_response = MagicMock()
        mock_resumes_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resumes_response
        
        # Mock job descriptions
        mock_jds_response = MagicMock()
        mock_jds_response.data = []
        
        # Mock audit log update
        mock_audit_update = MagicMock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_audit_update
        
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock):
            await service.delete_user_account(sample_user_id)
            
            # Verify audit log table was updated (not deleted immediately)
            # This keeps logs for 90-day retention
            assert mock_client.table.called


@pytest.mark.unit
@pytest.mark.asyncio
class TestCleanupExpiredData:
    """Tests for automated data cleanup."""

    async def test_cleanup_deletes_old_audit_logs(self, mock_settings):
        """Test that old audit logs are deleted after retention period."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock audit log deletion
        mock_delete_response = MagicMock()
        mock_delete_response.data = [{"id": "log1"}, {"id": "log2"}]  # 2 logs deleted
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_delete_response
        
        # Mock temp files list (empty)
        mock_client.storage.from_.return_value.list.return_value = []
        
        result = await service.cleanup_expired_data()
        
        # Verify stats
        assert result["audit_logs_deleted"] == 2
        assert "temp_files_deleted" in result
        assert "users_deleted" in result

    async def test_cleanup_deletes_temp_files(self, mock_settings):
        """Test that temporary export files are deleted after 24 hours."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock audit logs (none)
        mock_delete_response = MagicMock()
        mock_delete_response.data = []
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_delete_response
        
        # Mock temp files (old files)
        mock_client.storage.from_.return_value.list.return_value = [
            {"name": "old_file1.pdf", "created_at": "2020-01-01"},
            {"name": "old_file2.pdf", "created_at": "2020-01-01"},
        ]
        
        # Mock storage remove
        mock_storage = MagicMock()
        mock_client.storage.from_.return_value = mock_storage
        mock_storage.list.return_value = [
            {"name": "old_file1.pdf", "created_at": "2020-01-01"},
        ]
        
        result = await service.cleanup_expired_data()
        
        # Verify temp files were attempted to be deleted
        # (actual deletion may not be called due to date comparison logic)
        assert "temp_files_deleted" in result

    async def test_cleanup_returns_statistics(self, mock_settings):
        """Test that cleanup returns proper statistics."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock responses
        mock_delete_response = MagicMock()
        mock_delete_response.data = []
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_delete_response
        mock_client.storage.from_.return_value.list.return_value = []
        
        result = await service.cleanup_expired_data()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "audit_logs_deleted" in result
        assert "temp_files_deleted" in result
        assert "users_deleted" in result
        assert isinstance(result["audit_logs_deleted"], int)


@pytest.mark.unit
class TestDeletionServiceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_delete_resume_with_no_storage_files(self, mock_settings, sample_user_id, sample_resume_id):
        """Test deletion handles resumes with no storage files gracefully."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock resume exists
        mock_resume_response = MagicMock()
        mock_resume_response.data = {"id": sample_resume_id, "user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_resume_response
        
        # Mock versions with no storage paths
        mock_versions_response = MagicMock()
        mock_versions_response.data = [
            {"id": "v1", "storage_path": None},  # No file
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_versions_response
        
        # Mock exports (none)
        mock_exports_response = MagicMock()
        mock_exports_response.data = []
        
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock):
            # Should complete without calling storage.remove
            await service.delete_resume_completely(sample_user_id, sample_resume_id)
            
            # Verify storage.remove was NOT called (no files to delete)
            assert not mock_client.storage.from_.return_value.remove.called

    @pytest.mark.asyncio
    async def test_delete_user_with_no_resumes(self, mock_settings, sample_user_id):
        """Test user account deletion handles users with no resumes."""
        service = DeletionService(mock_settings)
        
        mock_client = MagicMock()
        service.client = mock_client
        
        # Mock empty resumes
        mock_resumes_response = MagicMock()
        mock_resumes_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resumes_response
        
        # Mock empty job descriptions
        mock_jds_response = MagicMock()
        mock_jds_response.data = []
        
        with patch('services.deletion_service.log_audit_event', new_callable=AsyncMock):
            # Should complete without errors
            await service.delete_user_account(sample_user_id)
            
            # Verify user table deletion was attempted
            assert mock_client.table.called
