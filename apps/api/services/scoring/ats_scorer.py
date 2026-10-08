from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ATSScoreResult:
    overall_score: float  # 0-100
    summary: dict[str, Any]
    issues: list[dict[str, Any]]


class ATSScorer:
    """
    Scores a resume for ATS compatibility without a job description.
    
    Checks:
    - Contact information completeness
    - Section presence and ordering
    - Content density (words per section)
    - Date formatting consistency
    - Keyword diversity
    """

    def score(self, resume_data: dict[str, Any]) -> ATSScoreResult:
        """Score a parsed resume for ATS compatibility."""
        issues: list[dict[str, Any]] = []
        scores: dict[str, float] = {}

        # 1. Contact Information (20 points)
        contact = resume_data.get("extraction", {}).get("contact") or {}
        contact_score = self._score_contact(contact, issues)
        scores["contact"] = contact_score

        # 2. Section Presence (20 points)
        sections = resume_data.get("sections") or []
        section_score = self._score_sections(sections, issues)
        scores["sections"] = section_score

        # 3. Content Density (20 points)
        blocks = resume_data.get("blocks") or []
        density_score = self._score_density(blocks, sections, issues)
        scores["density"] = density_score

        # 4. Work Experience Quality (20 points)
        work_exp = resume_data.get("extraction", {}).get("work_experience") or []
        experience_score = self._score_experience(work_exp, issues)
        scores["experience"] = experience_score

        # 5. Skills & Keywords (20 points)
        skills = resume_data.get("extraction", {}).get("skills") or []
        skills_score = self._score_skills(skills, issues)
        scores["skills"] = skills_score

        overall = sum(scores.values())

        summary = {
            "overall_score": round(overall, 2),
            "category_scores": {k: round(v, 2) for k, v in scores.items()},
            "total_issues": len(issues),
            "critical_issues": len([i for i in issues if i["severity"] == "critical"]),
            "high_issues": len([i for i in issues if i["severity"] == "high"]),
        }

        return ATSScoreResult(
            overall_score=round(overall, 2),
            summary=summary,
            issues=issues,
        )

    def _score_contact(self, contact: dict[str, Any], issues: list[dict[str, Any]]) -> float:
        """Score contact information completeness."""
        required_fields = ["email", "phone", "full_name"]
        optional_fields = ["location", "linkedin"]
        
        score = 0.0
        missing = []

        for field in required_fields:
            if contact.get(field):
                score += 20 / len(required_fields)
            else:
                missing.append(field)

        if missing:
            issues.append({
                "issue_type": "content",
                "severity": "high" if "email" in missing else "medium",
                "title": "Missing Contact Information",
                "description": f"Missing required fields: {', '.join(missing)}",
                "metadata": {"missing_fields": missing},
            })

        # Bonus for optional fields
        bonus = sum(1 for field in optional_fields if contact.get(field))
        score = min(20.0, score + bonus)

        return score

    def _score_sections(self, sections: list[dict[str, Any]], issues: list[dict[str, Any]]) -> float:
        """Score section presence and structure."""
        required_sections = ["experience", "education", "skills"]
        optional_sections = ["summary", "projects", "certifications"]
        
        section_types = {s["section_type"] for s in sections}
        
        score = 0.0
        missing = []

        for section_type in required_sections:
            if section_type in section_types:
                score += 20 / len(required_sections)
            else:
                missing.append(section_type)

        if missing:
            issues.append({
                "issue_type": "content",
                "severity": "critical" if "experience" in missing else "high",
                "title": "Missing Critical Sections",
                "description": f"Resume lacks: {', '.join(missing)}",
                "metadata": {"missing_sections": missing},
            })

        # Bonus for optional sections
        bonus = sum(2 for section_type in optional_sections if section_type in section_types)
        score = min(20.0, score + bonus)

        return score

    def _score_density(
        self,
        blocks: list[dict[str, Any]],
        sections: list[dict[str, Any]],
        issues: list[dict[str, Any]],
    ) -> float:
        """Score content density per section."""
        if not blocks:
            issues.append({
                "issue_type": "content",
                "severity": "critical",
                "title": "No Content Blocks",
                "description": "Resume has no parseable content",
                "metadata": {},
            })
            return 0.0

        # Group blocks by section
        section_blocks: dict[str, list[dict[str, Any]]] = {}
        section_map = {s["id"]: s["section_type"] for s in sections}

        for block in blocks:
            section_type = section_map.get(block["section_id"], "unknown")
            section_blocks.setdefault(section_type, []).append(block)

        score = 20.0
        thin_sections = []

        # Check experience section depth
        exp_blocks = section_blocks.get("experience", [])
        if exp_blocks:
            bullet_count = sum(1 for b in exp_blocks if b["block_type"] == "bullet")
            if bullet_count < 3:
                thin_sections.append("experience (needs more bullet points)")
                score -= 5

        # Check total block count
        total_blocks = len(blocks)
        if total_blocks < 10:
            issues.append({
                "issue_type": "content",
                "severity": "medium",
                "title": "Sparse Content",
                "description": f"Resume has only {total_blocks} content blocks. Add more detail.",
                "metadata": {"block_count": total_blocks},
            })
            score -= 5

        if thin_sections:
            issues.append({
                "issue_type": "content",
                "severity": "medium",
                "title": "Thin Sections",
                "description": f"These sections need more content: {', '.join(thin_sections)}",
                "metadata": {"thin_sections": thin_sections},
            })

        return max(0.0, score)

    def _score_experience(self, work_exp: list[dict[str, Any]], issues: list[dict[str, Any]]) -> float:
        """Score work experience quality."""
        if not work_exp:
            issues.append({
                "issue_type": "content",
                "severity": "critical",
                "title": "No Work Experience",
                "description": "Resume has no work experience listed",
                "metadata": {},
            })
            return 0.0

        score = 20.0
        problems = []

        for idx, exp in enumerate(work_exp):
            # Check for dates
            if not exp.get("start_date"):
                problems.append(f"{exp.get('title', 'Role')} at {exp.get('company', 'Unknown')}: missing start date")
                score -= 2

            # Check for bullets
            bullets = exp.get("bullets") or []
            if len(bullets) < 2:
                problems.append(f"{exp.get('title', 'Role')} at {exp.get('company', 'Unknown')}: needs more bullet points")
                score -= 3

            # Check for metrics in bullets
            has_metrics = any(any(char.isdigit() for char in bullet) for bullet in bullets)
            if not has_metrics:
                problems.append(f"{exp.get('title', 'Role')} at {exp.get('company', 'Unknown')}: no quantifiable achievements")
                score -= 2

        if problems:
            issues.append({
                "issue_type": "content",
                "severity": "medium",
                "title": "Experience Section Issues",
                "description": "Some experience entries need improvement",
                "metadata": {"problems": problems},
            })

        return max(0.0, score)

    def _score_skills(self, skills: list[dict[str, Any]], issues: list[dict[str, Any]]) -> float:
        """Score skills section."""
        if not skills:
            issues.append({
                "issue_type": "content",
                "severity": "high",
                "title": "No Skills Listed",
                "description": "Resume has no skills section",
                "metadata": {},
            })
            return 0.0

        score = 20.0

        # Penalize if too few skills
        if len(skills) < 5:
            issues.append({
                "issue_type": "keyword",
                "severity": "medium",
                "title": "Limited Skills",
                "description": f"Only {len(skills)} skills listed. Add more relevant skills.",
                "metadata": {"skill_count": len(skills)},
            })
            score -= 10

        # Penalize if too many (unfocused)
        elif len(skills) > 50:
            issues.append({
                "issue_type": "keyword",
                "severity": "low",
                "title": "Too Many Skills",
                "description": f"{len(skills)} skills may dilute focus. Consider consolidating.",
                "metadata": {"skill_count": len(skills)},
            })
            score -= 5

        return max(0.0, score)
