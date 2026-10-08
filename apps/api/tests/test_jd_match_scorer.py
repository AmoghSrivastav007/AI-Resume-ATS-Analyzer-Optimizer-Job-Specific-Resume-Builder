"""
Tests for JD Match Scorer (Step 6).
"""

import pytest
from services.jd_match_scorer import JDMatchScorer
from services.matching_engine import MatchResult


@pytest.fixture
def scorer():
    """Create JD match scorer instance."""
    return JDMatchScorer()


@pytest.fixture
def sample_match_results():
    """Sample match results for testing."""
    return [
        MatchResult(
            requirement_id="req1",
            requirement_text="Python",
            requirement_type="required_skill",
            match_status="matched",
            match_layer=1,
            match_score=100.0,
            evidence_text="Python listed in skills"
        ),
        MatchResult(
            requirement_id="req2",
            requirement_text="JavaScript",
            requirement_type="required_skill",
            match_status="partially_matched",
            match_layer=3,
            match_score=70.0,
            similarity_score=0.75
        ),
        MatchResult(
            requirement_id="req3",
            requirement_text="Docker",
            requirement_type="preferred_skill",
            match_status="missing",
            match_layer=0,
            match_score=0.0
        ),
        MatchResult(
            requirement_id="req4",
            requirement_text="Lead development team",
            requirement_type="responsibility",
            match_status="matched",
            match_layer=2,
            match_score=95.0
        )
    ]


class TestMatchRateCalculation:
    """Test match rate calculation."""
    
    def test_all_matched(self, scorer):
        results = [
            MatchResult("r1", "Skill 1", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "Skill 2", "required_skill", "matched", 1, 100.0)
        ]
        rate = scorer._calculate_match_rate(results)
        assert rate == 100.0
    
    def test_all_missing(self, scorer):
        results = [
            MatchResult("r1", "Skill 1", "required_skill", "missing", 0, 0.0),
            MatchResult("r2", "Skill 2", "required_skill", "missing", 0, 0.0)
        ]
        rate = scorer._calculate_match_rate(results)
        assert rate == 0.0
    
    def test_mixed_results(self, scorer):
        results = [
            MatchResult("r1", "Skill 1", "required_skill", "matched", 1, 100.0),  # 100 points
            MatchResult("r2", "Skill 2", "required_skill", "partially_matched", 3, 70.0),  # 70 points
            MatchResult("r3", "Skill 3", "required_skill", "weak_evidence", 4, 40.0),  # 40 points
            MatchResult("r4", "Skill 4", "required_skill", "missing", 0, 0.0)  # 0 points
        ]
        # (100 + 70 + 40 + 0) / 4 = 52.5
        rate = scorer._calculate_match_rate(results)
        assert rate == 52.5
    
    def test_empty_results(self, scorer):
        results = []
        rate = scorer._calculate_match_rate(results)
        assert rate == 100.0  # No requirements = perfect match
    
    def test_not_relevant_excluded(self, scorer):
        results = [
            MatchResult("r1", "Skill 1", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "Skill 2", "required_skill", "not_relevant", 0, 0.0)
        ]
        # not_relevant is excluded, so only 1 result counts
        rate = scorer._calculate_match_rate(results)
        assert rate == 100.0


class TestSkillsAlignment:
    """Test skills alignment score calculation."""
    
    def test_all_required_skills_matched(self, scorer):
        required = [
            MatchResult("r1", "Python", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "Java", "required_skill", "matched", 1, 100.0)
        ]
        score = scorer._calculate_skills_alignment(required, [], [])
        # 100 * 0.70 + 100 * 0.20 + 100 * 0.10 = 100
        assert score == 100.0
    
    def test_some_required_missing(self, scorer):
        required = [
            MatchResult("r1", "Python", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "Java", "required_skill", "missing", 0, 0.0)
        ]
        # Required score: (100 + 0) / 2 = 50
        # Overall: 50 * 0.70 + 100 * 0.20 + 100 * 0.10 = 65
        score = scorer._calculate_skills_alignment(required, [], [])
        assert score == 65.0
    
    def test_no_required_skills(self, scorer):
        # If no required skills, default to 100
        score = scorer._calculate_skills_alignment([], [], [])
        assert score == 100.0


class TestExperienceRelevance:
    """Test experience relevance score calculation."""
    
    def test_all_responsibilities_matched(self, scorer):
        responsibilities = [
            MatchResult("r1", "Lead team", "responsibility", "matched", 1, 100.0)
        ]
        score = scorer._calculate_experience_relevance(responsibilities, [], [], [])
        # 100 * 0.50 + 100 * 0.25 + 100 * 0.15 + 100 * 0.10 = 100
        assert score == 100.0
    
    def test_mixed_experience_match(self, scorer):
        responsibilities = [
            MatchResult("r1", "Lead team", "responsibility", "matched", 1, 100.0),
            MatchResult("r2", "Manage budget", "responsibility", "missing", 0, 0.0)
        ]
        domain = [
            MatchResult("r3", "Healthcare", "domain_knowledge", "partially_matched", 3, 70.0)
        ]
        # Resp: 50, Domain: 70, Competency: 100, Years: 100
        # 50 * 0.50 + 70 * 0.25 + 100 * 0.15 + 100 * 0.10 = 57.5
        score = scorer._calculate_experience_relevance(responsibilities, [], domain, [])
        assert score == 57.5


class TestJDMatchScoreCalculation:
    """Test complete JD Match Score calculation."""
    
    def test_perfect_match(self, scorer):
        results = [
            MatchResult("r1", "Python", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "React", "preferred_skill", "matched", 1, 100.0),
            MatchResult("r3", "Lead team", "responsibility", "matched", 1, 100.0)
        ]
        
        jd_score = scorer.calculate_jd_match_score(results, {})
        
        assert jd_score.overall_score == 100.0
        assert jd_score.keyword_relevance == 100.0
        assert jd_score.skills_alignment == 100.0
        assert jd_score.experience_relevance == 100.0
    
    def test_partial_match(self, scorer, sample_match_results):
        jd_score = scorer.calculate_jd_match_score(sample_match_results, {})
        
        # Should be between 0 and 100
        assert 0.0 <= jd_score.overall_score <= 100.0
        assert 0.0 <= jd_score.keyword_relevance <= 100.0
        assert 0.0 <= jd_score.skills_alignment <= 100.0
        assert 0.0 <= jd_score.experience_relevance <= 100.0
        
        # Overall should be weighted average
        expected_overall = (
            jd_score.keyword_relevance * scorer.KEYWORD_WEIGHT +
            jd_score.skills_alignment * scorer.SKILLS_WEIGHT +
            jd_score.experience_relevance * scorer.EXPERIENCE_WEIGHT
        )
        assert abs(jd_score.overall_score - expected_overall) < 0.01
    
    def test_weights_sum_to_100_percent(self, scorer):
        total_weight = (
            scorer.KEYWORD_WEIGHT +
            scorer.SKILLS_WEIGHT +
            scorer.EXPERIENCE_WEIGHT
        )
        assert abs(total_weight - 1.0) < 0.001  # Should sum to 1.0


class TestExplainabilityTree:
    """Test explainability tree generation."""
    
    def test_explainability_structure(self, scorer, sample_match_results):
        jd_score = scorer.calculate_jd_match_score(sample_match_results, {})
        
        breakdown = jd_score.breakdown
        
        assert "overall_score" in breakdown
        assert "categories" in breakdown
        assert "keyword_relevance" in breakdown["categories"]
        assert "skills_alignment" in breakdown["categories"]
        assert "experience_relevance" in breakdown["categories"]
    
    def test_category_structure(self, scorer, sample_match_results):
        jd_score = scorer.calculate_jd_match_score(sample_match_results, {})
        
        for category_name, category in jd_score.breakdown["categories"].items():
            assert "weight" in category
            assert "score" in category
            assert "contribution" in category
            assert "details" in category
            
            # Weight should match class constants
            if category_name == "keyword_relevance":
                assert category["weight"] == 40
            elif category_name == "skills_alignment":
                assert category["weight"] == 40
            elif category_name == "experience_relevance":
                assert category["weight"] == 20
    
    def test_contribution_calculation(self, scorer, sample_match_results):
        jd_score = scorer.calculate_jd_match_score(sample_match_results, {})
        
        for category in jd_score.breakdown["categories"].values():
            weight = category["weight"] / 100.0
            score = category["score"]
            contribution = category["contribution"]
            
            expected_contribution = round(score * weight, 2)
            assert abs(contribution - expected_contribution) < 0.01


class TestGapAnalysis:
    """Test gap analysis generation."""
    
    def test_gap_analysis_structure(self, scorer, sample_match_results):
        jd_score = scorer.calculate_jd_match_score(sample_match_results, {})
        
        gap = jd_score.gap_analysis
        
        assert "total_gaps" in gap
        assert "critical_gaps" in gap
        assert "gaps" in gap
        assert "critical" in gap["gaps"]
        assert "important" in gap["gaps"]
        assert "needs_improvement" in gap["gaps"]
    
    def test_missing_required_skill_is_critical(self, scorer):
        results = [
            MatchResult("r1", "Python", "required_skill", "missing", 0, 0.0,
                       recommendation="Add Python to skills")
        ]
        
        jd_score = scorer.calculate_jd_match_score(results, {})
        
        assert jd_score.gap_analysis["total_gaps"] == 1
        assert jd_score.gap_analysis["critical_gaps"] == 1
        assert len(jd_score.gap_analysis["gaps"]["critical"]) == 1
    
    def test_missing_preferred_skill_is_important(self, scorer):
        results = [
            MatchResult("r1", "Docker", "preferred_skill", "missing", 0, 0.0,
                       recommendation="Consider adding Docker")
        ]
        
        jd_score = scorer.calculate_jd_match_score(results, {})
        
        assert jd_score.gap_analysis["total_gaps"] == 1
        assert jd_score.gap_analysis["critical_gaps"] == 0
        assert len(jd_score.gap_analysis["gaps"]["important"]) == 1
    
    def test_weak_evidence_needs_improvement(self, scorer):
        results = [
            MatchResult("r1", "Leadership", "competency_signal", "weak_evidence", 4, 40.0,
                       recommendation="Add specific examples")
        ]
        
        jd_score = scorer.calculate_jd_match_score(results, {})
        
        assert jd_score.gap_analysis["total_gaps"] == 0  # Not counted as gap
        assert len(jd_score.gap_analysis["gaps"]["needs_improvement"]) == 1
    
    def test_no_gaps_for_perfect_match(self, scorer):
        results = [
            MatchResult("r1", "Python", "required_skill", "matched", 1, 100.0)
        ]
        
        jd_score = scorer.calculate_jd_match_score(results, {})
        
        assert jd_score.gap_analysis["total_gaps"] == 0
        assert jd_score.gap_analysis["critical_gaps"] == 0
        assert len(jd_score.gap_analysis["gaps"]["critical"]) == 0
        assert len(jd_score.gap_analysis["gaps"]["important"]) == 0


class TestTypeSummary:
    """Test requirement type summary generation."""
    
    def test_type_summary_counts(self, scorer):
        results = [
            MatchResult("r1", "Skill 1", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "Skill 2", "required_skill", "partially_matched", 3, 70.0),
            MatchResult("r3", "Skill 3", "required_skill", "weak_evidence", 4, 40.0),
            MatchResult("r4", "Skill 4", "required_skill", "missing", 0, 0.0)
        ]
        
        summary = scorer._get_type_summary(results, "required_skill")
        
        assert summary["total"] == 4
        assert summary["matched"] == 1
        assert summary["partially_matched"] == 1
        assert summary["weak_evidence"] == 1
        assert summary["missing"] == 1
    
    def test_type_summary_different_type(self, scorer):
        results = [
            MatchResult("r1", "Skill 1", "required_skill", "matched", 1, 100.0),
            MatchResult("r2", "Skill 2", "preferred_skill", "matched", 1, 100.0)
        ]
        
        summary = scorer._get_type_summary(results, "preferred_skill")
        
        assert summary["total"] == 1
        assert summary["matched"] == 1
