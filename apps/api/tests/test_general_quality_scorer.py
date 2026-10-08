import pytest

from models.quality_issue import ContentQualityAnalysis, QualityIssue
from services.scoring.general_quality_scorer import GeneralQualityScorer, SEVERITY_DEDUCTIONS


class TestGeneralQualityScorer:
    def test_perfect_resume_no_issues(self):
        """Test scoring a perfect resume with no issues."""
        scorer = GeneralQualityScorer()
        
        deterministic_issues = []
        content_analysis = ContentQualityAnalysis(
            issues=[],
            overall_content_quality="excellent",
            summary="Perfect resume with strong action verbs and metrics",
            strengths=["Clear metrics", "Strong verbs", "Well structured"],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        assert result.overall_score == 100.0
        assert result.total_issues == 0
        assert result.critical_issues == 0
        assert len(result.category_scores) == 5

    def test_score_with_critical_issues(self):
        """Test that critical issues significantly reduce score."""
        scorer = GeneralQualityScorer()
        
        deterministic_issues = [
            {
                "id": "det1",
                "issue_type": "content",
                "severity": "critical",
                "title": "No Work Experience",
                "description": "Resume has no work experience",
                "metadata": {},
            }
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[
                QualityIssue(
                    issue_category="grammar",
                    problem="Tense inconsistency",
                    severity="high",
                    why_it_matters="Looks unprofessional",
                    current_text="Led team, working on projects",
                    suggested_correction="Led team, worked on projects",
                    expected_benefit="Professional consistency",
                    confidence_level="high",
                )
            ],
            overall_content_quality="needs_improvement",
            summary="Has issues",
            strengths=[],
            weaknesses=["Tense issues"],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        # Critical = 20 points, High = 10 points
        assert result.overall_score < 100.0
        assert result.critical_issues == 1
        assert result.high_issues == 1
        assert result.total_issues == 2

    def test_category_grouping(self):
        """Test that issues are grouped into correct categories."""
        scorer = GeneralQualityScorer()
        
        deterministic_issues = [
            {
                "id": "1",
                "issue_type": "keyword",
                "severity": "medium",
                "title": "Missing keywords",
                "description": "...",
                "metadata": {},
            },
            {
                "id": "2",
                "issue_type": "formatting",
                "severity": "low",
                "title": "Inconsistent formatting",
                "description": "...",
                "metadata": {},
            },
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[
                QualityIssue(
                    issue_category="content",
                    problem="Weak verb",
                    severity="medium",
                    why_it_matters="...",
                    current_text="Worked on",
                    suggested_correction="Architected",
                    expected_benefit="...",
                    confidence_level="high",
                )
            ],
            overall_content_quality="good",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        # Check that we have 3 issues distributed across categories
        assert result.total_issues == 3
        
        # Structure should have the keyword issue
        structure_score = next(cs for cs in result.category_scores if cs.category == "structure")
        assert len(structure_score.deductions) >= 1
        
        # Content Quality should have the weak verb
        content_score = next(cs for cs in result.category_scores if cs.category == "content_quality")
        assert len(content_score.deductions) >= 1
        
        # Formatting should have the formatting issue
        formatting_score = next(cs for cs in result.category_scores if cs.category == "formatting")
        assert len(formatting_score.deductions) >= 1

    def test_score_breakdown_structure(self):
        """Test that score breakdown has correct structure."""
        scorer = GeneralQualityScorer()
        
        deterministic_issues = [
            {
                "id": "test1",
                "issue_type": "content",
                "severity": "medium",
                "title": "Test Issue",
                "description": "Test description",
                "metadata": {"suggested_correction": "Fix it this way"},
            }
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[],
            overall_content_quality="good",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        breakdown = result.score_breakdown
        
        assert "overall_score" in breakdown
        assert "categories" in breakdown
        assert isinstance(breakdown["categories"], dict)
        
        # Check that all 5 categories exist
        assert len(breakdown["categories"]) == 5
        
        for cat_name, cat_data in breakdown["categories"].items():
            assert "raw_score" in cat_data
            assert "weighted_score" in cat_data
            assert "max_score" in cat_data
            assert "weight_percentage" in cat_data
            assert "deductions" in cat_data
            assert isinstance(cat_data["deductions"], list)

    def test_deduction_points_calculation(self):
        """Test that deduction points match severity levels."""
        scorer = GeneralQualityScorer()
        
        # One issue of each severity
        deterministic_issues = [
            {"id": "1", "issue_type": "content", "severity": "critical", "title": "Critical", "description": "...", "metadata": {}},
            {"id": "2", "issue_type": "content", "severity": "high", "title": "High", "description": "...", "metadata": {}},
            {"id": "3", "issue_type": "content", "severity": "medium", "title": "Medium", "description": "...", "metadata": {}},
            {"id": "4", "issue_type": "content", "severity": "low", "title": "Low", "description": "...", "metadata": {}},
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[],
            overall_content_quality="needs_improvement",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        # Total deductions = 20 + 10 + 5 + 2 = 37 points from content_quality category
        # Content quality has weight of 18.2%, so raw score in that category = 100 - 37 = 63
        content_score = next(cs for cs in result.category_scores if cs.category == "content_quality")
        
        # Verify deductions sum correctly
        total_deducted = sum(ded["points"] for ded in content_score.deductions)
        assert total_deducted == 20 + 10 + 5 + 2

    def test_category_weights_sum_to_100(self):
        """Test that all category weights sum to 100."""
        from services.scoring.general_quality_scorer import WEIGHTS
        
        total_weight = sum(WEIGHTS.values())
        assert abs(total_weight - 100.0) < 0.1  # Allow tiny floating point error

    def test_weighted_scores_sum_to_overall(self):
        """Test that weighted scores sum to overall score."""
        scorer = GeneralQualityScorer()
        
        deterministic_issues = [
            {
                "id": "1",
                "issue_type": "content",
                "severity": "medium",
                "title": "Test",
                "description": "...",
                "metadata": {},
            }
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[],
            overall_content_quality="good",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        # Sum of weighted scores should equal overall score
        weighted_sum = sum(cs.weighted_score for cs in result.category_scores)
        assert abs(weighted_sum - result.overall_score) < 0.01

    def test_raw_score_floors_at_zero(self):
        """Test that raw scores cannot go below zero."""
        scorer = GeneralQualityScorer()
        
        # Create enough critical issues to exceed 100 points
        deterministic_issues = [
            {
                "id": f"crit{i}",
                "issue_type": "content",
                "severity": "critical",
                "title": f"Critical {i}",
                "description": "...",
                "metadata": {},
            }
            for i in range(10)  # 10 * 20 = 200 points
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[],
            overall_content_quality="poor",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        # All category raw scores should be >= 0
        for cat_score in result.category_scores:
            assert cat_score.raw_score >= 0.0

    def test_explainability_includes_recommendations(self):
        """Test that explainability tree includes recommendations."""
        scorer = GeneralQualityScorer()
        
        deterministic_issues = [
            {
                "id": "test1",
                "issue_type": "content",
                "severity": "high",
                "title": "Missing metrics",
                "description": "No quantifiable achievements",
                "metadata": {"suggested_correction": "Add numbers: '50% improvement', '10+ projects'"},
            }
        ]
        
        content_analysis = ContentQualityAnalysis(
            issues=[],
            overall_content_quality="needs_improvement",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate(deterministic_issues, content_analysis)
        
        breakdown = result.score_breakdown
        
        # Find the deduction in the breakdown
        for cat_data in breakdown["categories"].values():
            for deduction in cat_data["deductions"]:
                if deduction["issue_id"] == "test1":
                    assert "recommendation" in deduction
                    assert "Add numbers" in deduction["recommendation"]
                    break

    def test_llm_issue_metadata_preserved(self):
        """Test that LLM issue metadata is preserved."""
        scorer = GeneralQualityScorer()
        
        content_analysis = ContentQualityAnalysis(
            issues=[
                QualityIssue(
                    issue_category="content",
                    problem="Weak action verb",
                    severity="medium",
                    why_it_matters="Generic verbs don't stand out",
                    current_text="Worked on backend systems",
                    suggested_correction="Architected scalable backend systems",
                    expected_benefit="Shows technical leadership",
                    confidence_level="high",
                    location="Experience → Senior Engineer",
                )
            ],
            overall_content_quality="good",
            summary="...",
            strengths=[],
            weaknesses=[],
        )
        
        result = scorer.calculate([], content_analysis)
        
        # Find the LLM issue in breakdown
        breakdown = result.score_breakdown
        content_cat = breakdown["categories"]["content_quality"]
        
        assert len(content_cat["deductions"]) == 1
        deduction = content_cat["deductions"][0]
        
        assert deduction["recommendation"] == "Architected scalable backend systems"
        assert "Weak action verb" in deduction["reason"]
