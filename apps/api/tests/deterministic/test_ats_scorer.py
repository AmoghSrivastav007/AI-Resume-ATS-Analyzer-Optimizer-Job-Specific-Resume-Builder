"""
Tests for Step 4: ATS Scoring Math (Deterministic scoring logic).

Tests pure scoring functions with zero variance.
Same resume_data -> Same score every time.
"""

import pytest
from services.scoring.ats_scorer import ATSScorer, ATSScoreResult


class TestContactScoring:
    """Tests for _score_contact() deterministic scoring."""
    
    def test_score_contact_complete(self):
        """Complete contact information should score 20 points."""
        scorer = ATSScorer()
        contact = {
            "email": "john@example.com",
            "phone": "+1-555-1234",
            "full_name": "John Doe",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/johndoe"
        }
        issues = []
        
        score = scorer._score_contact(contact, issues)
        
        assert score == 20.0
        assert len(issues) == 0
        
        # Determinism check
        issues2 = []
        score2 = scorer._score_contact(contact, issues2)
        assert score2 == score
    
    def test_score_contact_missing_email(self):
        """Missing email should be high severity."""
        scorer = ATSScorer()
        contact = {
            "phone": "+1-555-1234",
            "full_name": "John Doe"
        }
        issues = []
        
        score = scorer._score_contact(contact, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "high"
        assert "email" in issues[0]["metadata"]["missing_fields"]
        
        # Determinism
        issues2 = []
        score2 = scorer._score_contact(contact, issues2)
        assert score2 == score
        assert len(issues2) == 1
    
    def test_score_contact_missing_phone(self):
        """Missing phone should be medium severity."""
        scorer = ATSScorer()
        contact = {
            "email": "john@example.com",
            "full_name": "John Doe"
        }
        issues = []
        
        score = scorer._score_contact(contact, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "medium"
        
        # Determinism
        issues2 = []
        score2 = scorer._score_contact(contact, issues2)
        assert score2 == score


class TestSectionScoring:
    """Tests for _score_sections() deterministic scoring."""
    
    def test_score_sections_all_present(self):
        """All required sections should score 20 points."""
        scorer = ATSScorer()
        sections = [
            {"section_type": "experience", "id": "exp1"},
            {"section_type": "education", "id": "edu1"},
            {"section_type": "skills", "id": "skills1"},
            {"section_type": "summary", "id": "sum1"}
        ]
        issues = []
        
        score = scorer._score_sections(sections, issues)
        
        assert score == 20.0
        assert len(issues) == 0
        
        # Determinism
        issues2 = []
        score2 = scorer._score_sections(sections, issues2)
        assert score2 == score
    
    def test_score_sections_missing_experience(self):
        """Missing experience should be critical severity."""
        scorer = ATSScorer()
        sections = [
            {"section_type": "education", "id": "edu1"},
            {"section_type": "skills", "id": "skills1"}
        ]
        issues = []
        
        score = scorer._score_sections(sections, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "critical"
        assert "experience" in issues[0]["metadata"]["missing_sections"]
        
        # Determinism
        issues2 = []
        score2 = scorer._score_sections(sections, issues2)
        assert score2 == score
    
    def test_score_sections_bonus_optional(self):
        """Optional sections should provide bonus points."""
        scorer = ATSScorer()
        sections = [
            {"section_type": "experience", "id": "exp1"},
            {"section_type": "education", "id": "edu1"},
            {"section_type": "skills", "id": "skills1"},
            {"section_type": "projects", "id": "proj1"},  # Optional bonus
            {"section_type": "certifications", "id": "cert1"}  # Optional bonus
        ]
        issues = []
        
        score = scorer._score_sections(sections, issues)
        
        assert score == 20.0  # Max capped at 20
        assert len(issues) == 0
        
        # Determinism
        issues2 = []
        score2 = scorer._score_sections(sections, issues2)
        assert score2 == score


class TestDensityScoring:
    """Tests for _score_density() deterministic scoring."""
    
    def test_score_density_adequate(self):
        """Adequate content density should score 20 points."""
        scorer = ATSScorer()
        sections = [{"id": "exp1", "section_type": "experience"}]
        blocks = [
            {"id": f"b{i}", "section_id": "exp1", "block_type": "bullet", "content": {"text": f"Bullet {i}"}}
            for i in range(15)  # 15 blocks, 5 bullets
        ]
        issues = []
        
        score = scorer._score_density(blocks, sections, issues)
        
        assert score == 20.0
        assert len(issues) == 0
        
        # Determinism
        issues2 = []
        score2 = scorer._score_density(blocks, sections, issues2)
        assert score2 == score
    
    def test_score_density_sparse(self):
        """Sparse content should trigger medium severity issues."""
        scorer = ATSScorer()
        sections = [{"id": "exp1", "section_type": "experience"}]
        blocks = [
            {"id": "b1", "section_id": "exp1", "block_type": "paragraph", "content": {"text": "Short"}},
            {"id": "b2", "section_id": "exp1", "block_type": "bullet", "content": {"text": "Bullet"}}
        ]  # Only 2 blocks, 1 bullet
        issues = []
        
        score = scorer._score_density(blocks, sections, issues)
        
        assert score < 20.0
        # Should trigger 2 issues: sparse content + thin experience section
        assert len(issues) == 2
        assert all(issue["severity"] == "medium" for issue in issues)
        issue_titles = [issue["title"] for issue in issues]
        assert "Sparse Content" in issue_titles
        assert "Thin Sections" in issue_titles
        
        # Determinism
        issues2 = []
        score2 = scorer._score_density(blocks, sections, issues2)
        assert score2 == score
        assert len(issues2) == 2
    
    def test_score_density_no_blocks(self):
        """No blocks should be critical severity."""
        scorer = ATSScorer()
        sections = []
        blocks = []
        issues = []
        
        score = scorer._score_density(blocks, sections, issues)
        
        assert score == 0.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "critical"
        
        # Determinism
        issues2 = []
        score2 = scorer._score_density(blocks, sections, issues2)
        assert score2 == score


class TestExperienceScoring:
    """Tests for _score_experience() deterministic scoring."""
    
    def test_score_experience_quality(self):
        """High quality experience should score 20 points."""
        scorer = ATSScorer()
        work_exp = [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01",
                "end_date": "2023-12",
                "bullets": [
                    "Built feature with 50% improvement",
                    "Led team of 5 developers",
                    "Reduced costs by 30%"
                ]
            }
        ]
        issues = []
        
        score = scorer._score_experience(work_exp, issues)
        
        assert score == 20.0
        assert len(issues) == 0
        
        # Determinism
        issues2 = []
        score2 = scorer._score_experience(work_exp, issues2)
        assert score2 == score
    
    def test_score_experience_missing_dates(self):
        """Missing dates should reduce score."""
        scorer = ATSScorer()
        work_exp = [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                # Missing start_date
                "bullets": ["Did something", "Did something else"]
            }
        ]
        issues = []
        
        score = scorer._score_experience(work_exp, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert "missing start date" in issues[0]["metadata"]["problems"][0]
        
        # Determinism
        issues2 = []
        score2 = scorer._score_experience(work_exp, issues2)
        assert score2 == score
    
    def test_score_experience_no_metrics(self):
        """No quantifiable metrics should reduce score."""
        scorer = ATSScorer()
        work_exp = [
            {
                "title": "Developer",
                "company": "Company",
                "start_date": "2020-01",
                "bullets": ["Wrote code", "Fixed bugs"]  # No numbers
            }
        ]
        issues = []
        
        score = scorer._score_experience(work_exp, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert "no quantifiable achievements" in issues[0]["metadata"]["problems"][0]
        
        # Determinism
        issues2 = []
        score2 = scorer._score_experience(work_exp, issues2)
        assert score2 == score
    
    def test_score_experience_none(self):
        """No experience should be critical."""
        scorer = ATSScorer()
        work_exp = []
        issues = []
        
        score = scorer._score_experience(work_exp, issues)
        
        assert score == 0.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "critical"
        
        # Determinism
        issues2 = []
        score2 = scorer._score_experience(work_exp, issues2)
        assert score2 == score


class TestSkillsScoring:
    """Tests for _score_skills() deterministic scoring."""
    
    def test_score_skills_balanced(self):
        """5-50 skills should score well."""
        scorer = ATSScorer()
        skills = [{"name": f"Skill {i}", "category": "technical"} for i in range(10)]
        issues = []
        
        score = scorer._score_skills(skills, issues)
        
        assert score == 20.0
        assert len(issues) == 0
        
        # Determinism
        issues2 = []
        score2 = scorer._score_skills(skills, issues2)
        assert score2 == score
    
    def test_score_skills_too_few(self):
        """Less than 5 skills should be medium severity."""
        scorer = ATSScorer()
        skills = [{"name": f"Skill {i}"} for i in range(3)]  # Only 3
        issues = []
        
        score = scorer._score_skills(skills, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "medium"
        assert "Limited Skills" in issues[0]["title"]
        
        # Determinism
        issues2 = []
        score2 = scorer._score_skills(skills, issues2)
        assert score2 == score
    
    def test_score_skills_too_many(self):
        """More than 50 skills should be low severity."""
        scorer = ATSScorer()
        skills = [{"name": f"Skill {i}"} for i in range(60)]  # 60 skills
        issues = []
        
        score = scorer._score_skills(skills, issues)
        
        assert score < 20.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "low"
        assert "Too Many Skills" in issues[0]["title"]
        
        # Determinism
        issues2 = []
        score2 = scorer._score_skills(skills, issues2)
        assert score2 == score
    
    def test_score_skills_none(self):
        """No skills should be high severity."""
        scorer = ATSScorer()
        skills = []
        issues = []
        
        score = scorer._score_skills(skills, issues)
        
        assert score == 0.0
        assert len(issues) == 1
        assert issues[0]["severity"] == "high"
        
        # Determinism
        issues2 = []
        score2 = scorer._score_skills(skills, issues2)
        assert score2 == score


class TestOverallScoring:
    """Tests for overall ATS scoring."""
    
    def test_score_perfect_resume(self):
        """Perfect resume should score close to 100."""
        scorer = ATSScorer()
        resume_data = {
            "extraction": {
                "contact": {
                    "email": "john@example.com",
                    "phone": "+1-555-1234",
                    "full_name": "John Doe",
                    "location": "SF",
                    "linkedin": "linkedin.com/in/john"
                },
                "work_experience": [
                    {
                        "title": "Senior Engineer",
                        "company": "Tech Co",
                        "start_date": "2020-01",
                        "bullets": ["Improved performance by 50%", "Led team of 8"]
                    }
                ],
                "skills": [{"name": f"Skill {i}"} for i in range(15)]
            },
            "sections": [
                {"section_type": "experience", "id": "exp"},
                {"section_type": "education", "id": "edu"},
                {"section_type": "skills", "id": "sk"}
            ],
            "blocks": [
                {"id": f"b{i}", "section_id": "exp", "block_type": "bullet", "content": {"text": f"Text {i}"}}
                for i in range(12)
            ]
        }
        
        result = scorer.score(resume_data)
        
        assert result.overall_score == 100.0
        assert len(result.issues) == 0
        assert result.summary["critical_issues"] == 0
        assert result.summary["high_issues"] == 0
        
        # Determinism check
        result2 = scorer.score(resume_data)
        assert result2.overall_score == result.overall_score
        assert len(result2.issues) == len(result.issues)
    
    def test_score_determinism(self):
        """Same resume_data should produce same score every time."""
        scorer = ATSScorer()
        resume_data = {
            "extraction": {
                "contact": {"email": "test@test.com", "phone": "123", "full_name": "Test"},
                "work_experience": [{"title": "Dev", "company": "Co", "start_date": "2020", "bullets": ["Did stuff with 100% success"]}],
                "skills": [{"name": f"Skill {i}"} for i in range(8)]
            },
            "sections": [
                {"section_type": "experience", "id": "1"},
                {"section_type": "education", "id": "2"},
                {"section_type": "skills", "id": "3"}
            ],
            "blocks": [{"id": str(i), "section_id": "1", "block_type": "bullet", "content": {"text": "text"}} for i in range(10)]
        }
        
        # Run multiple times
        results = [scorer.score(resume_data) for _ in range(5)]
        
        # All scores should be identical
        scores = [r.overall_score for r in results]
        assert all(s == scores[0] for s in scores)
        
        # All issue counts should be identical
        issue_counts = [len(r.issues) for r in results]
        assert all(c == issue_counts[0] for c in issue_counts)
