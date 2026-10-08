"""
Matching Service orchestrator for Step 6.

Coordinates:
1. Embedding generation for skills and requirements
2. 4-layer matching engine
3. JD Match Score calculation
4. Persistence to match_results and resume_analyses
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from supabase import Client

from services.embedding_service import get_embedding_service
from services.matching_engine import MatchingEngine, MatchResult
from services.jd_match_scorer import JDMatchScorer, JDMatchScore


class MatchingService:
    """
    Orchestrates the complete matching pipeline.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.embedding_service = get_embedding_service()
        self.matching_engine = MatchingEngine(supabase_client)
        self.scorer = JDMatchScorer()
    
    async def ensure_embeddings(
        self,
        job_posting_id: str,
        resume_version_id: str,
        user_id: str
    ) -> None:
        """
        Ensure all skills and requirements have embeddings.
        Generate embeddings for any missing ones.
        """
        # Embed job requirements
        requirements_response = self.supabase.table("job_requirements").select(
            "*"
        ).eq("job_posting_id", job_posting_id).eq("user_id", user_id).execute()
        
        for req in requirements_response.data or []:
            if not req.get("embedding"):
                embedding = await self.embedding_service.embed_text(req["requirement_text"])
                self.supabase.table("job_requirements").update({
                    "embedding": embedding
                }).eq("id", req["id"]).execute()
        
        # Embed resume skills
        skills_response = self.supabase.table("skills").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        for skill in skills_response.data or []:
            if not skill.get("embedding"):
                embedding = await self.embedding_service.embed_text(skill["name"])
                self.supabase.table("skills").update({
                    "embedding": embedding
                }).eq("id", skill["id"]).execute()
        
        # Embed resume blocks
        blocks_response = self.supabase.table("resume_blocks").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        for block in blocks_response.data or []:
            if not block.get("embedding"):
                content = block.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else str(content)
                if text:
                    embedding = await self.embedding_service.embed_text(text)
                    self.supabase.table("resume_blocks").update({
                        "embedding": embedding
                    }).eq("id", block["id"]).execute()
        
        # Embed experiences
        experiences_response = self.supabase.table("experiences").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        for exp in experiences_response.data or []:
            if not exp.get("embedding"):
                # Combine title, company, and description
                text_parts = [
                    exp.get("title", ""),
                    exp.get("company", ""),
                    exp.get("description", "")
                ]
                bullets = exp.get("bullets", [])
                if bullets:
                    text_parts.extend([str(b) for b in bullets])
                
                combined_text = " ".join(filter(None, text_parts))
                if combined_text:
                    embedding = await self.embedding_service.embed_text(combined_text)
                    self.supabase.table("experiences").update({
                        "embedding": embedding
                    }).eq("id", exp["id"]).execute()
    
    async def run_matching_analysis(
        self,
        resume_version_id: str,
        job_posting_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Run complete matching analysis.
        
        1. Ensure embeddings exist
        2. Run 4-layer matching
        3. Calculate JD Match Score
        4. Persist results
        5. Return analysis
        
        Args:
            resume_version_id: Resume version ID
            job_posting_id: Job posting ID
            user_id: User ID
            
        Returns:
            Complete analysis with match results and scores
        """
        # Step 1: Ensure embeddings
        await self.ensure_embeddings(job_posting_id, resume_version_id, user_id)
        
        # Step 2: Run matching engine
        match_results = await self.matching_engine.match_all_requirements(
            job_posting_id, resume_version_id, user_id
        )
        
        # Step 3: Get resume data for scoring
        resume_data = await self._get_resume_data(resume_version_id, user_id)
        
        # Step 4: Calculate JD Match Score
        jd_score = self.scorer.calculate_jd_match_score(match_results, resume_data)
        
        # Step 5: Persist results
        analysis_id = await self._persist_results(
            resume_version_id,
            job_posting_id,
            user_id,
            match_results,
            jd_score
        )
        
        # Step 6: Return complete analysis
        return {
            "analysis_id": str(analysis_id),
            "resume_version_id": resume_version_id,
            "job_posting_id": job_posting_id,
            "jd_match_score": jd_score.overall_score,
            "keyword_relevance": jd_score.keyword_relevance,
            "skills_alignment": jd_score.skills_alignment,
            "experience_relevance": jd_score.experience_relevance,
            "match_breakdown": jd_score.breakdown,
            "gap_analysis": jd_score.gap_analysis,
            "total_requirements": len(match_results),
            "matched": len([r for r in match_results if r.match_status == "matched"]),
            "partially_matched": len([r for r in match_results if r.match_status == "partially_matched"]),
            "missing": len([r for r in match_results if r.match_status == "missing"]),
            "weak_evidence": len([r for r in match_results if r.match_status == "weak_evidence"]),
            "match_results": [self._serialize_match_result(r) for r in match_results]
        }
    
    async def _get_resume_data(self, resume_version_id: str, user_id: str) -> Dict[str, Any]:
        """Fetch complete resume data for scoring."""
        skills = self.supabase.table("skills").select("*").eq(
            "resume_version_id", resume_version_id
        ).eq("user_id", user_id).execute().data or []
        
        experiences = self.supabase.table("experiences").select("*").eq(
            "resume_version_id", resume_version_id
        ).eq("user_id", user_id).execute().data or []
        
        blocks = self.supabase.table("resume_blocks").select("*").eq(
            "resume_version_id", resume_version_id
        ).eq("user_id", user_id).execute().data or []
        
        return {
            "skills": skills,
            "experiences": experiences,
            "blocks": blocks
        }
    
    async def _persist_results(
        self,
        resume_version_id: str,
        job_posting_id: str,
        user_id: str,
        match_results: List[MatchResult],
        jd_score: JDMatchScore
    ) -> UUID:
        """
        Persist matching results to database.
        
        Creates:
        1. resume_analyses record
        2. match_results records (one per requirement)
        """
        # Create analysis record
        analysis_id = uuid4()
        
        # Note: job_posting_id needs to reference job_descriptions for now
        # In production, update schema to allow job_postings FK or use lookup
        # For MVP, we'll use job_posting_id in summary field
        
        analysis_data = {
            "id": str(analysis_id),
            "user_id": user_id,
            "resume_version_id": resume_version_id,
            "job_description_id": None,  # Legacy field
            "analysis_type": "jd_match",
            "status": "completed",
            "overall_score": jd_score.overall_score,
            "jd_match_score": jd_score.overall_score,
            "match_breakdown": jd_score.breakdown,
            "summary": {
                "job_posting_id": job_posting_id,
                "keyword_relevance": jd_score.keyword_relevance,
                "skills_alignment": jd_score.skills_alignment,
                "experience_relevance": jd_score.experience_relevance,
                "gap_analysis": jd_score.gap_analysis
            }
        }
        
        self.supabase.table("resume_analyses").insert(analysis_data).execute()
        
        # Create match_results records
        for result in match_results:
            match_data = {
                "id": str(uuid4()),
                "user_id": user_id,
                "resume_analysis_id": str(analysis_id),
                "job_requirement_id": result.requirement_id,
                "match_score": result.match_score,
                "match_status": result.match_status,
                "match_layer": result.match_layer,
                "evidence_block_id": result.evidence_block_id,
                "recommendation": result.recommendation,
                "similarity_score": result.similarity_score,
                "evidence": {
                    "text": result.evidence_text,
                    "layer": result.match_layer,
                    "similarity": result.similarity_score
                }
            }
            
            self.supabase.table("match_results").insert(match_data).execute()
        
        return analysis_id
    
    def _serialize_match_result(self, result: MatchResult) -> Dict[str, Any]:
        """Convert MatchResult to dict for API response."""
        return {
            "requirement_id": result.requirement_id,
            "requirement_text": result.requirement_text,
            "requirement_type": result.requirement_type,
            "match_status": result.match_status,
            "match_layer": result.match_layer,
            "match_score": result.match_score,
            "evidence_block_id": result.evidence_block_id,
            "evidence_text": result.evidence_text,
            "similarity_score": result.similarity_score,
            "recommendation": result.recommendation
        }
    
    async def get_match_results(
        self,
        analysis_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get match results for an analysis.
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID for auth
            
        Returns:
            Complete match results with analysis summary
        """
        # Fetch analysis
        analysis_response = self.supabase.table("resume_analyses").select(
            "*"
        ).eq("id", analysis_id).eq("user_id", user_id).single().execute()
        
        if not analysis_response.data:
            raise ValueError("Analysis not found")
        
        analysis = analysis_response.data
        
        # Fetch match results
        matches_response = self.supabase.table("match_results").select(
            "*, job_requirements(*)"
        ).eq("resume_analysis_id", analysis_id).eq("user_id", user_id).execute()
        
        matches = matches_response.data or []
        
        # Group by match status
        grouped_matches = {
            "matched": [m for m in matches if m["match_status"] == "matched"],
            "partially_matched": [m for m in matches if m["match_status"] == "partially_matched"],
            "weak_evidence": [m for m in matches if m["match_status"] == "weak_evidence"],
            "missing": [m for m in matches if m["match_status"] == "missing"],
            "not_relevant": [m for m in matches if m["match_status"] == "not_relevant"]
        }
        
        return {
            "analysis": analysis,
            "match_results": matches,
            "grouped_matches": grouped_matches,
            "summary": {
                "total": len(matches),
                "matched": len(grouped_matches["matched"]),
                "partially_matched": len(grouped_matches["partially_matched"]),
                "weak_evidence": len(grouped_matches["weak_evidence"]),
                "missing": len(grouped_matches["missing"]),
                "not_relevant": len(grouped_matches["not_relevant"])
            }
        }
