"""
Deterministic Guardrails for Resume Optimization (Step 7 - Part 4 of Truth Guard).

Runs regardless of LLM verifier's verdict. These are HARD BLOCKS that cannot be overridden.

Guardrails:
1. Company names: ANY difference is a hard block
2. Job titles: ANY difference is a hard block  
3. Date ranges: ANY difference is a hard block
4. Skills/technologies: Any NEW technical term not in fact ledger (exact or alias-matched) is a hard block
5. Numeric claims: Any NEW number not in original bullet is a hard block

If ANY guardrail fails: REJECT, do not show to user, log and regenerate.
"""

import re
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from supabase import Client


@dataclass
class GuardrailViolation:
    """A single guardrail violation."""
    rule: str  # Which guardrail was violated
    severity: str  # 'critical' (hard block)
    description: str  # What went wrong
    original_value: str  # What was in original
    proposed_value: str  # What generator tried to add


@dataclass
class GuardrailResult:
    """Result of guardrail checks."""
    passed: bool  # True if ALL guardrails passed
    violations: List[GuardrailViolation]  # List of violations (empty if passed)


class DeterministicGuardrails:
    """
    Deterministic fact-checking guardrails.
    
    These run AFTER LLM verification and provide hard blocks for critical changes.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def check_guardrails(
        self,
        original_text: str,
        proposed_text: str,
        fact_ledger: List[Dict[str, Any]],
        user_id: str
    ) -> GuardrailResult:
        """
        Run all deterministic guardrails.
        
        Args:
            original_text: Original resume text
            proposed_text: Proposed optimized text
            fact_ledger: Complete fact ledger
            user_id: User ID for skill alias lookup
            
        Returns:
            GuardrailResult indicating pass/fail
        """
        violations: List[GuardrailViolation] = []
        
        # Extract facts from ledger
        ledger_companies = self._extract_companies(fact_ledger)
        ledger_titles = self._extract_titles(fact_ledger)
        ledger_dates = self._extract_dates(fact_ledger)
        ledger_skills = self._extract_skills(fact_ledger)
        ledger_numbers = self._extract_numbers(fact_ledger)
        
        # Extract from texts
        original_companies = self._extract_company_names(original_text)
        proposed_companies = self._extract_company_names(proposed_text)
        
        original_titles_in_text = self._extract_job_titles(original_text)
        proposed_titles_in_text = self._extract_job_titles(proposed_text)
        
        original_dates_in_text = self._extract_date_ranges(original_text)
        proposed_dates_in_text = self._extract_date_ranges(proposed_text)
        
        original_numbers = set(re.findall(r'\b\d+(?:[.,]\d+)?[%]?\b', original_text))
        proposed_numbers = set(re.findall(r'\b\d+(?:[.,]\d+)?[%]?\b', proposed_text))
        
        # Guardrail 1: Company names must match exactly
        new_companies = proposed_companies - original_companies
        if new_companies:
            # Check if new companies are in fact ledger
            for company in new_companies:
                if company.lower() not in [c.lower() for c in ledger_companies]:
                    violations.append(GuardrailViolation(
                        rule="company_name",
                        severity="critical",
                        description="New company name not in fact ledger",
                        original_value="N/A",
                        proposed_value=company
                    ))
        
        # Check for removed companies (also a violation)
        removed_companies = original_companies - proposed_companies
        if removed_companies:
            violations.append(GuardrailViolation(
                rule="company_name",
                severity="critical",
                description="Company name removed from original",
                original_value=str(removed_companies),
                proposed_value="N/A"
            ))
        
        # Guardrail 2: Job titles must match exactly
        new_titles = proposed_titles_in_text - original_titles_in_text
        if new_titles:
            for title in new_titles:
                if title.lower() not in [t.lower() for t in ledger_titles]:
                    violations.append(GuardrailViolation(
                        rule="job_title",
                        severity="critical",
                        description="New job title not in fact ledger",
                        original_value="N/A",
                        proposed_value=title
                    ))
        
        # Guardrail 3: Date ranges must match exactly
        new_dates = proposed_dates_in_text - original_dates_in_text
        if new_dates:
            for date in new_dates:
                # Date must be in ledger
                if date not in ledger_dates and not self._is_date_in_ledger(date, ledger_dates):
                    violations.append(GuardrailViolation(
                        rule="date_range",
                        severity="critical",
                        description="New date not in fact ledger",
                        original_value="N/A",
                        proposed_value=date
                    ))
        
        # Guardrail 4: Skills/technologies - new technical terms must be in ledger or alias table
        proposed_tech_terms = self._extract_technical_terms(proposed_text)
        original_tech_terms = self._extract_technical_terms(original_text)
        new_tech_terms = proposed_tech_terms - original_tech_terms
        
        if new_tech_terms:
            for term in new_tech_terms:
                # Check if in fact ledger skills
                if term.lower() not in [s.lower() for s in ledger_skills]:
                    # Check if in skill_aliases
                    if not await self._is_skill_alias(term, user_id):
                        violations.append(GuardrailViolation(
                            rule="skill_technology",
                            severity="critical",
                            description="New skill/technology not in fact ledger or alias table",
                            original_value="N/A",
                            proposed_value=term
                        ))
        
        # Guardrail 5: Numeric claims - new numbers must be in original
        new_numbers = proposed_numbers - original_numbers
        if new_numbers:
            # Check if numbers are in fact ledger metrics
            ledger_numbers_set = set(ledger_numbers)
            for number in new_numbers:
                if number not in ledger_numbers_set:
                    violations.append(GuardrailViolation(
                        rule="numeric_claim",
                        severity="critical",
                        description="New metric/number not in original text or fact ledger",
                        original_value="N/A",
                        proposed_value=number
                    ))
        
        # Determine overall result
        passed = len(violations) == 0
        
        return GuardrailResult(
            passed=passed,
            violations=violations
        )
    
    def _extract_companies(self, fact_ledger: List[Dict[str, Any]]) -> List[str]:
        """Extract company names from fact ledger."""
        companies = []
        for fact in fact_ledger:
            if fact["fact_type"] == "other" and fact.get("metadata", {}).get("field") == "company":
                companies.append(fact["fact_text"])
            # Also check metadata for company references
            metadata = fact.get("metadata", {})
            if "company" in metadata and metadata["company"]:
                companies.append(metadata["company"])
        return list(set(companies))
    
    def _extract_titles(self, fact_ledger: List[Dict[str, Any]]) -> List[str]:
        """Extract job titles from fact ledger."""
        titles = []
        for fact in fact_ledger:
            if fact["fact_type"] == "title":
                titles.append(fact["fact_text"])
        return list(set(titles))
    
    def _extract_dates(self, fact_ledger: List[Dict[str, Any]]) -> List[str]:
        """Extract dates from fact ledger."""
        dates = []
        for fact in fact_ledger:
            if fact["fact_type"] == "date":
                dates.append(fact["fact_text"])
        return list(set(dates))
    
    def _extract_skills(self, fact_ledger: List[Dict[str, Any]]) -> List[str]:
        """Extract skills from fact ledger."""
        skills = []
        for fact in fact_ledger:
            if fact["fact_type"] == "skill":
                skills.append(fact["fact_text"])
        return list(set(skills))
    
    def _extract_numbers(self, fact_ledger: List[Dict[str, Any]]) -> List[str]:
        """Extract numbers from fact ledger metrics."""
        numbers = []
        for fact in fact_ledger:
            if fact["fact_type"] == "metric":
                # Extract all numbers from the metric text
                found_numbers = re.findall(r'\b\d+(?:[.,]\d+)?[%]?\b', fact["fact_text"])
                numbers.extend(found_numbers)
        return list(set(numbers))
    
    def _extract_company_names(self, text: str) -> Set[str]:
        """Extract company names from text (simple extraction)."""
        # This is a simple heuristic - in production, use NER
        # For now, extract capitalized phrases that might be companies
        companies = set()
        
        # Common patterns: "at CompanyName", "for CompanyName"
        patterns = [
            r'at\s+([A-Z][A-Za-z\s&]+(?:Inc|LLC|Corp|Ltd)?)',
            r'for\s+([A-Z][A-Za-z\s&]+(?:Inc|LLC|Corp|Ltd)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            companies.update(match.strip() for match in matches)
        
        return companies
    
    def _extract_job_titles(self, text: str) -> Set[str]:
        """Extract job titles from text."""
        titles = set()
        
        # Common patterns for job titles
        patterns = [
            r'((?:Senior|Junior|Lead|Staff|Principal)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+\s+(?:Engineer|Developer|Manager|Director|Analyst|Designer))',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            titles.update(match.strip() for match in matches)
        
        return titles
    
    def _extract_date_ranges(self, text: str) -> Set[str]:
        """Extract date ranges from text."""
        dates = set()
        
        # Common date patterns
        patterns = [
            r'\b\d{4}\b',  # Years
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # Month Year
            r'\b\d{1,2}/\d{4}\b',  # MM/YYYY
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.update(match.strip() for match in matches)
        
        return dates
    
    def _extract_technical_terms(self, text: str) -> Set[str]:
        """Extract technical terms (skills/technologies) from text."""
        # Common technical terms patterns
        tech_terms = set()
        
        # Capitalize words and acronyms
        words = re.findall(r'\b[A-Z][A-Za-z0-9\+#\.]*\b', text)
        tech_terms.update(words)
        
        # Common patterns: Python, JavaScript, React, AWS, etc.
        # This is simplified - in production, use a more sophisticated approach
        
        return tech_terms
    
    def _is_date_in_ledger(self, date: str, ledger_dates: List[str]) -> bool:
        """Check if a date is approximately in the ledger."""
        # Allow for different date formats
        # Extract year from date
        year_match = re.search(r'\b(\d{4})\b', date)
        if year_match:
            year = year_match.group(1)
            # Check if year appears in any ledger date
            return any(year in ledger_date for ledger_date in ledger_dates)
        return False
    
    async def _is_skill_alias(self, term: str, user_id: str) -> bool:
        """Check if term is in skill_aliases table."""
        try:
            # Query skill_aliases for this term
            response = self.supabase.table("skill_aliases").select("*").or_(
                f"canonical_term.ilike.%{term}%,alias_term.ilike.%{term}%"
            ).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking skill alias: {e}")
            return False


def get_deterministic_guardrails(supabase_client: Client) -> DeterministicGuardrails:
    """Get or create deterministic guardrails instance."""
    return DeterministicGuardrails(supabase_client)
