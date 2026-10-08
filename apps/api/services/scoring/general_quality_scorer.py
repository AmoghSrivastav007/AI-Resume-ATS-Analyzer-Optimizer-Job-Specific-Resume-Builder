"""
General Resume Quality Score (no JD required).

Scoring Categories (reweighted to 100%):
- Parsing Compatibility: 36.4% (20% / 55% * 100)
- Structure: 27.3% (15% / 55% * 100)
- Content Quality: 18.2% (10% / 55% * 100)
- Formatting: 9.1% (5% / 55% * 100)
- Metadata: 9.1% (5% / 55% * 100)

Each category score = 100 - sum(issue deductions), floored at 0.
"""
from dataclasses import dataclass
from typing import Any

from models.quality_issue import ContentQualityAnalysis


# Category weights (sum to 100)
WEIGHTS = {
    "parsing_compatibility": 36.4,
    "structure": 27.3,
    "content_quality": 18.2,
    "formatting": 9.1,
    "metadata": 9.1,
}

# Issue deduction points by severity
SEVERITY_DEDUCTIONS = {
    "critical": 20.0,
    "high": 10.0,
    "medium": 5.0,
    "low": 2.0,
}


@dataclass(frozen=True)
class CategoryScore:
    """Score for a single category."""
    category: str
    raw_score: float  # 0-100
    weighted_score: float  # 0-WEIGHT
    max_score: float  # The weight
    deductions: list[dict[str, Any]]  # List of {issue_id, severity, points, reason}


@dataclass(frozen=True)
class GeneralQualityScore:
    """Overall General Resume Quality Score."""
    overall_score: float  # 0-100
    category_scores: list[CategoryScore]
    score_breakdown: dict[str, Any]  # Explainability tree
    total_issues: int
    critical_issues: int
    high_issues: int


class GeneralQualityScorer:
    """
    Calculate General Resume Quality Score from deterministic + LLM issues.
    
    Does NOT require a job description.
    """

    def calculate(
        self,
        deterministic_issues: list[dict[str, Any]],
        content_quality_analysis: ContentQualityAnalysis,
    ) -> GeneralQualityScore:
        """
        Calculate overall score from issues.
        
        Args:
            deterministic_issues: Issues from ATS scorer (Step 3)
            content_quality_analysis: LLM analysis results
        
        Returns:
            GeneralQualityScore with breakdown
        """
        # Merge all issues
        all_issues = self._merge_issues(deterministic_issues, content_quality_analysis)
        
        # Group issues by category
        issues_by_category = self._group_issues_by_category(all_issues)
        
        # Calculate category scores
        category_scores = []
        for category, weight in WEIGHTS.items():
            category_issues = issues_by_category.get(category, [])
            category_score = self._calculate_category_score(category, weight, category_issues)
            category_scores.append(category_score)
        
        # Calculate overall weighted score
        overall_score = sum(cs.weighted_score for cs in category_scores)
        overall_score = round(max(0.0, min(100.0, overall_score)), 2)
        
        # Build explainability tree
        score_breakdown = self._build_explainability_tree(category_scores, all_issues)
        
        # Count issues by severity
        critical_count = len([i for i in all_issues if i["severity"] == "critical"])
        high_count = len([i for i in all_issues if i["severity"] == "high"])
        
        return GeneralQualityScore(
            overall_score=overall_score,
            category_scores=category_scores,
            score_breakdown=score_breakdown,
            total_issues=len(all_issues),
            critical_issues=critical_count,
            high_issues=high_count,
        )

    def _merge_issues(
        self,
        deterministic_issues: list[dict[str, Any]],
        content_analysis: ContentQualityAnalysis,
    ) -> list[dict[str, Any]]:
        """Merge deterministic and LLM issues into unified format."""
        merged = []
        
        # Add deterministic issues (already in correct format)
        for issue in deterministic_issues:
            merged.append({
                "id": issue.get("id"),
                "issue_type": issue.get("issue_type", "other"),
                "severity": issue.get("severity", "medium"),
                "title": issue.get("title", ""),
                "description": issue.get("description", ""),
                "metadata": issue.get("metadata", {}),
                "source": "deterministic",
            })
        
        # Add LLM content quality issues
        for idx, llm_issue in enumerate(content_analysis.issues):
            merged.append({
                "id": f"llm_{idx}",
                "issue_type": llm_issue.issue_category,
                "severity": llm_issue.severity,
                "title": llm_issue.problem,
                "description": llm_issue.why_it_matters,
                "metadata": {
                    "current_text": llm_issue.current_text,
                    "suggested_correction": llm_issue.suggested_correction,
                    "expected_benefit": llm_issue.expected_benefit,
                    "confidence_level": llm_issue.confidence_level,
                    "location": llm_issue.location,
                },
                "source": "llm",
            })
        
        return merged

    def _group_issues_by_category(self, issues: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group issues into scoring categories."""
        grouped: dict[str, list[dict[str, Any]]] = {
            "parsing_compatibility": [],
            "structure": [],
            "content_quality": [],
            "formatting": [],
            "metadata": [],
        }
        
        for issue in issues:
            issue_type = issue.get("issue_type", "other")
            
            # Map issue types to categories
            if issue_type in ["content", "grammar"]:
                grouped["content_quality"].append(issue)
            elif issue_type == "keyword":
                grouped["structure"].append(issue)
            elif issue_type == "formatting":
                grouped["formatting"].append(issue)
            elif issue_type == "truth":
                grouped["content_quality"].append(issue)
            else:
                # Default mapping
                if "missing" in issue.get("title", "").lower():
                    grouped["structure"].append(issue)
                elif "format" in issue.get("title", "").lower():
                    grouped["formatting"].append(issue)
                else:
                    grouped["parsing_compatibility"].append(issue)
        
        return grouped

    def _calculate_category_score(
        self,
        category: str,
        weight: float,
        issues: list[dict[str, Any]],
    ) -> CategoryScore:
        """Calculate score for a single category."""
        # Calculate total deductions
        total_deduction = 0.0
        deductions = []
        
        for issue in issues:
            severity = issue.get("severity", "medium")
            points = SEVERITY_DEDUCTIONS.get(severity, 5.0)
            total_deduction += points
            
            deductions.append({
                "issue_id": issue.get("id"),
                "severity": severity,
                "points": points,
                "reason": issue.get("title", ""),
                "description": issue.get("description", ""),
            })
        
        # Raw score = 100 - deductions, floored at 0
        raw_score = max(0.0, 100.0 - total_deduction)
        
        # Weighted score = raw_score * (weight / 100)
        weighted_score = raw_score * (weight / 100.0)
        
        return CategoryScore(
            category=category,
            raw_score=round(raw_score, 2),
            weighted_score=round(weighted_score, 2),
            max_score=weight,
            deductions=deductions,
        )

    def _build_explainability_tree(
        self,
        category_scores: list[CategoryScore],
        all_issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Build explainability tree:
        
        {
          "overall_score": 78.5,
          "categories": {
            "parsing_compatibility": {
              "raw_score": 85.0,
              "weighted_score": 30.94,
              "max_score": 36.4,
              "weight_percentage": 36.4,
              "deductions": [
                {
                  "points": -10.0,
                  "reason": "Missing Contact Information",
                  "issue_id": "...",
                  "recommendation": "Add phone number and location"
                }
              ]
            },
            ...
          }
        }
        """
        overall = sum(cs.weighted_score for cs in category_scores)
        
        tree: dict[str, Any] = {
            "overall_score": round(overall, 2),
            "categories": {},
        }
        
        # Build issue lookup
        issue_map = {issue["id"]: issue for issue in all_issues}
        
        for cat_score in category_scores:
            tree["categories"][cat_score.category] = {
                "raw_score": cat_score.raw_score,
                "weighted_score": cat_score.weighted_score,
                "max_score": cat_score.max_score,
                "weight_percentage": cat_score.max_score,
                "deductions": [
                    {
                        "points": -ded["points"],
                        "reason": ded["reason"],
                        "description": ded["description"],
                        "issue_id": ded["issue_id"],
                        "severity": ded["severity"],
                        "recommendation": self._get_recommendation(issue_map.get(ded["issue_id"])),
                    }
                    for ded in cat_score.deductions
                ],
            }
        
        return tree

    def _get_recommendation(self, issue: dict[str, Any] | None) -> str:
        """Extract recommendation from issue."""
        if not issue:
            return "Review and correct this issue"
        
        metadata = issue.get("metadata", {})
        
        # LLM issues have suggested_correction
        if "suggested_correction" in metadata:
            return metadata["suggested_correction"]
        
        # Deterministic issues may have problems list
        if "problems" in metadata:
            problems = metadata["problems"]
            if problems:
                return problems[0] if isinstance(problems, list) else str(problems)
        
        # Default
        return issue.get("description", "Review and correct this issue")
