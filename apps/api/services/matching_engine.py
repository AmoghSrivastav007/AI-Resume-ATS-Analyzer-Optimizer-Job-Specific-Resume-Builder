"""
4-Layer Matching Engine for Resume-to-JD matching (Step 6).

Implements the matching strategy from architecture §7:
- Layer 1: Exact match (normalized string)
- Layer 2: Alias match (skill_aliases table)
- Layer 3: Semantic match (pgvector cosine similarity, banded)
- Layer 4: Context/evidence match (LLM judges demonstration vs listing)
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from supabase import Client
from anthropic import Anthropic

from services.embedding_service import get_embedding_service


@dataclass
class MatchResult:
    """Result of matching a job requirement against a resume."""
    requirement_id: str
    requirement_text: str
    requirement_type: str
    match_status: str  # matched, partially_matched, missing, weak_evidence, not_relevant
    match_layer: int  # 1-4, which layer found the match
    match_score: float  # 0-100
    evidence_block_id: Optional[str] = None
    evidence_text: Optional[str] = None
    similarity_score: Optional[float] = None  # For layer 3
    recommendation: Optional[str] = None


class MatchingEngine:
    """
    4-layer matching engine for resume-to-JD matching.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.embedding_service = get_embedding_service()
        
        # LLM for Layer 4 context matching
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.haiku_model = os.getenv("ANTHROPIC_HAIKU_MODEL", "claude-3-haiku-20240307")
        if self.anthropic_key:
            self.anthropic = Anthropic(api_key=self.anthropic_key)
        else:
            self.anthropic = None
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for exact matching."""
        # Remove special characters, lowercase, trim whitespace
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    async def match_requirement(
        self,
        requirement: Dict,
        resume_skills: List[Dict],
        resume_blocks: List[Dict],
        resume_experiences: List[Dict]
    ) -> MatchResult:
        """
        Match a single job requirement against resume using 4-layer strategy.
        
        Args:
            requirement: Job requirement dict with id, text, type, embedding
            resume_skills: List of skills from resume
            resume_blocks: List of resume blocks (bullets, paragraphs)
            resume_experiences: List of experience entries
            
        Returns:
            MatchResult with classification and evidence
        """
        req_id = requirement["id"]
        req_text = requirement["requirement_text"]
        req_type = requirement["requirement_type"]
        req_embedding = requirement.get("embedding")
        
        # Layer 1: Exact match
        layer1_result = await self._layer1_exact_match(req_text, resume_skills, resume_blocks)
        if layer1_result:
            return layer1_result
        
        # Layer 2: Alias match
        layer2_result = await self._layer2_alias_match(req_text, resume_skills, resume_blocks)
        if layer2_result:
            return layer2_result
        
        # Layer 3: Semantic match (pgvector)
        if req_embedding:
            layer3_result = await self._layer3_semantic_match(
                req_id, req_text, req_type, req_embedding,
                resume_skills, resume_blocks, resume_experiences
            )
            if layer3_result:
                # If similarity > 0.85, auto-match
                if layer3_result.similarity_score and layer3_result.similarity_score > 0.85:
                    return layer3_result
                # If 0.70 <= similarity <= 0.85, send to Layer 4
                elif layer3_result.similarity_score and layer3_result.similarity_score >= 0.70:
                    # Layer 4: Context/evidence match (LLM)
                    layer4_result = await self._layer4_context_match(
                        req_text, req_type, layer3_result, resume_blocks
                    )
                    if layer4_result:
                        return layer4_result
                # If similarity < 0.70, not a match - continue to missing classification
        
        # No match found in any layer
        return MatchResult(
            requirement_id=req_id,
            requirement_text=req_text,
            requirement_type=req_type,
            match_status="missing",
            match_layer=0,
            match_score=0.0,
            recommendation=self._generate_missing_recommendation(req_text, req_type)
        )
    
    async def _layer1_exact_match(
        self,
        req_text: str,
        resume_skills: List[Dict],
        resume_blocks: List[Dict]
    ) -> Optional[MatchResult]:
        """
        Layer 1: Exact string match (normalized).
        """
        normalized_req = self.normalize_text(req_text)
        
        # Check skills
        for skill in resume_skills:
            normalized_skill = self.normalize_text(skill["name"])
            if normalized_skill == normalized_req:
                return MatchResult(
                    requirement_id="",  # Will be set by caller
                    requirement_text=req_text,
                    requirement_type="",  # Will be set by caller
                    match_status="matched",
                    match_layer=1,
                    match_score=100.0,
                    evidence_text=f"Skill listed: {skill['name']}",
                    recommendation="Exact match found"
                )
        
        # Check resume blocks (bullets, paragraphs)
        for block in resume_blocks:
            content = block.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            normalized_block = self.normalize_text(text)
            
            if normalized_req in normalized_block:
                return MatchResult(
                    requirement_id="",
                    requirement_text=req_text,
                    requirement_type="",
                    match_status="matched",
                    match_layer=1,
                    match_score=100.0,
                    evidence_block_id=block["id"],
                    evidence_text=text[:200],  # First 200 chars
                    recommendation="Exact match found in resume content"
                )
        
        return None
    
    async def _layer2_alias_match(
        self,
        req_text: str,
        resume_skills: List[Dict],
        resume_blocks: List[Dict]
    ) -> Optional[MatchResult]:
        """
        Layer 2: Alias match using skill_aliases table.
        """
        normalized_req = self.normalize_text(req_text)
        
        # Query skill_aliases for matches
        response = self.supabase.table("skill_aliases").select("*").or_(
            f"canonical_term.ilike.%{req_text}%,alias_term.ilike.%{req_text}%"
        ).execute()
        
        if not response.data:
            return None
        
        # Get all canonical terms and aliases
        canonical_terms = set()
        alias_terms = set()
        for alias in response.data:
            canonical_terms.add(self.normalize_text(alias["canonical_term"]))
            alias_terms.add(self.normalize_text(alias["alias_term"]))
        
        # Check skills against aliases
        for skill in resume_skills:
            normalized_skill = self.normalize_text(skill["name"])
            if normalized_skill in canonical_terms or normalized_skill in alias_terms:
                return MatchResult(
                    requirement_id="",
                    requirement_text=req_text,
                    requirement_type="",
                    match_status="matched",
                    match_layer=2,
                    match_score=95.0,
                    evidence_text=f"Skill listed: {skill['name']} (alias match)",
                    recommendation="Alias match found"
                )
        
        # Check resume blocks
        for block in resume_blocks:
            content = block.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            normalized_block = self.normalize_text(text)
            
            for term in canonical_terms.union(alias_terms):
                if term in normalized_block:
                    return MatchResult(
                        requirement_id="",
                        requirement_text=req_text,
                        requirement_type="",
                        match_status="matched",
                        match_layer=2,
                        match_score=95.0,
                        evidence_block_id=block["id"],
                        evidence_text=text[:200],
                        recommendation="Alias match found in resume content"
                    )
        
        return None
    
    async def _layer3_semantic_match(
        self,
        req_id: str,
        req_text: str,
        req_type: str,
        req_embedding: List[float],
        resume_skills: List[Dict],
        resume_blocks: List[Dict],
        resume_experiences: List[Dict]
    ) -> Optional[MatchResult]:
        """
        Layer 3: Semantic match using pgvector cosine similarity.
        
        Banded approach:
        - > 0.85: Auto-match (return immediately)
        - 0.70-0.85: Send to Layer 4 for context check
        - < 0.70: Not a match
        """
        best_similarity = 0.0
        best_match = None
        best_evidence = None
        
        # Check skills embeddings
        for skill in resume_skills:
            if skill.get("embedding"):
                similarity = self.embedding_service.cosine_similarity(
                    req_embedding, skill["embedding"]
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = skill
                    best_evidence = f"Skill: {skill['name']}"
        
        # Check resume blocks embeddings
        for block in resume_blocks:
            if block.get("embedding"):
                similarity = self.embedding_service.cosine_similarity(
                    req_embedding, block["embedding"]
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = block
                    content = block.get("content", {})
                    text = content.get("text", "") if isinstance(content, dict) else str(content)
                    best_evidence = text[:200]
        
        # Check experience embeddings
        for exp in resume_experiences:
            if exp.get("embedding"):
                similarity = self.embedding_service.cosine_similarity(
                    req_embedding, exp["embedding"]
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = exp
                    best_evidence = f"{exp.get('title', '')} at {exp.get('company', '')}"
        
        if best_similarity < 0.70:
            return None
        
        # Determine match status based on similarity band
        if best_similarity > 0.85:
            match_status = "matched"
            match_score = 90.0
            recommendation = f"Strong semantic match (similarity: {best_similarity:.2f})"
        else:  # 0.70 - 0.85 range
            match_status = "partially_matched"
            match_score = 70.0
            recommendation = f"Potential match (similarity: {best_similarity:.2f}) - needs context verification"
        
        return MatchResult(
            requirement_id=req_id,
            requirement_text=req_text,
            requirement_type=req_type,
            match_status=match_status,
            match_layer=3,
            match_score=match_score,
            evidence_block_id=best_match.get("id") if isinstance(best_match, dict) and "id" in best_match else None,
            evidence_text=best_evidence,
            similarity_score=best_similarity,
            recommendation=recommendation
        )
    
    async def _layer4_context_match(
        self,
        req_text: str,
        req_type: str,
        layer3_result: MatchResult,
        resume_blocks: List[Dict]
    ) -> Optional[MatchResult]:
        """
        Layer 4: LLM-based context/evidence match.
        
        Judges whether the skill is demonstrated (in context) vs merely listed.
        Uses Haiku for cost efficiency.
        """
        if not self.anthropic:
            # Fall back to Layer 3 result if LLM not available
            return layer3_result
        
        # Get relevant resume context
        evidence_text = layer3_result.evidence_text or ""
        
        # Construct prompt for LLM judgment
        prompt = f"""You are evaluating whether a resume demonstrates a required skill or competency.

Job Requirement: {req_text}
Requirement Type: {req_type}

Resume Evidence: {evidence_text}

Question: Does the resume evidence demonstrate practical experience or proficiency with this requirement, or is it merely listed without context?

Respond with a JSON object:
{{
  "demonstrated": true/false,
  "confidence": "high"/"medium"/"low",
  "reasoning": "brief explanation",
  "recommendation": "what to improve if not demonstrated"
}}
"""
        
        try:
            response = self.anthropic.messages.create(
                model=self.haiku_model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Simple JSON parsing (in production, use structured output)
            import json
            result = json.loads(content)
            
            demonstrated = result.get("demonstrated", False)
            confidence = result.get("confidence", "low")
            reasoning = result.get("reasoning", "")
            recommendation = result.get("recommendation", "")
            
            if demonstrated and confidence in ["high", "medium"]:
                return MatchResult(
                    requirement_id=layer3_result.requirement_id,
                    requirement_text=req_text,
                    requirement_type=req_type,
                    match_status="matched",
                    match_layer=4,
                    match_score=85.0 if confidence == "high" else 75.0,
                    evidence_block_id=layer3_result.evidence_block_id,
                    evidence_text=evidence_text,
                    similarity_score=layer3_result.similarity_score,
                    recommendation=f"Demonstrated in context: {reasoning}"
                )
            else:
                return MatchResult(
                    requirement_id=layer3_result.requirement_id,
                    requirement_text=req_text,
                    requirement_type=req_type,
                    match_status="weak_evidence",
                    match_layer=4,
                    match_score=40.0,
                    evidence_block_id=layer3_result.evidence_block_id,
                    evidence_text=evidence_text,
                    similarity_score=layer3_result.similarity_score,
                    recommendation=recommendation or "Add specific examples or context demonstrating this skill"
                )
        
        except Exception as e:
            print(f"Layer 4 LLM error: {e}")
            # Fall back to partially_matched
            return MatchResult(
                requirement_id=layer3_result.requirement_id,
                requirement_text=req_text,
                requirement_type=req_type,
                match_status="partially_matched",
                match_layer=3,
                match_score=layer3_result.match_score,
                evidence_block_id=layer3_result.evidence_block_id,
                evidence_text=layer3_result.evidence_text,
                similarity_score=layer3_result.similarity_score,
                recommendation="Could not verify context - add specific examples"
            )
    
    def _generate_missing_recommendation(self, req_text: str, req_type: str) -> str:
        """Generate recommendation for missing requirements."""
        if req_type == "required_skill":
            return f"Add '{req_text}' to your skills section and provide examples of using it in your experience bullets"
        elif req_type == "preferred_skill":
            return f"Consider adding '{req_text}' if you have experience with it"
        elif req_type == "responsibility":
            return f"Add bullet points demonstrating experience with: {req_text}"
        elif req_type == "education":
            return f"Requirement: {req_text}"
        elif req_type == "experience_years":
            return f"Requirement: {req_text}"
        elif req_type == "certification":
            return f"Consider obtaining: {req_text}"
        elif req_type == "domain_knowledge":
            return f"Highlight any relevant experience in: {req_text}"
        elif req_type == "competency_signal":
            return f"Add examples demonstrating: {req_text}"
        else:
            return f"Add evidence for: {req_text}"
    
    async def match_all_requirements(
        self,
        job_posting_id: str,
        resume_version_id: str,
        user_id: str
    ) -> List[MatchResult]:
        """
        Match all requirements from a job posting against a resume.
        
        Args:
            job_posting_id: ID of job posting
            resume_version_id: ID of resume version
            user_id: User ID for auth
            
        Returns:
            List of MatchResult objects
        """
        # Fetch job requirements
        requirements_response = self.supabase.table("job_requirements").select(
            "*"
        ).eq("job_posting_id", job_posting_id).eq("user_id", user_id).execute()
        
        if not requirements_response.data:
            return []
        
        # Fetch resume data
        skills_response = self.supabase.table("skills").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        blocks_response = self.supabase.table("resume_blocks").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        experiences_response = self.supabase.table("experiences").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        resume_skills = skills_response.data or []
        resume_blocks = blocks_response.data or []
        resume_experiences = experiences_response.data or []
        
        # Match each requirement
        results = []
        for req in requirements_response.data:
            result = await self.match_requirement(
                req, resume_skills, resume_blocks, resume_experiences
            )
            # Set IDs that weren't set in match_requirement
            result.requirement_id = req["id"]
            result.requirement_type = req["requirement_type"]
            results.append(result)
        
        return results
