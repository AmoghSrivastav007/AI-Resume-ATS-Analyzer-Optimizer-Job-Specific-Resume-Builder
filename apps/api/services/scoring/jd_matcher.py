from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RequirementMatch:
    requirement_id: str
    requirement_text: str
    requirement_type: str
    match_score: float  # 0-100
    match_status: str  # matched | partial | missing
    evidence: dict[str, Any]


@dataclass(frozen=True)
class JDMatchResult:
    overall_score: float  # 0-100
    matches: list[RequirementMatch]
    summary: dict[str, Any]


class JDMatcher:
    """
    Matches a resume against job description requirements.
    
    Uses keyword matching and semantic comparison to determine:
    - Which requirements are met
    - Which are partially met
    - Which are missing
    """

    def match(
        self,
        resume_data: dict[str, Any],
        jd_requirements: list[dict[str, Any]],
    ) -> JDMatchResult:
        """Match resume against job requirements."""
        extraction = resume_data.get("extraction") or {}
        
        # Build resume keyword sets
        resume_keywords = self._extract_resume_keywords(extraction)
        
        matches: list[RequirementMatch] = []
        
        for req in jd_requirements:
            match = self._match_requirement(
                requirement=req,
                resume_keywords=resume_keywords,
                extraction=extraction,
            )
            matches.append(match)

        # Calculate overall score
        overall_score = self._calculate_overall_score(matches, jd_requirements)

        # Build summary
        matched_count = len([m for m in matches if m.match_status == "matched"])
        partial_count = len([m for m in matches if m.match_status == "partial"])
        missing_count = len([m for m in matches if m.match_status == "missing"])

        required_matches = [
            m for m in matches 
            if m.requirement_type == "required" and m.match_status == "matched"
        ]
        required_total = len([m for m in matches if m.requirement_type == "required"])

        summary = {
            "overall_score": round(overall_score, 2),
            "matched": matched_count,
            "partial": partial_count,
            "missing": missing_count,
            "total_requirements": len(jd_requirements),
            "required_matched": len(required_matches),
            "required_total": required_total,
            "match_rate": round(matched_count / len(jd_requirements) * 100, 2) if jd_requirements else 0,
        }

        return JDMatchResult(
            overall_score=round(overall_score, 2),
            matches=matches,
            summary=summary,
        )

    def _extract_resume_keywords(self, extraction: dict[str, Any]) -> dict[str, set[str]]:
        """Extract searchable keywords from resume."""
        keywords: dict[str, set[str]] = {
            "skills": set(),
            "titles": set(),
            "companies": set(),
            "degrees": set(),
            "certifications": set(),
            "technologies": set(),
        }

        # Skills
        for skill in extraction.get("skills") or []:
            name = skill.get("name", "").lower()
            if name:
                keywords["skills"].add(name)

        # Work experience
        for exp in extraction.get("work_experience") or []:
            title = exp.get("title", "").lower()
            company = exp.get("company", "").lower()
            if title:
                keywords["titles"].add(title)
            if company:
                keywords["companies"].add(company)
            
            # Extract keywords from bullets
            for bullet in exp.get("bullets") or []:
                bullet_lower = bullet.lower()
                # Simple keyword extraction from bullets
                words = bullet_lower.split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        keywords["skills"].add(word.strip(",.;:()"))

        # Education
        for edu in extraction.get("education") or []:
            degree = edu.get("degree", "").lower()
            if degree:
                keywords["degrees"].add(degree)

        # Certifications
        for cert in extraction.get("certifications") or []:
            name = cert.get("name", "").lower()
            if name:
                keywords["certifications"].add(name)

        # Projects
        for project in extraction.get("projects") or []:
            for tech in project.get("technologies") or []:
                tech_lower = tech.lower()
                if tech_lower:
                    keywords["technologies"].add(tech_lower)

        return keywords

    def _match_requirement(
        self,
        requirement: dict[str, Any],
        resume_keywords: dict[str, set[str]],
        extraction: dict[str, Any],
    ) -> RequirementMatch:
        """Match a single requirement against resume."""
        req_text = requirement.get("requirement_text", "").lower()
        req_type = requirement.get("requirement_type", "required")
        req_id = requirement.get("id", "")

        # Simple keyword-based matching
        evidence: dict[str, Any] = {"matched_terms": [], "context": []}
        match_score = 0.0

        # Check skills
        for skill in resume_keywords["skills"]:
            if skill in req_text or req_text in skill:
                evidence["matched_terms"].append(skill)
                match_score += 15

        # Check titles
        for title in resume_keywords["titles"]:
            if title in req_text or req_text in title:
                evidence["matched_terms"].append(f"title: {title}")
                match_score += 10

        # Check certifications
        for cert in resume_keywords["certifications"]:
            if cert in req_text or req_text in cert:
                evidence["matched_terms"].append(f"cert: {cert}")
                match_score += 20

        # Check degrees
        for degree in resume_keywords["degrees"]:
            if degree in req_text or req_text in degree:
                evidence["matched_terms"].append(f"degree: {degree}")
                match_score += 15

        # Check technologies
        for tech in resume_keywords["technologies"]:
            if tech in req_text or req_text in tech:
                evidence["matched_terms"].append(f"tech: {tech}")
                match_score += 10

        # Cap at 100
        match_score = min(100.0, match_score)

        # Determine match status
        if match_score >= 70:
            match_status = "matched"
        elif match_score >= 30:
            match_status = "partial"
        else:
            match_status = "missing"

        return RequirementMatch(
            requirement_id=req_id,
            requirement_text=requirement.get("requirement_text", ""),
            requirement_type=req_type,
            match_score=round(match_score, 2),
            match_status=match_status,
            evidence=evidence,
        )

    def _calculate_overall_score(
        self,
        matches: list[RequirementMatch],
        jd_requirements: list[dict[str, Any]],
    ) -> float:
        """Calculate weighted overall match score."""
        if not matches:
            return 0.0

        # Weight by requirement type
        weights = {
            "required": 1.0,
            "preferred": 0.7,
            "nice_to_have": 0.3,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for match in matches:
            weight = weights.get(match.requirement_type, 1.0)
            weighted_sum += match.match_score * weight
            total_weight += weight * 100  # Max score is 100

        overall = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0
        return overall
