"""
Tests for Step 6: Matching Engine Deterministic Logic.

Tests pure functions with zero variance:
- Text normalization
- Layer 1 exact matching logic
- Layer 2 alias matching logic
- Match scoring calculations

Note: Layer 3 (semantic/vector) and Layer 4 (LLM) are NOT tested here
as they involve non-deterministic components (embeddings, LLM).
"""

import pytest
import os
from services.matching_engine import MatchingEngine, MatchResult
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_anthropic_env(monkeypatch):
    """Mock ANTHROPIC_API_KEY for all tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-12345")
    yield


class TestTextNormalization:
    """Tests for normalize_text() deterministic function."""
    
    def test_normalize_text_basic(self):
        """Basic text normalization."""
        engine = MatchingEngine(Mock())
        
        result = engine.normalize_text("Python Programming")
        
        assert result == "python programming"
        
        # Determinism
        result2 = engine.normalize_text("Python Programming")
        assert result2 == result
    
    def test_normalize_text_special_chars(self):
        """Remove special characters and punctuation."""
        engine = MatchingEngine(Mock())
        
        result = engine.normalize_text("Node.js & React!")
        
        assert result == "nodejs react"
        assert "." not in result
        assert "&" not in result
        assert "!" not in result
        
        # Determinism
        result2 = engine.normalize_text("Node.js & React!")
        assert result2 == result
    
    def test_normalize_text_multiple_spaces(self):
        """Collapse multiple spaces to single space."""
        engine = MatchingEngine(Mock())
        
        result = engine.normalize_text("Machine    Learning     AI")
        
        assert result == "machine learning ai"
        assert "  " not in result
        
        # Determinism
        result2 = engine.normalize_text("Machine    Learning     AI")
        assert result2 == result
    
    def test_normalize_text_whitespace(self):
        """Trim leading/trailing whitespace."""
        engine = MatchingEngine(Mock())
        
        result = engine.normalize_text("  Data Science  ")
        
        assert result == "data science"
        assert not result.startswith(" ")
        assert not result.endswith(" ")
        
        # Determinism
        result2 = engine.normalize_text("  Data Science  ")
        assert result2 == result
    
    def test_normalize_text_case_insensitive(self):
        """Normalize to lowercase."""
        engine = MatchingEngine(Mock())
        
        result1 = engine.normalize_text("JavaScript")
        result2 = engine.normalize_text("javascript")
        result3 = engine.normalize_text("JAVASCRIPT")
        
        assert result1 == result2 == result3 == "javascript"
    
    def test_normalize_text_determinism(self):
        """Same input always produces same output."""
        engine = MatchingEngine(Mock())
        
        inputs = [
            "Python",
            "Node.js & React",
            "  Whitespace  ",
            "UPPERCASE",
            "Multiple    Spaces"
        ]
        
        for text in inputs:
            results = [engine.normalize_text(text) for _ in range(5)]
            assert all(r == results[0] for r in results), f"Non-deterministic for: {text}"


class TestLayer1ExactMatching:
    """Tests for Layer 1 exact matching logic."""
    
    @pytest.mark.asyncio
    async def test_layer1_exact_match_skill(self):
        """Exact match found in skills list."""
        engine = MatchingEngine(Mock())
        
        req_text = "Python"
        resume_skills = [
            {"name": "Python", "category": "programming"},
            {"name": "JavaScript", "category": "programming"}
        ]
        resume_blocks = []
        
        result = await engine._layer1_exact_match(req_text, resume_skills, resume_blocks)
        
        assert result is not None
        assert result.match_status == "matched"
        assert result.match_layer == 1
        assert result.match_score == 100.0
        assert "Python" in result.evidence_text
    
    @pytest.mark.asyncio
    async def test_layer1_exact_match_case_insensitive(self):
        """Exact match should be case-insensitive."""
        engine = MatchingEngine(Mock())
        
        req_text = "python"  # lowercase
        resume_skills = [
            {"name": "Python", "category": "programming"}  # uppercase P
        ]
        resume_blocks = []
        
        result = await engine._layer1_exact_match(req_text, resume_skills, resume_blocks)
        
        assert result is not None
        assert result.match_status == "matched"
        assert result.match_score == 100.0
    
    @pytest.mark.asyncio
    async def test_layer1_exact_match_in_block(self):
        """Exact match found in resume block."""
        engine = MatchingEngine(Mock())
        
        req_text = "Docker"
        resume_skills = []
        resume_blocks = [
            {
                "id": "block1",
                "content": {"text": "Deployed applications using Docker containers"}
            }
        ]
        
        result = await engine._layer1_exact_match(req_text, resume_skills, resume_blocks)
        
        assert result is not None
        assert result.match_status == "matched"
        assert result.match_layer == 1
        assert result.match_score == 100.0
        assert result.evidence_block_id == "block1"
    
    @pytest.mark.asyncio
    async def test_layer1_no_match(self):
        """No match returns None."""
        engine = MatchingEngine(Mock())
        
        req_text = "Rust"
        resume_skills = [{"name": "Python"}]
        resume_blocks = [{"id": "b1", "content": {"text": "Built with Python"}}]
        
        result = await engine._layer1_exact_match(req_text, resume_skills, resume_blocks)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_layer1_match_determinism(self):
        """Same inputs produce same results."""
        engine = MatchingEngine(Mock())
        
        req_text = "Python"
        resume_skills = [{"name": "Python"}]
        resume_blocks = []
        
        results = [
            await engine._layer1_exact_match(req_text, resume_skills, resume_blocks)
            for _ in range(3)
        ]
        
        assert all(r is not None for r in results)
        assert all(r.match_status == "matched" for r in results)
        assert all(r.match_score == 100.0 for r in results)


class TestLayer2AliasMatching:
    """Tests for Layer 2 alias matching logic."""
    
    @pytest.mark.asyncio
    async def test_layer2_alias_match_setup(self):
        """Test that layer 2 queries skill_aliases table."""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_or = Mock()
        
        # Setup mock chain
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.or_.return_value = mock_or
        mock_or.execute.return_value = Mock(data=[
            {"canonical_term": "JavaScript", "alias_term": "JS"}
        ])
        
        engine = MatchingEngine(mock_supabase)
        req_text = "JavaScript"
        resume_skills = [{"name": "JS"}]
        resume_blocks = []
        
        result = await engine._layer2_alias_match(req_text, resume_skills, resume_blocks)
        
        # Verify it queried the database
        mock_supabase.table.assert_called_with("skill_aliases")
        assert result is not None
        assert result.match_layer == 2
    
    @pytest.mark.asyncio
    async def test_layer2_no_aliases_found(self):
        """No aliases in database returns None."""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_or = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.or_.return_value = mock_or
        mock_or.execute.return_value = Mock(data=[])  # No aliases
        
        engine = MatchingEngine(mock_supabase)
        req_text = "SomeUnknownTech"
        resume_skills = []
        resume_blocks = []
        
        result = await engine._layer2_alias_match(req_text, resume_skills, resume_blocks)
        
        assert result is None


class TestMatchResultScoring:
    """Tests for match result score assignments."""
    
    def test_match_result_layer1_score(self):
        """Layer 1 matches score 100."""
        result = MatchResult(
            requirement_id="req1",
            requirement_text="Python",
            requirement_type="skill",
            match_status="matched",
            match_layer=1,
            match_score=100.0,
            evidence_text="Python listed"
        )
        
        assert result.match_score == 100.0
        assert result.match_layer == 1
        assert result.match_status == "matched"
    
    def test_match_result_missing_status(self):
        """Missing requirements score 0."""
        result = MatchResult(
            requirement_id="req1",
            requirement_text="Rust",
            requirement_type="skill",
            match_status="missing",
            match_layer=0,
            match_score=0.0,
            recommendation="Add this skill to your resume"
        )
        
        assert result.match_score == 0.0
        assert result.match_layer == 0
        assert result.match_status == "missing"
    
    def test_match_result_similarity_score(self):
        """Layer 3 results include similarity score."""
        result = MatchResult(
            requirement_id="req1",
            requirement_text="Machine Learning",
            requirement_type="skill",
            match_status="matched",
            match_layer=3,
            match_score=90.0,
            similarity_score=0.92
        )
        
        assert result.similarity_score == 0.92
        assert result.match_layer == 3
        assert result.match_score == 90.0


class TestMatchingLogicDeterminism:
    """Tests for overall deterministic behavior."""
    
    def test_normalize_multiple_runs(self):
        """Normalize same text 100 times - should be identical."""
        engine = MatchingEngine(Mock())
        text = "Python, JavaScript & React.js"
        
        results = [engine.normalize_text(text) for _ in range(100)]
        
        assert all(r == results[0] for r in results)
    
    @pytest.mark.asyncio
    async def test_layer1_multiple_runs(self):
        """Layer 1 match same inputs 10 times - should be identical."""
        engine = MatchingEngine(Mock())
        req_text = "Python"
        resume_skills = [{"name": "Python"}]
        resume_blocks = []
        
        results = [
            await engine._layer1_exact_match(req_text, resume_skills, resume_blocks)
            for _ in range(10)
        ]
        
        assert all(r is not None for r in results)
        assert all(r.match_status == results[0].match_status for r in results)
        assert all(r.match_score == results[0].match_score for r in results)
        assert all(r.match_layer == results[0].match_layer for r in results)


class TestGenerateMissingRecommendation:
    """Tests for _generate_missing_recommendation() deterministic function."""
    
    def test_generate_missing_recommendation_skill(self):
        """Generate recommendation for missing skill."""
        engine = MatchingEngine(Mock())
        
        recommendation = engine._generate_missing_recommendation("Python", "skill")
        
        assert "Python" in recommendation
        assert len(recommendation) > 0
        
        # Determinism
        recommendation2 = engine._generate_missing_recommendation("Python", "skill")
        assert recommendation2 == recommendation
    
    def test_generate_missing_recommendation_experience(self):
        """Generate recommendation for missing experience."""
        engine = MatchingEngine(Mock())
        
        recommendation = engine._generate_missing_recommendation(
            "5 years of leadership", 
            "experience"
        )
        
        assert len(recommendation) > 0
        
        # Determinism
        recommendation2 = engine._generate_missing_recommendation(
            "5 years of leadership", 
            "experience"
        )
        assert recommendation2 == recommendation
