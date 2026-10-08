import pytest

from services.scoring.ats_scorer import ATSScorer
from services.scoring.jd_matcher import JDMatcher


class TestATSScorer:
    def test_score_complete_resume(self):
        """Test scoring a well-formed resume."""
        scorer = ATSScorer()
        
        resume_data = {
            "extraction": {
                "contact": {
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-1234",
                    "location": "San Francisco, CA",
                },
                "summary": "Experienced software engineer",
                "work_experience": [
                    {
                        "title": "Senior Engineer",
                        "company": "TechCorp",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "bullets": [
                            "Led team of 5 engineers",
                            "Improved performance by 50%",
                            "Shipped 10+ features",
                        ],
                    }
                ],
                "education": [
                    {
                        "degree": "BS Computer Science",
                        "institution": "MIT",
                    }
                ],
                "skills": [
                    {"name": "Python"},
                    {"name": "JavaScript"},
                    {"name": "AWS"},
                    {"name": "Docker"},
                    {"name": "Kubernetes"},
                ],
                "certifications": [],
                "projects": [],
                "languages": [],
            },
            "sections": [
                {"id": "1", "section_type": "contact"},
                {"id": "2", "section_type": "summary"},
                {"id": "3", "section_type": "experience"},
                {"id": "4", "section_type": "education"},
                {"id": "5", "section_type": "skills"},
            ],
            "blocks": [
                {"id": "b1", "section_id": "3", "block_type": "heading"},
                {"id": "b2", "section_id": "3", "block_type": "bullet"},
                {"id": "b3", "section_id": "3", "block_type": "bullet"},
                {"id": "b4", "section_id": "3", "block_type": "bullet"},
            ],
        }
        
        result = scorer.score(resume_data)
        
        assert result.overall_score > 0
        assert result.overall_score <= 100
        assert isinstance(result.summary, dict)
        assert isinstance(result.issues, list)
        assert "overall_score" in result.summary
        assert "category_scores" in result.summary

    def test_score_missing_contact(self):
        """Test scoring resume with missing contact info."""
        scorer = ATSScorer()
        
        resume_data = {
            "extraction": {
                "contact": {},  # Empty contact
                "work_experience": [],
                "education": [],
                "skills": [],
            },
            "sections": [],
            "blocks": [],
        }
        
        result = scorer.score(resume_data)
        
        # Should have issues about missing contact
        contact_issues = [i for i in result.issues if "contact" in i["title"].lower()]
        assert len(contact_issues) > 0
        assert result.overall_score < 50

    def test_score_missing_sections(self):
        """Test scoring resume with missing critical sections."""
        scorer = ATSScorer()
        
        resume_data = {
            "extraction": {
                "contact": {"full_name": "John", "email": "john@example.com"},
                "work_experience": [],  # No experience
                "education": [],
                "skills": [],
            },
            "sections": [{"id": "1", "section_type": "contact"}],
            "blocks": [],
        }
        
        result = scorer.score(resume_data)
        
        # Should have critical issue about missing experience
        critical_issues = [i for i in result.issues if i["severity"] == "critical"]
        assert len(critical_issues) > 0


class TestJDMatcher:
    def test_match_with_matching_skills(self):
        """Test matching resume against JD with overlapping skills."""
        matcher = JDMatcher()
        
        resume_data = {
            "extraction": {
                "skills": [
                    {"name": "Python"},
                    {"name": "Django"},
                    {"name": "PostgreSQL"},
                ],
                "work_experience": [
                    {
                        "title": "Backend Engineer",
                        "company": "TechCorp",
                        "bullets": ["Built REST APIs with Python and Django"],
                    }
                ],
                "education": [],
                "certifications": [],
                "projects": [],
            },
        }
        
        jd_requirements = [
            {
                "id": "req1",
                "requirement_text": "Python programming",
                "requirement_type": "required",
            },
            {
                "id": "req2",
                "requirement_text": "Django framework experience",
                "requirement_type": "required",
            },
            {
                "id": "req3",
                "requirement_text": "Kubernetes expertise",
                "requirement_type": "preferred",
            },
        ]
        
        result = matcher.match(resume_data, jd_requirements)
        
        assert result.overall_score > 0
        assert len(result.matches) == 3
        
        # Should match Python and Django
        python_match = next(m for m in result.matches if "Python" in m.requirement_text)
        assert python_match.match_status in ["matched", "partial"]
        
        django_match = next(m for m in result.matches if "Django" in m.requirement_text)
        assert django_match.match_status in ["matched", "partial"]
        
        # Should miss Kubernetes
        k8s_match = next(m for m in result.matches if "Kubernetes" in m.requirement_text)
        assert k8s_match.match_status == "missing"

    def test_match_empty_resume(self):
        """Test matching empty resume against JD."""
        matcher = JDMatcher()
        
        resume_data = {
            "extraction": {
                "skills": [],
                "work_experience": [],
                "education": [],
                "certifications": [],
                "projects": [],
            },
        }
        
        jd_requirements = [
            {
                "id": "req1",
                "requirement_text": "Python programming",
                "requirement_type": "required",
            },
        ]
        
        result = matcher.match(resume_data, jd_requirements)
        
        assert result.overall_score < 30
        assert all(m.match_status == "missing" for m in result.matches)

    def test_calculate_weighted_score(self):
        """Test that required requirements are weighted higher than preferred."""
        matcher = JDMatcher()
        
        resume_data = {
            "extraction": {
                "skills": [{"name": "Python"}],
                "work_experience": [],
                "education": [],
                "certifications": [],
                "projects": [],
            },
        }
        
        # One required, one preferred
        jd_requirements = [
            {
                "id": "req1",
                "requirement_text": "Python",
                "requirement_type": "required",
            },
            {
                "id": "req2",
                "requirement_text": "Go",
                "requirement_type": "preferred",
            },
        ]
        
        result = matcher.match(resume_data, jd_requirements)
        
        # Should have higher score because we match the required one
        assert result.overall_score > 40
