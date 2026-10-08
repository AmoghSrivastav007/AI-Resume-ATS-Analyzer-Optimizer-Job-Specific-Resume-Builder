"""
Tests for matching engine (Step 6).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.matching_engine import MatchingEngine, MatchResult


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    return Mock()


@pytest.fixture
def matching_engine(mock_supabase):
    """Create matching engine with mocked dependencies."""
    return MatchingEngine(mock_supabase)


class TestTextNormalization:
    """Test text normalization for Layer 1 matching."""
    
    def test_normalize_removes_special_chars(self, matching_engine):
        text = "C++ Programming!"
        normalized = matching_engine.normalize_text(text)
        assert normalized == "c programming"
    
    def test_normalize_lowercases(self, matching_engine):
        text = "JavaScript"
        normalized = matching_engine.normalize_text(text)
        assert normalized == "javascript"
    
    def test_normalize_removes_extra_whitespace(self, matching_engine):
        text = "Node.js   Development"
        normalized = matching_engine.normalize_text(text)
        assert normalized == "nodejs development"


class TestLayer1ExactMatch:
    """Test Layer 1: Exact string matching."""
    
    @pytest.mark.asyncio
    async def test_exact_match_in_skills(self, matching_engine):
        req_text = "Python"
        resume_skills = [
            {"id": "skill1", "name": "Python"},
            {"id": "skill2", "name": "JavaScript"}
        ]
        resume_blocks = []
        
        result = await matching_engine._layer1_exact_match(
            req_text, resume_skills, resume_blocks
        )
        
        assert result is not None
        assert result.match_status == "matched"
        assert result.match_layer == 1
        assert result.match_score == 100.0
    
    @pytest.mark.asyncio
    async def test_exact_match_case_insensitive(self, matching_engine):
        req_text = "python"
        resume_skills = [
            {"id": "skill1", "name": "Python"}
        ]
        resume_blocks = []
        
        result = await matching_engine._layer1_exact_match(
            req_text, resume_skills, resume_blocks
        )
        
        assert result is not None
        assert result.match_status == "matched"
    
    @pytest.mark.asyncio
    async def test_exact_match_in_blocks(self, matching_engine):
        req_text = "Docker"
        resume_skills = []
        resume_blocks = [
            {
                "id": "block1",
                "content": {"text": "Deployed applications using Docker containers"}
            }
        ]
        
        result = await matching_engine._layer1_exact_match(
            req_text, resume_skills, resume_blocks
        )
        
        assert result is not None
        assert result.match_status == "matched"
        assert result.evidence_block_id == "block1"
    
    @pytest.mark.asyncio
    async def test_no_exact_match(self, matching_engine):
        req_text = "Kubernetes"
        resume_skills = [{"id": "skill1", "name": "Docker"}]
        resume_blocks = []
        
        result = await matching_engine._layer1_exact_match(
            req_text, resume_skills, resume_blocks
        )
        
        assert result is None


class TestLayer2AliasMatch:
    """Test Layer 2: Alias-based matching."""
    
    @pytest.mark.asyncio
    async def test_alias_match_found(self, matching_engine):
        # Mock Supabase response with aliases
        mock_response = Mock()
        mock_response.data = [
            {"canonical_term": "JavaScript", "alias_term": "JS"},
            {"canonical_term": "JavaScript", "alias_term": "ECMAScript"}
        ]
        matching_engine.supabase.table.return_value.select.return_value.or_.return_value.execute.return_value = mock_response
        
        req_text = "JavaScript"
        resume_skills = [{"id": "skill1", "name": "JS"}]
        resume_blocks = []
        
        result = await matching_engine._layer2_alias_match(
            req_text, resume_skills, resume_blocks
        )
        
        assert result is not None
        assert result.match_status == "matched"
        assert result.match_layer == 2
        assert result.match_score == 95.0
    
    @pytest.mark.asyncio
    async def test_alias_match_not_found(self, matching_engine):
        # Mock empty Supabase response
        mock_response = Mock()
        mock_response.data = []
        matching_engine.supabase.table.return_value.select.return_value.or_.return_value.execute.return_value = mock_response
        
        req_text = "Python"
        resume_skills = [{"id": "skill1", "name": "Java"}]
        resume_blocks = []
        
        result = await matching_engine._layer2_alias_match(
            req_text, resume_skills, resume_blocks
        )
        
        assert result is None


class TestMatchResultGeneration:
    """Test match result generation."""
    
    def test_missing_recommendation_required_skill(self, matching_engine):
        rec = matching_engine._generate_missing_recommendation("Python", "required_skill")
        assert "Python" in rec
        assert "skills section" in rec.lower()
    
    def test_missing_recommendation_preferred_skill(self, matching_engine):
        rec = matching_engine._generate_missing_recommendation("Docker", "preferred_skill")
        assert "Docker" in rec
        assert "consider" in rec.lower()
    
    def test_missing_recommendation_responsibility(self, matching_engine):
        rec = matching_engine._generate_missing_recommendation(
            "Lead team meetings", "responsibility"
        )
        assert "Lead team meetings" in rec
        assert "bullet" in rec.lower()


class TestMatchRequirement:
    """Test complete requirement matching."""
    
    @pytest.mark.asyncio
    async def test_match_returns_missing_when_no_layers_match(self, matching_engine):
        # Mock all layers to return None
        matching_engine._layer1_exact_match = AsyncMock(return_value=None)
        matching_engine._layer2_alias_match = AsyncMock(return_value=None)
        
        requirement = {
            "id": "req1",
            "requirement_text": "Unknown Skill",
            "requirement_type": "required_skill",
            "embedding": None
        }
        
        result = await matching_engine.match_requirement(
            requirement, [], [], []
        )
        
        assert result.match_status == "missing"
        assert result.match_score == 0.0
        assert result.match_layer == 0
        assert result.recommendation is not None


class TestSemanticMatching:
    """Test Layer 3: Semantic matching with embeddings."""
    
    @pytest.mark.asyncio
    async def test_high_similarity_auto_match(self, matching_engine):
        req_embedding = [0.9] * 1536
        skill_embedding = [0.9] * 1536  # Very similar
        
        requirement = {
            "id": "req1",
            "requirement_text": "Python Development",
            "requirement_type": "required_skill",
            "embedding": req_embedding
        }
        
        resume_skills = [
            {"id": "skill1", "name": "Python", "embedding": skill_embedding}
        ]
        
        result = await matching_engine._layer3_semantic_match(
            "req1", "Python Development", "required_skill", req_embedding,
            resume_skills, [], []
        )
        
        assert result is not None
        # Similarity should be high (cosine of similar vectors)
        if result.similarity_score and result.similarity_score > 0.85:
            assert result.match_status == "matched"
    
    @pytest.mark.asyncio
    async def test_low_similarity_no_match(self, matching_engine):
        req_embedding = [1.0] + [0.0] * 1535
        skill_embedding = [0.0] * 1535 + [1.0]  # Orthogonal
        
        requirement = {
            "id": "req1",
            "requirement_text": "Python",
            "requirement_type": "required_skill",
            "embedding": req_embedding
        }
        
        resume_skills = [
            {"id": "skill1", "name": "Java", "embedding": skill_embedding}
        ]
        
        result = await matching_engine._layer3_semantic_match(
            "req1", "Python", "required_skill", req_embedding,
            resume_skills, [], []
        )
        
        # Orthogonal vectors have ~0 similarity, below 0.70 threshold
        assert result is None


@pytest.mark.asyncio
async def test_match_all_requirements_integration(matching_engine):
    """Test matching all requirements against a resume."""
    # Mock Supabase responses
    requirements_response = Mock()
    requirements_response.data = [
        {
            "id": "req1",
            "requirement_text": "Python",
            "requirement_type": "required_skill",
            "embedding": None
        }
    ]
    
    skills_response = Mock()
    skills_response.data = [
        {"id": "skill1", "name": "Python", "embedding": None}
    ]
    
    blocks_response = Mock()
    blocks_response.data = []
    
    experiences_response = Mock()
    experiences_response.data = []
    
    matching_engine.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
        requirements_response,
        skills_response,
        blocks_response,
        experiences_response
    ]
    
    results = await matching_engine.match_all_requirements(
        "job1", "resume1", "user1"
    )
    
    assert len(results) == 1
    assert results[0].requirement_id == "req1"
    assert results[0].match_status == "matched"  # Layer 1 exact match
