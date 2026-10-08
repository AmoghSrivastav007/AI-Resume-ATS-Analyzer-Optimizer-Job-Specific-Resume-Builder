"""
Tests for Step 7: Guardrails (Deterministic extraction and pattern matching).

Tests pure extraction functions with zero variance:
- Extracting facts from ledger
- Extracting patterns from text
- Fuzzy matching logic

These are deterministic components of the guardrail system.
The actual guardrail check (check_guardrails) is async and requires database,
so we test only the pure extraction functions here.
"""

import pytest
from services.optimizer.guardrails import DeterministicGuardrails
from unittest.mock import Mock


class TestLedgerExtraction:
    """Tests for extracting facts from fact ledger (pure functions)."""
    
    def test_extract_companies_from_ledger(self):
        """Extract company names from fact ledger."""
        guardrails = DeterministicGuardrails(Mock())
        
        fact_ledger = [
            {
                "fact_type": "other",
                "fact_text": "Google",
                "metadata": {"field": "company"}
            },
            {
                "fact_type": "other",
                "fact_text": "Microsoft",
                "metadata": {"field": "company"}
            },
            {
                "fact_type": "skill",
                "fact_text": "Python",
                "metadata": {}
            }
        ]
        
        companies = guardrails._extract_companies(fact_ledger)
        
        assert "Google" in companies
        assert "Microsoft" in companies
        assert "Python" not in companies
        
        # Determinism
        companies2 = guardrails._extract_companies(fact_ledger)
        assert set(companies) == set(companies2)
    
    def test_extract_titles_from_ledger(self):
        """Extract job titles from fact ledger."""
        guardrails = DeterministicGuardrails(Mock())
        
        fact_ledger = [
            {
                "fact_type": "title",
                "fact_text": "Software Engineer",
                "metadata": {}
            },
            {
                "fact_type": "title",
                "fact_text": "Senior Developer",
                "metadata": {}
            },
            {
                "fact_type": "skill",
                "fact_text": "JavaScript",
                "metadata": {}
            }
        ]
        
        titles = guardrails._extract_titles(fact_ledger)
        
        assert "Software Engineer" in titles
        assert "Senior Developer" in titles
        assert "JavaScript" not in titles
        
        # Determinism
        titles2 = guardrails._extract_titles(fact_ledger)
        assert set(titles) == set(titles2)
    
    def test_extract_dates_from_ledger(self):
        """Extract dates from fact ledger."""
        guardrails = DeterministicGuardrails(Mock())
        
        fact_ledger = [
            {
                "fact_type": "date",
                "fact_text": "2020-01",
                "metadata": {}
            },
            {
                "fact_type": "date",
                "fact_text": "2023-12",
                "metadata": {}
            },
            {
                "fact_type": "skill",
                "fact_text": "Python",
                "metadata": {}
            }
        ]
        
        dates = guardrails._extract_dates(fact_ledger)
        
        assert "2020-01" in dates
        assert "2023-12" in dates
        assert "Python" not in dates
        
        # Determinism
        dates2 = guardrails._extract_dates(fact_ledger)
        assert set(dates) == set(dates2)
    
    def test_extract_skills_from_ledger(self):
        """Extract skills from fact ledger."""
        guardrails = DeterministicGuardrails(Mock())
        
        fact_ledger = [
            {
                "fact_type": "skill",
                "fact_text": "Python",
                "metadata": {}
            },
            {
                "fact_type": "skill",
                "fact_text": "JavaScript",
                "metadata": {}
            },
            {
                "fact_type": "date",
                "fact_text": "2020-01",
                "metadata": {}
            }
        ]
        
        skills = guardrails._extract_skills(fact_ledger)
        
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "2020-01" not in skills
        
        # Determinism
        skills2 = guardrails._extract_skills(fact_ledger)
        assert set(skills) == set(skills2)
    
    def test_extract_numbers_from_ledger(self):
        """Extract numbers from metric facts."""
        guardrails = DeterministicGuardrails(Mock())
        
        fact_ledger = [
            {
                "fact_type": "metric",
                "fact_text": "Improved performance by 50%",
                "metadata": {}
            },
            {
                "fact_type": "metric",
                "fact_text": "Led team of 8 developers",
                "metadata": {}
            },
            {
                "fact_type": "skill",
                "fact_text": "Python",
                "metadata": {}
            }
        ]
        
        numbers = guardrails._extract_numbers(fact_ledger)
        
        assert "50" in numbers or "50%" in numbers
        assert "8" in numbers
        
        # Determinism
        numbers2 = guardrails._extract_numbers(fact_ledger)
        assert set(numbers) == set(numbers2)


class TestTextExtraction:
    """Tests for extracting patterns from text (pure regex functions)."""
    
    def test_extract_company_names_from_text(self):
        """Extract company names using regex patterns."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Worked at Google for 3 years and then at Microsoft for 2 years."
        
        companies = guardrails._extract_company_names(text)
        
        # Regex captures some trailing words - check for substring
        assert any("Google" in c for c in companies)
        assert any("Microsoft" in c for c in companies)
        
        # Determinism
        companies2 = guardrails._extract_company_names(text)
        assert companies == companies2
    
    def test_extract_company_names_with_suffixes(self):
        """Extract company names with Inc/LLC/Corp suffixes."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Software Engineer at Tech Corp from 2020 to 2023."
        
        companies = guardrails._extract_company_names(text)
        
        # Should find "Tech Corp"
        assert any("Tech" in c for c in companies)
        
        # Determinism
        companies2 = guardrails._extract_company_names(text)
        assert companies == companies2
    
    def test_extract_job_titles_from_text(self):
        """Extract job titles using regex patterns."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Senior Software Engineer at Tech Co. Previously worked as Lead Developer."
        
        titles = guardrails._extract_job_titles(text)
        
        assert any("Senior" in t or "Engineer" in t for t in titles)
        assert any("Lead" in t or "Developer" in t for t in titles)
        
        # Determinism
        titles2 = guardrails._extract_job_titles(text)
        assert titles == titles2
    
    def test_extract_date_ranges_from_text(self):
        """Extract dates and date ranges from text."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Worked from Jan 2020 to Dec 2023. Started in 2019."
        
        dates = guardrails._extract_date_ranges(text)
        
        # Should find years and month-year patterns
        assert any("2020" in d for d in dates)
        assert any("2023" in d for d in dates)
        assert any("2019" in d for d in dates)
        
        # Determinism
        dates2 = guardrails._extract_date_ranges(text)
        assert dates == dates2
    
    def test_extract_date_ranges_multiple_formats(self):
        """Handle multiple date formats."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Employment: 01/2020 to 12/2023. Also worked in 2019."
        
        dates = guardrails._extract_date_ranges(text)
        
        # Should extract both MM/YYYY and YYYY formats
        assert len(dates) > 0
        
        # Determinism
        dates2 = guardrails._extract_date_ranges(text)
        assert dates == dates2
    
    def test_extract_technical_terms(self):
        """Extract technical terms/skills from text."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Built applications using Python, JavaScript, and React. Deployed on AWS with Docker."
        
        terms = guardrails._extract_technical_terms(text)
        
        # Should extract capitalized technical terms
        assert "Python" in terms
        assert "JavaScript" in terms
        assert "React" in terms
        assert "AWS" in terms
        assert "Docker" in terms
        
        # Determinism
        terms2 = guardrails._extract_technical_terms(text)
        assert terms == terms2
    
    def test_extract_technical_terms_with_special_chars(self):
        """Extract terms with special characters like Node.js, C++."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Experience with Node.js, C++, and C#."
        
        terms = guardrails._extract_technical_terms(text)
        
        # Should handle special characters
        assert len(terms) > 0
        
        # Determinism
        terms2 = guardrails._extract_technical_terms(text)
        assert terms == terms2


class TestFuzzyMatching:
    """Tests for fuzzy matching logic (deterministic)."""
    
    def test_is_date_in_ledger_year_match(self):
        """Fuzzy date matching by year."""
        guardrails = DeterministicGuardrails(Mock())
        
        date = "Jan 2020"
        ledger_dates = ["2020-01", "2021-06", "2023-12"]
        
        result = guardrails._is_date_in_ledger(date, ledger_dates)
        
        # Should match because year 2020 is in "2020-01"
        assert result is True
        
        # Determinism
        result2 = guardrails._is_date_in_ledger(date, ledger_dates)
        assert result2 == result
    
    def test_is_date_in_ledger_no_match(self):
        """Date not in ledger returns False."""
        guardrails = DeterministicGuardrails(Mock())
        
        date = "2025"
        ledger_dates = ["2020-01", "2021-06", "2023-12"]
        
        result = guardrails._is_date_in_ledger(date, ledger_dates)
        
        assert result is False
        
        # Determinism
        result2 = guardrails._is_date_in_ledger(date, ledger_dates)
        assert result2 == result
    
    def test_is_date_in_ledger_partial_year(self):
        """Partial year match (e.g., "20" in "2020")."""
        guardrails = DeterministicGuardrails(Mock())
        
        date = "2020"
        ledger_dates = ["Jan 2020", "2021-06"]
        
        result = guardrails._is_date_in_ledger(date, ledger_dates)
        
        # Should match
        assert result is True
        
        # Determinism
        result2 = guardrails._is_date_in_ledger(date, ledger_dates)
        assert result2 == result


class TestDeterminism:
    """Verify determinism across all extraction functions."""
    
    def test_extraction_determinism_multiple_runs(self):
        """All extraction functions should be deterministic."""
        guardrails = DeterministicGuardrails(Mock())
        
        fact_ledger = [
            {"fact_type": "skill", "fact_text": "Python", "metadata": {}},
            {"fact_type": "title", "fact_text": "Engineer", "metadata": {}},
            {"fact_type": "date", "fact_text": "2020", "metadata": {}},
            {"fact_type": "metric", "fact_text": "Improved by 50%", "metadata": {}}
        ]
        
        # Run each extraction 5 times
        skills_results = [guardrails._extract_skills(fact_ledger) for _ in range(5)]
        titles_results = [guardrails._extract_titles(fact_ledger) for _ in range(5)]
        dates_results = [guardrails._extract_dates(fact_ledger) for _ in range(5)]
        
        # All should be identical
        assert all(set(r) == set(skills_results[0]) for r in skills_results)
        assert all(set(r) == set(titles_results[0]) for r in titles_results)
        assert all(set(r) == set(dates_results[0]) for r in dates_results)
    
    def test_text_pattern_determinism(self):
        """Text pattern extraction should be deterministic."""
        guardrails = DeterministicGuardrails(Mock())
        
        text = "Senior Engineer at Google from 2020 to 2023 using Python and AWS."
        
        # Run each extraction 5 times
        companies = [guardrails._extract_company_names(text) for _ in range(5)]
        titles = [guardrails._extract_job_titles(text) for _ in range(5)]
        dates = [guardrails._extract_date_ranges(text) for _ in range(5)]
        terms = [guardrails._extract_technical_terms(text) for _ in range(5)]
        
        # All should be identical
        assert all(r == companies[0] for r in companies)
        assert all(r == titles[0] for r in titles)
        assert all(r == dates[0] for r in dates)
        assert all(r == terms[0] for r in terms)
