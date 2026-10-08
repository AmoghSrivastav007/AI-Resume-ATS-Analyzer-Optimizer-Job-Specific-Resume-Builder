"""
Optimization Service - Wires the complete Truth Guard pipeline (Step 7).

Pipeline:
1. Fetch fact ledger, resume blocks, job requirements, gap analysis
2. Generate optimizations (Sonnet) with fact traceability
3. Verify each edit independently (Haiku)
4. Run deterministic guardrails on each edit
5. Assign status based on results:
   - SUPPORTED + guardrails passed = 'supported' (auto-approved)
   - PARTIALLY_SUPPORTED = 'partially_supported' (requires confirmation)
   - UNSUPPORTED or guardrails failed = auto-rejected, logged, regenerate that section

Zero tolerance for hallucinations.
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from supabase import Client

from services.optimizer import (
    get_constrained_generator,
    get_independent_verifier,
    get_deterministic_guardrails,
    ProposedEdit,
    VerificationResult,
    GuardrailResult
)


class OptimizationService:
    """
    Complete optimization pipeline with Truth Guard.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.generator = get_constrained_generator()
        self.verifier = get_independent_verifier()
        self.guardrails = get_deterministic_guardrails(supabase_client)
    
    async def generate_optimizations(
        self,
        resume_version_id: str,
        job_posting_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate optimizations for a resume against a job posting.
        
        Full Truth Guard pipeline:
        1. Fetch fact ledger + resume blocks + job requirements + gap analysis
        2. Generate (Sonnet)
        3. Verify (Haiku)
        4. Check guardrails (deterministic)
        5. Store with appropriate status
        
        Args:
            resume_version_id: Resume version ID
            job_posting_id: Job posting ID
            user_id: User ID
            
        Returns:
            Summary of generated optimizations
        """
        # Step 1: Fetch all required data
        fact_ledger = await self._fetch_fact_ledger(resume_version_id, user_id)
        resume_blocks = await self._fetch_resume_blocks(resume_version_id, user_id)
        job_requirements = await self._fetch_job_requirements(job_posting_id, user_id)
        gap_analysis = await self._fetch_gap_analysis(resume_version_id, job_posting_id, user_id)
        
        if not fact_ledger:
            raise ValueError("No fact ledger found - resume must be parsed first")
        
        if not job_requirements:
            raise ValueError("No job requirements found - job posting must be extracted first")
        
        # Step 2: Generate optimizations (Sonnet with fact traceability)
        print(f"Generating optimizations with {len(fact_ledger)} facts in ledger...")
        proposed_edits = await self.generator.generate_optimizations(
            resume_blocks=resume_blocks,
            fact_ledger=fact_ledger,
            job_requirements=job_requirements,
            gap_analysis=gap_analysis
        )
        
        print(f"Generated {len(proposed_edits)} proposed edits")
        
        # Step 3-5: Verify, check guardrails, and store
        stored_optimizations = []
        rejected_count = 0
        
        for edit in proposed_edits:
            # Find original block
            original_block = next((b for b in resume_blocks if b["id"] == edit.block_id), None)
            if not original_block:
                print(f"Warning: Block {edit.block_id} not found")
                continue
            
            # Step 3: Independent verification (Haiku)
            verification = await self.verifier.verify_edit(
                proposed_text=edit.proposed_text,
                fact_ledger=fact_ledger,
                original_text=edit.original_text
            )
            
            # Step 4: Deterministic guardrails
            guardrail_result = await self.guardrails.check_guardrails(
                original_text=edit.original_text,
                proposed_text=edit.proposed_text,
                fact_ledger=fact_ledger,
                user_id=user_id
            )
            
            # Step 5: Determine final status
            final_status = self._determine_status(verification, guardrail_result)
            
            if final_status == "rejected":
                # Auto-rejected - log and skip (don't show to user)
                rejected_count += 1
                self._log_rejection(edit, verification, guardrail_result, user_id)
                print(f"Rejected edit for block {edit.block_id}: {verification.verification_status}, guardrails: {guardrail_result.passed}")
                continue
            
            # Store optimization
            optimization = await self._store_optimization(
                resume_version_id=resume_version_id,
                user_id=user_id,
                block_id=edit.block_id,
                edit=edit,
                verification=verification,
                guardrail_result=guardrail_result,
                final_status=final_status
            )
            
            stored_optimizations.append(optimization)
        
        return {
            "resume_version_id": resume_version_id,
            "job_posting_id": job_posting_id,
            "total_generated": len(proposed_edits),
            "stored": len(stored_optimizations),
            "auto_rejected": rejected_count,
            "supported": len([o for o in stored_optimizations if o["verification_status"] == "supported"]),
            "partially_supported": len([o for o in stored_optimizations if o["verification_status"] == "partially_supported"]),
            "optimizations": stored_optimizations
        }
    
    async def _fetch_fact_ledger(self, resume_version_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Fetch complete fact ledger for resume."""
        response = self.supabase.table("fact_ledger_entries").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        return response.data or []
    
    async def _fetch_resume_blocks(self, resume_version_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Fetch all resume blocks."""
        response = self.supabase.table("resume_blocks").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).order(
            "sort_order"
        ).execute()
        
        return response.data or []
    
    async def _fetch_job_requirements(self, job_posting_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Fetch job requirements."""
        response = self.supabase.table("job_requirements").select(
            "*"
        ).eq("job_posting_id", job_posting_id).eq("user_id", user_id).execute()
        
        return response.data or []
    
    async def _fetch_gap_analysis(
        self,
        resume_version_id: str,
        job_posting_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Fetch gap analysis from matching service."""
        # Find the most recent matching analysis
        response = self.supabase.table("resume_analyses").select(
            "summary"
        ).eq("resume_version_id", resume_version_id).eq(
            "user_id", user_id
        ).eq("analysis_type", "jd_match").order(
            "created_at", desc=True
        ).limit(1).execute()
        
        if response.data:
            summary = response.data[0].get("summary", {})
            return summary.get("gap_analysis", {})
        
        return {}
    
    def _determine_status(
        self,
        verification: VerificationResult,
        guardrail_result: GuardrailResult
    ) -> str:
        """
        Determine final status based on verification and guardrails.
        
        Rules:
        - UNSUPPORTED → rejected
        - Guardrails failed → rejected
        - SUPPORTED + guardrails passed → supported (auto-approved)
        - PARTIALLY_SUPPORTED + guardrails passed → partially_supported (requires confirmation)
        """
        # Hard block: guardrails failed
        if not guardrail_result.passed:
            return "rejected"
        
        # Hard block: unsupported by verifier
        if verification.verification_status == "UNSUPPORTED":
            return "rejected"
        
        # Supported and passed guardrails → auto-approve
        if verification.verification_status == "SUPPORTED":
            return "supported"
        
        # Partially supported → requires user confirmation
        if verification.verification_status == "PARTIALLY_SUPPORTED":
            return "partially_supported"
        
        # Default to rejected (conservative)
        return "rejected"
    
    async def _store_optimization(
        self,
        resume_version_id: str,
        user_id: str,
        block_id: str,
        edit: ProposedEdit,
        verification: VerificationResult,
        guardrail_result: GuardrailResult,
        final_status: str
    ) -> Dict[str, Any]:
        """Store optimization in database."""
        optimization_id = str(uuid4())
        
        optimization_data = {
            "id": optimization_id,
            "user_id": user_id,
            "resume_version_id": resume_version_id,
            "issue_id": None,  # Not linked to specific issue
            "optimization_type": "rewrite",
            "status": "proposed",  # User hasn't decided yet
            "original_content": {
                "block_id": block_id,
                "text": edit.original_text,
                "type": edit.edit_type
            },
            "proposed_content": {
                "text": edit.proposed_text,
                "fact_ledger_ids": edit.fact_ledger_ids,
                "reasoning": edit.reasoning,
                "target_requirement_ids": edit.target_requirement_ids,
                "verification_status": final_status,
                "verification_result": {
                    "status": verification.verification_status,
                    "confidence": verification.confidence,
                    "reasoning": verification.reasoning,
                    "supported_claims": verification.supported_claims,
                    "unsupported_claims": verification.unsupported_claims
                },
                "guardrail_result": {
                    "passed": guardrail_result.passed,
                    "violations": [
                        {
                            "rule": v.rule,
                            "severity": v.severity,
                            "description": v.description,
                            "original": v.original_value,
                            "proposed": v.proposed_value
                        }
                        for v in guardrail_result.violations
                    ]
                }
            }
        }
        
        response = self.supabase.table("optimizations").insert(optimization_data).execute()
        
        if response.data:
            return {
                **response.data[0],
                "verification_status": final_status
            }
        
        return {}
    
    def _log_rejection(
        self,
        edit: ProposedEdit,
        verification: VerificationResult,
        guardrail_result: GuardrailResult,
        user_id: str
    ):
        """Log rejected optimization for monitoring."""
        # In production, send to monitoring service (Sentry, DataDog, etc.)
        print(f"REJECTED OPTIMIZATION (hallucination detected):")
        print(f"  User: {user_id}")
        print(f"  Block: {edit.block_id}")
        print(f"  Verification: {verification.verification_status}")
        print(f"  Unsupported claims: {verification.unsupported_claims}")
        print(f"  Guardrails passed: {guardrail_result.passed}")
        if not guardrail_result.passed:
            print(f"  Violations: {[v.description for v in guardrail_result.violations]}")
    
    async def get_optimizations(
        self,
        resume_version_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all optimizations for a resume."""
        response = self.supabase.table("optimizations").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq(
            "user_id", user_id
        ).eq("status", "proposed").execute()
        
        return response.data or []
    
    async def apply_optimization(
        self,
        optimization_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Apply an optimization (user accepted)."""
        # Update optimization status
        response = self.supabase.table("optimizations").update({
            "status": "applied",
            "applied_at": "now()"
        }).eq("id", optimization_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise ValueError("Optimization not found")
        
        # TODO: Actually update the resume_block with new content
        # This would create a new version or update the current block
        
        return response.data[0]
    
    async def reject_optimization(
        self,
        optimization_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Reject an optimization (user declined)."""
        response = self.supabase.table("optimizations").update({
            "status": "rejected"
        }).eq("id", optimization_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise ValueError("Optimization not found")
        
        return response.data[0]
