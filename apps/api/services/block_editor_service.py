"""
Block Editor Service (Step 8)

Handles block editing operations with Truth Guard integration for AI rewrites.
All AI-generated changes go through the same hallucination prevention pipeline as Step 7.
"""

import os
from typing import Dict, Any, List, Optional
from uuid import uuid4
from supabase import Client
from anthropic import Anthropic

from services.optimizer import (
    get_independent_verifier,
    get_deterministic_guardrails
)


class BlockEditorService:
    """
    Service for editing resume blocks.
    
    Provides:
    - Manual editing (PATCH block)
    - AI-powered rewrites with Truth Guard
    - Block creation/deletion
    - Reordering within sections
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if self.anthropic_key:
            self.anthropic = Anthropic(api_key=self.anthropic_key)
            self.haiku_model = os.getenv("ANTHROPIC_HAIKU_MODEL", "claude-3-haiku-20240307")
            self.sonnet_model = os.getenv("ANTHROPIC_SONNET_MODEL", "claude-3-5-sonnet-20241022")
    
    async def update_block(
        self,
        block_id: str,
        content: Dict[str, Any],
        block_type: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update a block with manual edits.
        
        This is for direct user typing/editing, NOT AI-generated changes.
        """
        update_data = {
            "content": content,
            "updated_at": "now()"
        }
        
        if block_type:
            update_data["block_type"] = block_type
        
        response = self.supabase.table("resume_blocks").update(
            update_data
        ).eq("id", block_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise ValueError("Block not found or update failed")
        
        return response.data[0]
    
    async def ai_rewrite_block(
        self,
        block_id: str,
        instruction: str,
        context: Optional[str],
        user_id: str,
        resume_version_id: str
    ) -> Dict[str, Any]:
        """
        AI-powered rewrite of a block with Truth Guard.
        
        Process:
        1. Fetch block and fact ledger
        2. Generate rewrite with Haiku (simple) or Sonnet (complex)
        3. Verify with independent verifier (Haiku)
        4. Check deterministic guardrails
        5. Return proposed rewrite with verification status
        
        Args:
            block_id: Block to rewrite
            instruction: shorten|expand|fix_grammar|improve
            context: Optional additional context
            user_id: User ID
            resume_version_id: Resume version ID
            
        Returns:
            Dict with original_text, proposed_text, verification_status, etc.
        """
        # Fetch block
        block_response = self.supabase.table("resume_blocks").select(
            "*"
        ).eq("id", block_id).eq("user_id", user_id).execute()
        
        if not block_response.data:
            raise ValueError("Block not found")
        
        block = block_response.data[0]
        original_text = block["content"].get("text", "")
        
        if not original_text:
            raise ValueError("Block has no text content")
        
        # Fetch fact ledger for this resume version
        fact_ledger = await self._fetch_fact_ledger(resume_version_id, user_id)
        
        # Determine model based on instruction complexity
        model = self.haiku_model if instruction in ["shorten", "fix_grammar"] else self.sonnet_model
        
        # Generate rewrite
        proposed_text = await self._generate_rewrite(
            original_text=original_text,
            instruction=instruction,
            context=context,
            fact_ledger=fact_ledger,
            model=model
        )
        
        # Independent verification (Step 7)
        verifier = get_independent_verifier()
        verification_result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text=original_text
        )
        
        # Deterministic guardrails (Step 7)
        guardrails = get_deterministic_guardrails(self.supabase)
        guardrail_result = await guardrails.check_guardrails(
            original_text=original_text,
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            user_id=user_id
        )
        
        # Determine status
        warnings = []
        
        if not guardrail_result.passed:
            # Guardrail violations
            warnings.append("Guardrail checks failed - proposed changes may alter critical facts")
            for violation in guardrail_result.violations:
                warnings.append(f"{violation.rule}: {violation.description}")
        
        if verification_result.verification_status == "UNSUPPORTED":
            warnings.append("Verification failed - proposed text contains unsupported claims")
        
        if verification_result.verification_status == "PARTIALLY_SUPPORTED":
            warnings.append("Some claims are vague or not fully supported - user confirmation required")
        
        return {
            "original_text": original_text,
            "proposed_text": proposed_text,
            "verification_status": verification_result.verification_status.lower(),
            "guardrails_passed": guardrail_result.passed,
            "reasoning": verification_result.reasoning,
            "warnings": warnings,
            "supported_claims": verification_result.supported_claims,
            "unsupported_claims": verification_result.unsupported_claims
        }
    
    async def apply_rewrite(
        self,
        block_id: str,
        proposed_text: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Apply an AI-generated rewrite to a block.
        
        Updates the block content with the proposed text.
        """
        # Fetch current block
        block_response = self.supabase.table("resume_blocks").select(
            "*"
        ).eq("id", block_id).eq("user_id", user_id).execute()
        
        if not block_response.data:
            raise ValueError("Block not found")
        
        block = block_response.data[0]
        
        # Update content
        new_content = {**block["content"], "text": proposed_text}
        
        response = self.supabase.table("resume_blocks").update({
            "content": new_content,
            "updated_at": "now()"
        }).eq("id", block_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise ValueError("Failed to apply rewrite")
        
        return response.data[0]
    
    async def create_block(
        self,
        section_id: str,
        resume_version_id: str,
        content: Dict[str, Any],
        block_type: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Create a new block in a section."""
        # Get max sort_order in section
        blocks_response = self.supabase.table("resume_blocks").select(
            "sort_order"
        ).eq("section_id", section_id).order(
            "sort_order", desc=True
        ).limit(1).execute()
        
        max_sort_order = blocks_response.data[0]["sort_order"] if blocks_response.data else 0
        
        # Create new block
        new_block = {
            "id": str(uuid4()),
            "resume_version_id": resume_version_id,
            "section_id": section_id,
            "user_id": user_id,
            "block_type": block_type,
            "content": content,
            "sort_order": max_sort_order + 1
        }
        
        response = self.supabase.table("resume_blocks").insert(new_block).execute()
        
        if not response.data:
            raise ValueError("Failed to create block")
        
        return response.data[0]
    
    async def reorder_blocks(
        self,
        section_id: str,
        block_ids: List[str],
        user_id: str
    ):
        """
        Reorder blocks within a section.
        
        Updates sort_order for each block based on position in block_ids list.
        """
        for index, block_id in enumerate(block_ids):
            self.supabase.table("resume_blocks").update({
                "sort_order": index
            }).eq("id", block_id).eq(
                "section_id", section_id
            ).eq("user_id", user_id).execute()
    
    async def _fetch_fact_ledger(
        self,
        resume_version_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch fact ledger for a resume version."""
        response = self.supabase.table("fact_ledger_entries").select(
            "*"
        ).eq("resume_version_id", resume_version_id).eq("user_id", user_id).execute()
        
        return response.data or []
    
    async def _generate_rewrite(
        self,
        original_text: str,
        instruction: str,
        context: Optional[str],
        fact_ledger: List[Dict[str, Any]],
        model: str
    ) -> str:
        """
        Generate a rewrite using Anthropic API.
        
        Constrained to prevent hallucinations:
        - Rephrasing allowed
        - Content additions only from fact ledger
        - No fabrication of new claims
        """
        # Build fact ledger text
        fact_ledger_text = self._format_fact_ledger(fact_ledger)
        
        # Build instruction-specific prompt
        instruction_prompts = {
            "shorten": "Make this text more concise while preserving all key information.",
            "expand": "Add more detail to this text, using ONLY facts from the fact ledger below. Do not invent new information.",
            "fix_grammar": "Fix any grammar, punctuation, or spelling errors in this text. Do not change the meaning.",
            "improve": "Improve this text with stronger action verbs and better phrasing. Do not add new information not supported by the fact ledger."
        }
        
        instruction_text = instruction_prompts.get(instruction, instruction_prompts["improve"])
        
        prompt = f"""You are a professional resume editor. Your task is to rewrite the following text according to the instruction.

CRITICAL RULES:
1. You may REPHRASE the text (better words, tighter sentences, improved structure)
2. You may ONLY add information that is in the fact ledger below
3. You must NOT invent new companies, titles, dates, skills, metrics, or achievements
4. You must NOT fabricate information not in the fact ledger

FACT LEDGER (Source of Truth):
{fact_ledger_text}

INSTRUCTION:
{instruction_text}

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

ORIGINAL TEXT:
{original_text}

REWRITTEN TEXT (following all rules above):"""
        
        try:
            response = self.anthropic.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3  # Conservative for factual accuracy
            )
            
            return response.content[0].text.strip()
        
        except Exception as e:
            print(f"Error in AI rewrite generation: {e}")
            raise ValueError(f"Failed to generate rewrite: {str(e)}")
    
    def _format_fact_ledger(self, fact_ledger: List[Dict[str, Any]]) -> str:
        """Format fact ledger for prompt."""
        if not fact_ledger:
            return "(No facts in ledger - rephrase only, do not add new information)"
        
        lines = []
        for fact in fact_ledger:
            fact_type = fact["fact_type"]
            fact_text = fact["fact_text"]
            lines.append(f"- [{fact_type.upper()}] {fact_text}")
        
        return "\n".join(lines)


def get_block_editor_service(supabase_client: Client) -> BlockEditorService:
    """Get or create block editor service instance."""
    return BlockEditorService(supabase_client)
