"""
Unit tests for Block Editor Service (Step 8).

Tests block editing operations including manual edits, AI rewrites with Truth Guard,
block creation/deletion, and reordering.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from uuid import uuid4

from services.block_editor_service import BlockEditorService


@pytest.mark.unit
@pytest.mark.asyncio
class TestBlockEditorService:
    """Test suite for BlockEditorService."""
    
    async def test_update_block_content_success(self, mock_supabase_client, sample_user_id):
        """Test successful block content update."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        block_id = str(uuid4())
        new_content = {"text": "Updated content"}
        block_type = "text"
        
        # Mock successful update
        mock_response = MagicMock()
        mock_response.data = [{
            "id": block_id,
            "content": new_content,
            "block_type": block_type,
            "updated_at": "2026-10-07T10:00:00"
        }]
        
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        # Act
        result = await service.update_block(
            block_id=block_id,
            content=new_content,
            block_type=block_type,
            user_id=sample_user_id
        )
        
        # Assert
        assert result["id"] == block_id
        assert result["content"] == new_content
        assert result["block_type"] == block_type
        mock_supabase_client.table.assert_called_with("resume_blocks")
    
    async def test_update_block_not_found(self, mock_supabase_client, sample_user_id):
        """Test updating a non-existent block raises error."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        block_id = str(uuid4())
        
        # Mock empty response (block not found)
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(ValueError, match="Block not found or update failed"):
            await service.update_block(
                block_id=block_id,
                content={"text": "New text"},
                block_type=None,
                user_id=sample_user_id
            )
    
    async def test_create_block_success(self, mock_supabase_client, sample_user_id):
        """Test successful block creation."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        section_id = str(uuid4())
        resume_version_id = str(uuid4())
        content = {"company": "Tech Corp", "title": "Engineer"}
        block_type = "experience"
        
        # Mock max sort_order query
        sort_response = MagicMock()
        sort_response.data = [{"sort_order": 2}]
        
        # Mock insert response
        insert_response = MagicMock()
        new_block_id = str(uuid4())
        insert_response.data = [{
            "id": new_block_id,
            "section_id": section_id,
            "content": content,
            "block_type": block_type,
            "sort_order": 3
        }]
        
        # Configure mock chain
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = sort_response
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = insert_response
        
        # Act
        result = await service.create_block(
            section_id=section_id,
            resume_version_id=resume_version_id,
            content=content,
            block_type=block_type,
            user_id=sample_user_id
        )
        
        # Assert
        assert result["id"] == new_block_id
        assert result["sort_order"] == 3  # max + 1
        assert result["content"] == content
    
    async def test_create_block_first_in_section(self, mock_supabase_client, sample_user_id):
        """Test creating the first block in an empty section."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        section_id = str(uuid4())
        resume_version_id = str(uuid4())
        
        # Mock empty section (no existing blocks)
        sort_response = MagicMock()
        sort_response.data = []
        
        # Mock insert response
        insert_response = MagicMock()
        new_block_id = str(uuid4())
        insert_response.data = [{
            "id": new_block_id,
            "section_id": section_id,
            "sort_order": 1  # First block should be 1 (0 + 1)
        }]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = sort_response
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = insert_response
        
        # Act
        result = await service.create_block(
            section_id=section_id,
            resume_version_id=resume_version_id,
            content={"text": "First block"},
            block_type="text",
            user_id=sample_user_id
        )
        
        # Assert
        assert result["sort_order"] == 1
    
    async def test_reorder_blocks_success(self, mock_supabase_client, sample_user_id):
        """Test successful block reordering."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        section_id = str(uuid4())
        block_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
        
        # Mock update responses
        mock_response = MagicMock()
        mock_response.data = [{"id": "updated"}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        # Act
        await service.reorder_blocks(
            section_id=section_id,
            block_ids=block_ids,
            user_id=sample_user_id
        )
        
        # Assert - called 3 times (once per block)
        assert mock_supabase_client.table.call_count >= 3
    
    async def test_apply_rewrite_success(self, mock_supabase_client, sample_user_id):
        """Test applying AI-generated rewrite to a block."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        block_id = str(uuid4())
        proposed_text = "Improved text with better phrasing"
        
        # Mock fetch current block
        fetch_response = MagicMock()
        fetch_response.data = [{
            "id": block_id,
            "content": {"text": "Original text", "metadata": "some_data"}
        }]
        
        # Mock update response
        update_response = MagicMock()
        update_response.data = [{
            "id": block_id,
            "content": {"text": proposed_text, "metadata": "some_data"}
        }]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = fetch_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = update_response
        
        # Act
        result = await service.apply_rewrite(
            block_id=block_id,
            proposed_text=proposed_text,
            user_id=sample_user_id
        )
        
        # Assert
        assert result["content"]["text"] == proposed_text
        assert result["content"]["metadata"] == "some_data"  # Preserves other content
    
    async def test_apply_rewrite_block_not_found(self, mock_supabase_client, sample_user_id):
        """Test applying rewrite to non-existent block raises error."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        block_id = str(uuid4())
        
        # Mock empty response
        fetch_response = MagicMock()
        fetch_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = fetch_response
        
        # Act & Assert
        with pytest.raises(ValueError, match="Block not found"):
            await service.apply_rewrite(
                block_id=block_id,
                proposed_text="New text",
                user_id=sample_user_id
            )
    
    async def test_fetch_fact_ledger(self, mock_supabase_client, sample_user_id):
        """Test fetching fact ledger for a resume version."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        resume_version_id = str(uuid4())
        
        # Mock fact ledger response
        fact_response = MagicMock()
        fact_response.data = [
            {
                "id": str(uuid4()),
                "fact_type": "experience",
                "fact_text": "Worked at Tech Corp as Software Engineer",
                "is_verified": True
            },
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "Python programming",
                "is_verified": True
            }
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = fact_response
        
        # Act
        result = await service._fetch_fact_ledger(
            resume_version_id=resume_version_id,
            user_id=sample_user_id
        )
        
        # Assert
        assert len(result) == 2
        assert result[0]["fact_type"] == "experience"
        assert result[1]["fact_type"] == "skill"
    
    def test_format_fact_ledger_with_facts(self, mock_supabase_client):
        """Test formatting fact ledger for prompt."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        fact_ledger = [
            {"fact_type": "experience", "fact_text": "Worked at Company X"},
            {"fact_type": "education", "fact_text": "BS in Computer Science"},
            {"fact_type": "skill", "fact_text": "Python programming"}
        ]
        
        # Act
        result = service._format_fact_ledger(fact_ledger)
        
        # Assert
        assert "[EXPERIENCE]" in result
        assert "[EDUCATION]" in result
        assert "[SKILL]" in result
        assert "Worked at Company X" in result
        assert "BS in Computer Science" in result
        assert "Python programming" in result
    
    def test_format_fact_ledger_empty(self, mock_supabase_client):
        """Test formatting empty fact ledger."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        fact_ledger = []
        
        # Act
        result = service._format_fact_ledger(fact_ledger)
        
        # Assert
        assert "No facts in ledger" in result
        assert "rephrase only" in result


@pytest.mark.unit
@pytest.mark.asyncio
class TestBlockEditorAIRewrite:
    """Test AI rewrite functionality with Truth Guard integration."""
    
    async def test_ai_rewrite_block_no_text(self, mock_supabase_client, sample_user_id):
        """Test AI rewrite on block with no text content raises error."""
        # Arrange
        service = BlockEditorService(mock_supabase_client)
        block_id = str(uuid4())
        resume_version_id = str(uuid4())
        
        # Mock block with no text
        block_response = MagicMock()
        block_response.data = [{
            "id": block_id,
            "content": {"metadata": "some_data"}  # No "text" key
        }]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = block_response
        
        # Act & Assert
        with pytest.raises(ValueError, match="Block has no text content"):
            await service.ai_rewrite_block(
                block_id=block_id,
                instruction="shorten",
                context=None,
                user_id=sample_user_id,
                resume_version_id=resume_version_id
            )
    
    async def test_generate_rewrite_with_anthropic(self, mock_supabase_client):
        """Test generating rewrite with Anthropic API."""
        # Arrange
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = BlockEditorService(mock_supabase_client)
            
            # Mock Anthropic response
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Improved and concise text with better phrasing."
            mock_response.content = [mock_content]
            
            service.anthropic = MagicMock()
            service.anthropic.messages.create.return_value = mock_response
            
            original_text = "This is some text that could be improved and made more concise."
            fact_ledger = [
                {"fact_type": "skill", "fact_text": "Python programming"}
            ]
            
            # Act
            result = await service._generate_rewrite(
                original_text=original_text,
                instruction="shorten",
                context=None,
                fact_ledger=fact_ledger,
                model="claude-haiku-4-5-20251001"
            )
            
            # Assert
            assert result == "Improved and concise text with better phrasing."
            service.anthropic.messages.create.assert_called_once()
            
            # Verify prompt contains critical rules
            call_args = service.anthropic.messages.create.call_args
            prompt = call_args[1]["messages"][0]["content"]
            assert "CRITICAL RULES" in prompt
            assert "FACT LEDGER" in prompt
            assert original_text in prompt
    
    async def test_generate_rewrite_api_error(self, mock_supabase_client):
        """Test handling Anthropic API errors."""
        # Arrange
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = BlockEditorService(mock_supabase_client)
            
            # Mock API error
            service.anthropic = MagicMock()
            service.anthropic.messages.create.side_effect = Exception("API Error")
            
            # Act & Assert
            with pytest.raises(ValueError, match="Failed to generate rewrite"):
                await service._generate_rewrite(
                    original_text="Some text",
                    instruction="improve",
                    context=None,
                    fact_ledger=[],
                    model="claude-haiku-4-5-20251001"
                )
