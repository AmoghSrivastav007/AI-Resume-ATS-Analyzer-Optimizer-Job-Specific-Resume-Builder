"""
Unit tests for Matching Service (Step 6).

Tests the complete matching pipeline including embedding generation,
4-layer matching, scoring, and persistence.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from uuid import uuid4
import os

from services.matching_service import MatchingService
from services.matching_engine import MatchResult


@pytest.fixture
def mock_anthropic_env():
    """Mock ANTHROPIC_API_KEY environment variable."""
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
        yield


@pytest.mark.unit
@pytest.mark.asyncio
class TestMatchingService:
    """Test suite for MatchingService."""
    
    async def test_ensure_embeddings_generates_missing(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test that missing embeddings are generated."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        job_posting_id = str(uuid4())
        resume_version_id = str(uuid4())
        
        # Mock requirements without embeddings
        requirements_response = MagicMock()
        requirements_response.data = [
            {"id": str(uuid4()), "requirement_text": "Python", "embedding": None},
            {"id": str(uuid4()), "requirement_text": "React", "embedding": None}
        ]
        
        # Mock skills without embeddings
        skills_response = MagicMock()
        skills_response.data = [
            {"id": str(uuid4()), "name": "JavaScript", "embedding": None}
        ]
        
        # Mock blocks, experiences (empty for simplicity)
        empty_response = MagicMock()
        empty_response.data = []
        
        # Configure mock chains
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.side_effect = [
            requirements_response,
            skills_response,
            empty_response,
            empty_response
        ]
        
        # Mock update responses
        update_response = MagicMock()
        update_response.data = [{"id": "updated"}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_response
        
        # Mock embedding service
        with patch.object(service.embedding_service, 'embed_text', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1536  # Mock embedding vector
            
            # Act
            await service.ensure_embeddings(
                job_posting_id=job_posting_id,
                resume_version_id=resume_version_id,
                user_id=sample_user_id
            )
            
            # Assert - should call embed_text 3 times (2 requirements + 1 skill)
            assert mock_embed.call_count == 3
    
    async def test_ensure_embeddings_skips_existing(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test that existing embeddings are not regenerated."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        job_posting_id = str(uuid4())
        resume_version_id = str(uuid4())
        
        # Mock requirements WITH embeddings
        requirements_response = MagicMock()
        requirements_response.data = [
            {"id": str(uuid4()), "requirement_text": "Python", "embedding": [0.1] * 1536}
        ]
        
        # Mock skills WITH embeddings
        skills_response = MagicMock()
        skills_response.data = [
            {"id": str(uuid4()), "name": "JavaScript", "embedding": [0.2] * 1536}
        ]
        
        # Mock blocks, experiences (empty)
        empty_response = MagicMock()
        empty_response.data = []
        
        # Configure mocks
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.side_effect = [
            requirements_response,
            skills_response,
            empty_response,
            empty_response
        ]
        
        # Mock embedding service
        with patch.object(service.embedding_service, 'embed_text', new_callable=AsyncMock) as mock_embed:
            # Act
            await service.ensure_embeddings(
                job_posting_id=job_posting_id,
                resume_version_id=resume_version_id,
                user_id=sample_user_id
            )
            
            # Assert - should NOT call embed_text (all embeddings exist)
            mock_embed.assert_not_called()
    
    async def test_run_matching_analysis_success(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test successful end-to-end matching analysis."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        resume_version_id = str(uuid4())
        job_posting_id = str(uuid4())
        
        # Mock match results from matching engine
        mock_match_results = [
            MatchResult(
                requirement_id=str(uuid4()),
                requirement_text="Python",
                requirement_type="required_skill",
                match_status="matched",
                match_layer=1,
                match_score=100.0,
                evidence_text="Python experience"
            ),
            MatchResult(
                requirement_id=str(uuid4()),
                requirement_text="React",
                requirement_type="required_skill",
                match_status="missing",
                match_layer=0,
                match_score=0.0
            )
        ]
        
        # Mock resume data
        resume_data = {
            "skills": [{"name": "Python"}],
            "experiences": [],
            "blocks": []
        }
        
        # Mock JD score
        from services.jd_match_scorer import JDMatchScore
        mock_jd_score = JDMatchScore(
            overall_score=75.0,
            keyword_relevance=80.0,
            skills_alignment=70.0,
            experience_relevance=75.0,
            breakdown={"matched": 1, "missing": 1},
            gap_analysis={"missing_skills": ["React"]}
        )
        
        # Mock database responses
        empty_response = MagicMock()
        empty_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty_response
        
        insert_response = MagicMock()
        insert_response.data = [{"id": str(uuid4())}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = insert_response
        
        # Patch internal methods
        with patch.object(service, 'ensure_embeddings', new_callable=AsyncMock) as mock_embeddings, \
             patch.object(service.matching_engine, 'match_all_requirements', new_callable=AsyncMock) as mock_match, \
             patch.object(service, '_get_resume_data', new_callable=AsyncMock) as mock_resume_data, \
             patch.object(service.scorer, 'calculate_jd_match_score') as mock_scorer:
            
            mock_embeddings.return_value = None
            mock_match.return_value = mock_match_results
            mock_resume_data.return_value = resume_data
            mock_scorer.return_value = mock_jd_score
            
            # Act
            result = await service.run_matching_analysis(
                resume_version_id=resume_version_id,
                job_posting_id=job_posting_id,
                user_id=sample_user_id
            )
            
            # Assert
            assert "analysis_id" in result
            assert result["jd_match_score"] == 75.0
            assert result["keyword_relevance"] == 80.0
            assert result["skills_alignment"] == 70.0
            assert result["experience_relevance"] == 75.0
            assert result["total_requirements"] == 2
            assert result["matched"] == 1
            assert result["missing"] == 1
            
            # Verify workflow
            mock_embeddings.assert_called_once()
            mock_match.assert_called_once()
            mock_resume_data.assert_called_once()
            mock_scorer.assert_called_once()
    
    async def test_get_resume_data(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test fetching complete resume data."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        resume_version_id = str(uuid4())
        
        # Mock responses
        skills_response = MagicMock()
        skills_response.data = [{"name": "Python"}]
        
        experiences_response = MagicMock()
        experiences_response.data = [{"title": "Engineer", "company": "TechCorp"}]
        
        blocks_response = MagicMock()
        blocks_response.data = [{"content": {"text": "Sample text"}}]
        
        # Configure mock to return different responses
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.side_effect = [
            skills_response,
            experiences_response,
            blocks_response
        ]
        
        # Act
        result = await service._get_resume_data(resume_version_id, sample_user_id)
        
        # Assert
        assert "skills" in result
        assert "experiences" in result
        assert "blocks" in result
        assert len(result["skills"]) == 1
        assert len(result["experiences"]) == 1
        assert len(result["blocks"]) == 1
    
    async def test_persist_results(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test persisting match results to database."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        resume_version_id = str(uuid4())
        job_posting_id = str(uuid4())
        
        match_results = [
            MatchResult(
                requirement_id=str(uuid4()),
                requirement_text="Python",
                requirement_type="required_skill",
                match_status="matched",
                match_layer=1,
                match_score=100.0
            )
        ]
        
        from services.jd_match_scorer import JDMatchScore
        jd_score = JDMatchScore(
            overall_score=80.0,
            keyword_relevance=85.0,
            skills_alignment=75.0,
            experience_relevance=80.0,
            breakdown={"matched": 1},
            gap_analysis={}
        )
        
        # Mock insert responses
        insert_response = MagicMock()
        insert_response.data = [{"id": str(uuid4())}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = insert_response
        
        # Act
        analysis_id = await service._persist_results(
            resume_version_id=resume_version_id,
            job_posting_id=job_posting_id,
            user_id=sample_user_id,
            match_results=match_results,
            jd_score=jd_score
        )
        
        # Assert
        assert analysis_id is not None
        # Should insert 2 records: 1 analysis + 1 match_result
        assert mock_supabase_client.table.return_value.insert.return_value.execute.call_count == 2
    
    def test_serialize_match_result(self, mock_supabase_client, mock_anthropic_env):
        """Test serializing MatchResult to dict."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        match_result = MatchResult(
            requirement_id=str(uuid4()),
            requirement_text="Python",
            requirement_type="required_skill",
            match_status="matched",
            match_layer=1,
            match_score=100.0,
            evidence_text="Python development",
            similarity_score=0.95,
            recommendation="Strong match"
        )
        
        # Act
        serialized = service._serialize_match_result(match_result)
        
        # Assert
        assert serialized["requirement_text"] == "Python"
        assert serialized["match_status"] == "matched"
        assert serialized["match_layer"] == 1
        assert serialized["match_score"] == 100.0
        assert serialized["similarity_score"] == 0.95
    
    async def test_get_match_results(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test retrieving match results for an analysis."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        analysis_id = str(uuid4())
        
        # Mock analysis response
        analysis_response = MagicMock()
        analysis_response.data = {
            "id": analysis_id,
            "overall_score": 85.0,
            "status": "completed"
        }
        
        # Mock matches response
        matches_response = MagicMock()
        matches_response.data = [
            {
                "id": str(uuid4()),
                "match_status": "matched",
                "match_score": 100.0,
                "job_requirements": {"requirement_text": "Python"}
            },
            {
                "id": str(uuid4()),
                "match_status": "missing",
                "match_score": 0.0,
                "job_requirements": {"requirement_text": "React"}
            }
        ]
        
        # Configure mocks
        single_mock = mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value
        single_mock.execute.return_value = analysis_response
        
        select_mock = mock_supabase_client.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.return_value = matches_response
        
        # Act
        result = await service.get_match_results(analysis_id, sample_user_id)
        
        # Assert
        assert "analysis" in result
        assert "match_results" in result
        assert "grouped_matches" in result
        assert "summary" in result
        assert result["summary"]["total"] == 2
        assert result["summary"]["matched"] == 1
        assert result["summary"]["missing"] == 1
    
    async def test_get_match_results_not_found(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test error handling when analysis not found."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        analysis_id = str(uuid4())
        
        # Mock empty response
        analysis_response = MagicMock()
        analysis_response.data = None
        
        single_mock = mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value
        single_mock.execute.return_value = analysis_response
        
        # Act & Assert
        with pytest.raises(ValueError, match="Analysis not found"):
            await service.get_match_results(analysis_id, sample_user_id)


@pytest.mark.unit
@pytest.mark.asyncio
class TestMatchingServiceIntegration:
    """Integration-style tests for matching service workflows."""
    
    async def test_full_matching_workflow(self, mock_supabase_client, sample_user_id, mock_anthropic_env):
        """Test complete matching workflow from start to finish."""
        # Arrange
        service = MatchingService(mock_supabase_client)
        resume_version_id = str(uuid4())
        job_posting_id = str(uuid4())
        
        # Setup extensive mocks for full workflow
        # This test validates the orchestration works end-to-end
        
        # Mock all database operations
        empty_response = MagicMock()
        empty_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty_response
        
        insert_response = MagicMock()
        insert_response.data = [{"id": str(uuid4())}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = insert_response
        
        update_response = MagicMock()
        update_response.data = [{"id": "updated"}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_response
        
        # Patch all internal operations
        with patch.object(service, 'ensure_embeddings', new_callable=AsyncMock), \
             patch.object(service.matching_engine, 'match_all_requirements', new_callable=AsyncMock) as mock_match, \
             patch.object(service, '_get_resume_data', new_callable=AsyncMock) as mock_data, \
             patch.object(service.scorer, 'calculate_jd_match_score') as mock_score:
            
            # Setup return values
            mock_match.return_value = []
            mock_data.return_value = {"skills": [], "experiences": [], "blocks": []}
            
            from services.jd_match_scorer import JDMatchScore
            mock_score.return_value = JDMatchScore(
                overall_score=70.0,
                keyword_relevance=70.0,
                skills_alignment=70.0,
                experience_relevance=70.0,
                breakdown={},
                gap_analysis={}
            )
            
            # Act
            result = await service.run_matching_analysis(
                resume_version_id=resume_version_id,
                job_posting_id=job_posting_id,
                user_id=sample_user_id
            )
            
            # Assert - verify complete workflow executed
            assert result is not None
            assert "analysis_id" in result
            assert "jd_match_score" in result
            assert result["jd_match_score"] == 70.0
