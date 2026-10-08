from typing import Any
from uuid import UUID

from config import Settings
from services.audit import write_audit_log
from services.resume_query import get_resume_detail
from services.scoring.ats_scorer import ATSScorer
from services.scoring.content_quality_analyzer import analyze_content_quality
from services.scoring.general_quality_scorer import GeneralQualityScorer
from services.scoring.jd_matcher import JDMatcher
from services.scoring.jd_parser import parse_job_description
from services.supabase_client import create_service_client


class AnalysisService:
    """Service for running resume analyses (ATS scoring and JD matching)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = create_service_client(settings)

    def _resume_to_dict(self, resume_response: Any) -> dict[str, Any]:
        """Convert ResumeDetailResponse to dict for scorers/matchers."""
        data = resume_response.data
        
        # Build extraction dict from sections
        extraction: dict[str, Any] = {
            "contact": {},
            "summary": None,
            "work_experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "projects": [],
            "languages": [],
        }
        
        for section in data.sections:
            if section.section_type == "contact" and section.blocks:
                # Extract contact from first block content
                extraction["contact"] = section.blocks[0].content
            elif section.section_type == "summary" and section.blocks:
                extraction["summary"] = section.blocks[0].content.get("text")
            elif section.section_type == "experience":
                # Reconstruct work experience from blocks
                current_exp = None
                for block in section.blocks:
                    if block.block_type == "heading":
                        if current_exp:
                            extraction["work_experience"].append(current_exp)
                        current_exp = {**block.content, "bullets": []}
                    elif block.block_type == "bullet" and current_exp:
                        current_exp["bullets"].append(block.content.get("text", ""))
                if current_exp:
                    extraction["work_experience"].append(current_exp)
            elif section.section_type == "education":
                for block in section.blocks:
                    if block.block_type == "heading":
                        extraction["education"].append(block.content)
            elif section.section_type == "skills":
                for block in section.blocks:
                    extraction["skills"].append(block.content)
            elif section.section_type == "certifications":
                for block in section.blocks:
                    extraction["certifications"].append(block.content)
            elif section.section_type == "projects":
                for block in section.blocks:
                    if block.block_type == "heading":
                        extraction["projects"].append(block.content)
            elif section.section_type == "languages":
                for block in section.blocks:
                    extraction["languages"].append(block.content)
        
        return {
            "extraction": extraction,
            "sections": [
                {
                    "id": s.id,
                    "section_type": s.section_type,
                    "title": s.title,
                    "sort_order": s.sort_order,
                }
                for s in data.sections
            ],
            "blocks": [
                {
                    "id": b.id,
                    "section_id": s.id,
                    "block_type": b.block_type,
                    "content": b.content,
                    "sort_order": b.sort_order,
                }
                for s in data.sections
                for b in s.blocks
            ],
            "facts": [
                {
                    "id": f.id,
                    "fact_type": f.fact_type,
                    "fact_text": f.fact_text,
                    "is_verified": f.is_verified,
                    "metadata": f.metadata,
                }
                for f in data.facts
            ],
        }

    def run_ats_analysis(
        self,
        user_id: str,
        resume_version_id: str,
    ) -> dict[str, Any]:
        """Run ATS compatibility analysis on a resume (General Resume Quality Score)."""
        # Create analysis record
        analysis_row = (
            self.client.table("resume_analyses")
            .insert({
                "user_id": user_id,
                "resume_version_id": resume_version_id,
                "analysis_type": "ats",
                "status": "running",
            })
            .execute()
        )

        if not analysis_row.data:
            raise RuntimeError("Failed to create resume_analyses record")

        analysis = analysis_row.data[0]
        analysis_id = analysis["id"]

        try:
            # Get parsed resume data
            resume_response = get_resume_detail(self.client, user_id, resume_version_id)
            resume_data = self._resume_to_dict(resume_response)

            # Step 1: Run deterministic ATS scoring (from Step 3)
            ats_scorer = ATSScorer()
            ats_result = ats_scorer.score(resume_data)

            # Step 2: Run LLM content quality analysis (Sonnet model)
            content_analysis = analyze_content_quality(resume_data, self.settings)

            # Step 3: Calculate General Resume Quality Score
            quality_scorer = GeneralQualityScorer()
            quality_score = quality_scorer.calculate(
                deterministic_issues=ats_result.issues,
                content_quality_analysis=content_analysis,
            )

            # Persist all issues (deterministic + LLM)
            all_issues = []
            
            # Deterministic issues
            for issue in ats_result.issues:
                issue_row = self.client.table("issues").insert({
                    "user_id": user_id,
                    "resume_analysis_id": analysis_id,
                    "issue_type": issue["issue_type"],
                    "severity": issue["severity"],
                    "title": issue["title"],
                    "description": issue["description"],
                    "affected_block_id": issue.get("affected_block_id"),
                    "metadata": issue.get("metadata", {}),
                }).execute()
                if issue_row.data:
                    all_issues.append(issue_row.data[0]["id"])
            
            # LLM content quality issues
            for llm_issue in content_analysis.issues:
                issue_row = self.client.table("issues").insert({
                    "user_id": user_id,
                    "resume_analysis_id": analysis_id,
                    "issue_type": llm_issue.issue_category,
                    "severity": llm_issue.severity,
                    "title": llm_issue.problem,
                    "description": llm_issue.why_it_matters,
                    "affected_block_id": None,  # Could map from location if needed
                    "metadata": {
                        "current_text": llm_issue.current_text,
                        "suggested_correction": llm_issue.suggested_correction,
                        "expected_benefit": llm_issue.expected_benefit,
                        "confidence_level": llm_issue.confidence_level,
                        "location": llm_issue.location,
                        "source": "llm_content_quality",
                    },
                }).execute()
                if issue_row.data:
                    all_issues.append(issue_row.data[0]["id"])

            # Build summary with explainability data
            summary = {
                "overall_score": quality_score.overall_score,
                "score_type": "general_resume_quality",
                "category_scores": {
                    cs.category: {
                        "raw_score": cs.raw_score,
                        "weighted_score": cs.weighted_score,
                        "max_score": cs.max_score,
                    }
                    for cs in quality_score.category_scores
                },
                "total_issues": quality_score.total_issues,
                "critical_issues": quality_score.critical_issues,
                "high_issues": quality_score.high_issues,
                "content_quality": {
                    "overall": content_analysis.overall_content_quality,
                    "summary": content_analysis.summary,
                    "strengths": content_analysis.strengths,
                    "weaknesses": content_analysis.weaknesses,
                },
            }

            # Update analysis record with score breakdown
            self.client.table("resume_analyses").update({
                "status": "completed",
                "overall_score": quality_score.overall_score,
                "summary": summary,
                "score_breakdown": quality_score.score_breakdown,
            }).eq("id", analysis_id).execute()

            write_audit_log(
                self.client,
                user_id,
                "create",
                "resume_analyses",
                analysis_id,
                {"event": "ats_analysis_v2", "score": quality_score.overall_score},
            )

            return {
                "analysis_id": analysis_id,
                "overall_score": quality_score.overall_score,
                "summary": summary,
                "issue_count": quality_score.total_issues,
            }

        except Exception as exc:
            self.client.table("resume_analyses").update({
                "status": "failed",
                "summary": {"error": str(exc)},
            }).eq("id", analysis_id).execute()
            raise

    def run_jd_match_analysis(
        self,
        user_id: str,
        resume_version_id: str,
        job_description_id: str,
    ) -> dict[str, Any]:
        """Run job description match analysis."""
        # Create analysis record
        analysis_row = (
            self.client.table("resume_analyses")
            .insert({
                "user_id": user_id,
                "resume_version_id": resume_version_id,
                "job_description_id": job_description_id,
                "analysis_type": "jd_match",
                "status": "running",
            })
            .execute()
        )

        if not analysis_row.data:
            raise RuntimeError("Failed to create resume_analyses record")

        analysis = analysis_row.data[0]
        analysis_id = analysis["id"]

        try:
            # Get resume data
            resume_response = get_resume_detail(self.client, user_id, resume_version_id)
            resume_data = self._resume_to_dict(resume_response)

            # Get JD requirements
            jd_response = (
                self.client.table("job_descriptions")
                .select("*, job_requirements(*)")
                .eq("id", job_description_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            if not jd_response.data:
                raise ValueError("Job description not found")

            jd_data = jd_response.data
            jd_requirements = jd_data.get("job_requirements") or []

            # Run matching
            matcher = JDMatcher()
            result = matcher.match(resume_data, jd_requirements)

            # Persist match results
            for match in result.matches:
                self.client.table("match_results").insert({
                    "user_id": user_id,
                    "resume_analysis_id": analysis_id,
                    "job_requirement_id": match.requirement_id,
                    "match_score": match.match_score,
                    "match_status": match.match_status,
                    "evidence": match.evidence,
                }).execute()

            # Create issues for missing requirements
            for match in result.matches:
                if match.match_status == "missing" and match.requirement_type == "required":
                    self.client.table("issues").insert({
                        "user_id": user_id,
                        "resume_analysis_id": analysis_id,
                        "issue_type": "keyword",
                        "severity": "high",
                        "title": "Missing Required Requirement",
                        "description": f"No evidence found for: {match.requirement_text}",
                        "metadata": {"requirement_id": match.requirement_id},
                    }).execute()

            # Update analysis record
            self.client.table("resume_analyses").update({
                "status": "completed",
                "overall_score": result.overall_score,
                "summary": result.summary,
            }).eq("id", analysis_id).execute()

            write_audit_log(
                self.client,
                user_id,
                "create",
                "resume_analyses",
                analysis_id,
                {"event": "jd_match_analysis", "score": result.overall_score},
            )

            return {
                "analysis_id": analysis_id,
                "overall_score": result.overall_score,
                "summary": result.summary,
                "match_count": len(result.matches),
            }

        except Exception as exc:
            self.client.table("resume_analyses").update({
                "status": "failed",
                "summary": {"error": str(exc)},
            }).eq("id", analysis_id).execute()
            raise

    def create_job_description(
        self,
        user_id: str,
        title: str,
        raw_text: str,
        company: str | None = None,
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """Create a job description and parse its requirements."""
        # Parse JD with LLM
        parsed = parse_job_description(raw_text, self.settings)

        # Create JD record
        jd_row = (
            self.client.table("job_descriptions")
            .insert({
                "user_id": user_id,
                "title": title,
                "company": company,
                "source_url": source_url,
                "raw_text": raw_text,
            })
            .execute()
        )

        if not jd_row.data:
            raise RuntimeError("Failed to create job_descriptions record")

        jd = jd_row.data[0]
        jd_id = jd["id"]

        # Create requirement records
        for req in parsed.requirements:
            self.client.table("job_requirements").insert({
                "user_id": user_id,
                "job_description_id": jd_id,
                "requirement_text": req.requirement_text,
                "requirement_type": req.requirement_type,
            }).execute()

        write_audit_log(
            self.client,
            user_id,
            "create",
            "job_descriptions",
            jd_id,
            {"event": "jd_created", "requirement_count": len(parsed.requirements)},
        )

        return {
            "id": jd_id,
            "title": title,
            "company": company,
            "requirement_count": len(parsed.requirements),
            "parsed": parsed.model_dump(),
        }

    def get_analysis(self, user_id: str, analysis_id: str) -> dict[str, Any]:
        """Get detailed analysis results."""
        # Get analysis with matches and issues
        response = (
            self.client.table("resume_analyses")
            .select("*, match_results(*), issues(*)")
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not response.data:
            raise ValueError("Analysis not found")

        return response.data
