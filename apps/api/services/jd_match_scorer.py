"""
JD Match Score calculator (Step 6).

Calculates the JD Match Score based on keyword relevance, skills alignment,
and experience relevance. Separate from General Quality Score (Step 4).

Implements scoring from architecture §6.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from services.matching_engine import MatchResult


@dataclass
class JDMatchScore:
    """JD Match Score with explainability tree."""
    overall_score: float  # 0-100
    keyword_relevance: float  # 0-100
    skills_alignment: float  # 0-100
    experience_relevance: float  # 0-100
    breakdown: Dict[str, Any]  # Explainability tree
    gap_analysis: Dict[str, Any]  # Missing requirements


class JDMatchScorer:
    """
    Calculate JD Match Score based on matching results.
    
    Three categories (reweighted to 100%):
    - Keyword Relevance: 40%
    - Skills Alignment: 40%
    - Experience Relevance: 20%
    """
    
    # Category weights (sum to 100%)
    KEYWORD_WEIGHT = 0.40
    SKILLS_WEIGHT = 0.40
    EXPERIENCE_WEIGHT = 0.20
    
    def calculate_jd_match_score(
        self,
        match_results: List[MatchResult],
        resume_data: Dict[str, Any]
    ) -> JDMatchScore:
        """
        Calculate JD Match Score from matching results.
        
        Args:
            match_results: List of MatchResult objects from matching engine
            resume_data: Resume data for context (skills, experiences, etc.)
            
        Returns:
            JDMatchScore with overall score and breakdown
        """
        # Separate results by requirement type
        required_skills = [r for r in match_results if r.requirement_type == "required_skill"]
        preferred_skills = [r for r in match_results if r.requirement_type == "preferred_skill"]
        responsibilities = [r for r in match_results if r.requirement_type == "responsibility"]
        education = [r for r in match_results if r.requirement_type == "education"]
        experience_years = [r for r in match_results if r.requirement_type == "experience_years"]
        certifications = [r for r in match_results if r.requirement_type == "certification"]
        domain_knowledge = [r for r in match_results if r.requirement_type == "domain_knowledge"]
        competency_signals = [r for r in match_results if r.requirement_type == "competency_signal"]
        
        # Calculate category scores
        keyword_score = self._calculate_keyword_relevance(
            match_results, resume_data
        )
        
        skills_score = self._calculate_skills_alignment(
            required_skills, preferred_skills, certifications
        )
        
        experience_score = self._calculate_experience_relevance(
            responsibilities, experience_years, domain_knowledge, competency_signals
        )
        
        # Calculate weighted overall score
        overall_score = (
            keyword_score * self.KEYWORD_WEIGHT +
            skills_score * self.SKILLS_WEIGHT +
            experience_score * self.EXPERIENCE_WEIGHT
        )
        
        # Build explainability tree
        breakdown = self._build_explainability_tree(
            overall_score,
            keyword_score,
            skills_score,
            experience_score,
            match_results
        )
        
        # Generate gap analysis
        gap_analysis = self._generate_gap_analysis(match_results)
        
        return JDMatchScore(
            overall_score=round(overall_score, 2),
            keyword_relevance=round(keyword_score, 2),
            skills_alignment=round(skills_score, 2),
            experience_relevance=round(experience_score, 2),
            breakdown=breakdown,
            gap_analysis=gap_analysis
        )
    
    def _calculate_keyword_relevance(
        self,
        all_results: List[MatchResult],
        resume_data: Dict[str, Any]
    ) -> float:
        """
        Calculate keyword relevance score.
        
        Based on:
        - Presence of job keywords in resume
        - Keyword density (avoid stuffing)
        - Keyword positioning (early sections score higher)
        """
        if not all_results:
            return 0.0
        
        # Count matched vs total
        matched = [r for r in all_results if r.match_status in ["matched", "partially_matched"]]
        match_rate = len(matched) / len(all_results)
        
        # Base score from match rate
        base_score = match_rate * 100
        
        # Detect keyword stuffing (penalty)
        # Count occurrences of each requirement in resume
        # If any keyword appears >5 times, it's likely stuffing
        # TODO: Implement keyword stuffing detection (§7)
        stuffing_penalty = 0.0
        
        # Keyword positioning bonus
        # Requirements matched in early sections (skills, summary) get bonus
        early_matches = [r for r in matched if r.evidence_block_id]  # Has evidence
        positioning_bonus = min(5.0, len(early_matches) * 0.5)
        
        score = base_score - stuffing_penalty + positioning_bonus
        return max(0.0, min(100.0, score))
    
    def _calculate_skills_alignment(
        self,
        required_skills: List[MatchResult],
        preferred_skills: List[MatchResult],
        certifications: List[MatchResult]
    ) -> float:
        """
        Calculate skills alignment score.
        
        Weighted by requirement type:
        - Required skills: 70%
        - Preferred skills: 20%
        - Certifications: 10%
        """
        required_score = self._calculate_match_rate(required_skills) if required_skills else 100.0
        preferred_score = self._calculate_match_rate(preferred_skills) if preferred_skills else 100.0
        cert_score = self._calculate_match_rate(certifications) if certifications else 100.0
        
        # Weighted combination
        score = (
            required_score * 0.70 +
            preferred_score * 0.20 +
            cert_score * 0.10
        )
        
        return score
    
    def _calculate_experience_relevance(
        self,
        responsibilities: List[MatchResult],
        experience_years: List[MatchResult],
        domain_knowledge: List[MatchResult],
        competency_signals: List[MatchResult]
    ) -> float:
        """
        Calculate experience relevance score.
        
        Weighted by requirement type:
        - Responsibilities: 50%
        - Domain knowledge: 25%
        - Competency signals: 15%
        - Experience years: 10%
        """
        resp_score = self._calculate_match_rate(responsibilities) if responsibilities else 100.0
        domain_score = self._calculate_match_rate(domain_knowledge) if domain_knowledge else 100.0
        competency_score = self._calculate_match_rate(competency_signals) if competency_signals else 100.0
        years_score = self._calculate_match_rate(experience_years) if experience_years else 100.0
        
        # Weighted combination
        score = (
            resp_score * 0.50 +
            domain_score * 0.25 +
            competency_score * 0.15 +
            years_score * 0.10
        )
        
        return score
    
    def _calculate_match_rate(self, results: List[MatchResult]) -> float:
        """
        Calculate match rate for a list of results.
        
        Scoring:
        - matched: 100 points
        - partially_matched: 70 points
        - weak_evidence: 40 points
        - missing: 0 points
        - not_relevant: excluded from calculation
        """
        if not results:
            return 100.0
        
        relevant_results = [r for r in results if r.match_status != "not_relevant"]
        if not relevant_results:
            return 100.0
        
        total_points = 0.0
        for result in relevant_results:
            if result.match_status == "matched":
                total_points += 100.0
            elif result.match_status == "partially_matched":
                total_points += 70.0
            elif result.match_status == "weak_evidence":
                total_points += 40.0
            # missing = 0 points
        
        return total_points / len(relevant_results)
    
    def _build_explainability_tree(
        self,
        overall_score: float,
        keyword_score: float,
        skills_score: float,
        experience_score: float,
        match_results: List[MatchResult]
    ) -> Dict[str, Any]:
        """
        Build explainability tree matching Step 4's format.
        
        Format:
        {
          "overall_score": 85.0,
          "categories": {
            "keyword_relevance": {
              "weight": 40,
              "score": 90.0,
              "contribution": 36.0,
              "details": {...}
            },
            ...
          }
        }
        """
        return {
            "overall_score": overall_score,
            "categories": {
                "keyword_relevance": {
                    "weight": int(self.KEYWORD_WEIGHT * 100),
                    "score": keyword_score,
                    "contribution": round(keyword_score * self.KEYWORD_WEIGHT, 2),
                    "details": {
                        "matched_keywords": len([r for r in match_results if r.match_status == "matched"]),
                        "total_keywords": len(match_results),
                        "match_rate": round(len([r for r in match_results if r.match_status == "matched"]) / len(match_results) * 100, 2) if match_results else 0.0
                    }
                },
                "skills_alignment": {
                    "weight": int(self.SKILLS_WEIGHT * 100),
                    "score": skills_score,
                    "contribution": round(skills_score * self.SKILLS_WEIGHT, 2),
                    "details": {
                        "required_skills": self._get_type_summary(match_results, "required_skill"),
                        "preferred_skills": self._get_type_summary(match_results, "preferred_skill"),
                        "certifications": self._get_type_summary(match_results, "certification")
                    }
                },
                "experience_relevance": {
                    "weight": int(self.EXPERIENCE_WEIGHT * 100),
                    "score": experience_score,
                    "contribution": round(experience_score * self.EXPERIENCE_WEIGHT, 2),
                    "details": {
                        "responsibilities": self._get_type_summary(match_results, "responsibility"),
                        "domain_knowledge": self._get_type_summary(match_results, "domain_knowledge"),
                        "competency_signals": self._get_type_summary(match_results, "competency_signal"),
                        "experience_years": self._get_type_summary(match_results, "experience_years")
                    }
                }
            }
        }
    
    def _get_type_summary(self, results: List[MatchResult], req_type: str) -> Dict[str, int]:
        """Get summary counts for a requirement type."""
        type_results = [r for r in results if r.requirement_type == req_type]
        return {
            "total": len(type_results),
            "matched": len([r for r in type_results if r.match_status == "matched"]),
            "partially_matched": len([r for r in type_results if r.match_status == "partially_matched"]),
            "weak_evidence": len([r for r in type_results if r.match_status == "weak_evidence"]),
            "missing": len([r for r in type_results if r.match_status == "missing"])
        }
    
    def _generate_gap_analysis(self, match_results: List[MatchResult]) -> Dict[str, Any]:
        """
        Generate gap analysis showing missing requirements.
        """
        missing = [r for r in match_results if r.match_status == "missing"]
        weak = [r for r in match_results if r.match_status == "weak_evidence"]
        
        # Group by type
        gaps = {
            "critical": [  # Missing required skills
                {
                    "requirement": r.requirement_text,
                    "type": r.requirement_type,
                    "recommendation": r.recommendation
                }
                for r in missing if r.requirement_type == "required_skill"
            ],
            "important": [  # Missing preferred skills and certifications
                {
                    "requirement": r.requirement_text,
                    "type": r.requirement_type,
                    "recommendation": r.recommendation
                }
                for r in missing if r.requirement_type in ["preferred_skill", "certification"]
            ],
            "needs_improvement": [  # Weak evidence
                {
                    "requirement": r.requirement_text,
                    "type": r.requirement_type,
                    "recommendation": r.recommendation
                }
                for r in weak
            ]
        }
        
        return {
            "total_gaps": len(missing),
            "critical_gaps": len(gaps["critical"]),
            "gaps": gaps
        }
