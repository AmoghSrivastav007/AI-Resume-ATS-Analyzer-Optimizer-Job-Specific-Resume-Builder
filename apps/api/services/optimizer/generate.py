"""
Constrained Generation for Resume Optimization (Step 7 - Part 2 of Truth Guard).

Generates resume optimizations using Anthropic Sonnet with strict fact traceability.
Every generated edit MUST be tagged with fact_ledger_entry_id(s) it draws from.

REPHRASING (always allowed):
- Better action verbs
- Tighter phrasing
- Reordering
- Grammar fixes

CONTENT_ADDITION (only if traceable to fact ledger):
- Must reference specific fact_ledger_entry_id
- Cannot invent new companies, titles, dates, skills, or metrics
- Cannot add unsupported claims
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from anthropic import Anthropic


@dataclass
class ProposedEdit:
    """A single proposed edit with fact traceability."""
    block_id: str
    original_text: str
    proposed_text: str
    edit_type: str  # 'rephrase' or 'content_addition'
    fact_ledger_ids: List[str]  # IDs of facts used (empty for rephrase-only)
    reasoning: str  # Why this edit improves the resume
    target_requirement_ids: List[str]  # Job requirements this addresses


class ConstrainedGenerator:
    """
    Generates resume optimizations with strict fact traceability.
    
    Uses Anthropic Sonnet for high-quality generation.
    Every edit is tagged with source facts from the ledger.
    """
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.sonnet_model = os.getenv("ANTHROPIC_SONNET_MODEL", "claude-3-5-sonnet-20241022")
        self.client = Anthropic(api_key=self.api_key)
    
    async def generate_optimizations(
        self,
        resume_blocks: List[Dict[str, Any]],
        fact_ledger: List[Dict[str, Any]],
        job_requirements: List[Dict[str, Any]],
        gap_analysis: Dict[str, Any]
    ) -> List[ProposedEdit]:
        """
        Generate constrained optimizations for resume blocks.
        
        Args:
            resume_blocks: Current resume blocks to optimize
            fact_ledger: Complete fact ledger (source of truth)
            job_requirements: Job requirements to match
            gap_analysis: Gaps from matching analysis
            
        Returns:
            List of proposed edits, each tagged with fact IDs
        """
        # Build fact ledger lookup for the prompt
        fact_ledger_text = self._format_fact_ledger(fact_ledger)
        
        # Build requirements text
        requirements_text = self._format_requirements(job_requirements, gap_analysis)
        
        # Build resume blocks text
        blocks_text = self._format_blocks(resume_blocks)
        
        # Create structured prompt
        prompt = self._build_generation_prompt(
            fact_ledger_text,
            requirements_text,
            blocks_text
        )
        
        try:
            # Call Anthropic Sonnet with structured output
            response = self.client.messages.create(
                model=self.sonnet_model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3  # Lower temperature for more conservative generation
            )
            
            # Parse structured response
            content = response.content[0].text
            
            # Extract JSON from response
            edits_data = self._parse_json_response(content)
            
            # Convert to ProposedEdit objects
            proposed_edits = []
            for edit_data in edits_data.get("edits", []):
                proposed_edits.append(ProposedEdit(
                    block_id=edit_data["block_id"],
                    original_text=edit_data["original_text"],
                    proposed_text=edit_data["proposed_text"],
                    edit_type=edit_data["edit_type"],
                    fact_ledger_ids=edit_data["fact_ledger_ids"],
                    reasoning=edit_data["reasoning"],
                    target_requirement_ids=edit_data.get("target_requirement_ids", [])
                ))
            
            return proposed_edits
        
        except Exception as e:
            print(f"Error in constrained generation: {e}")
            return []
    
    def _format_fact_ledger(self, fact_ledger: List[Dict[str, Any]]) -> str:
        """Format fact ledger for prompt."""
        lines = ["=== FACT LEDGER (Source of Truth) ===\n"]
        
        for fact in fact_ledger:
            fact_id = fact["id"]
            fact_type = fact["fact_type"]
            fact_text = fact["fact_text"]
            metadata = fact.get("metadata", {})
            
            lines.append(f"[ID: {fact_id}] [{fact_type.upper()}] {fact_text}")
            if metadata:
                lines.append(f"  Context: {json.dumps(metadata)}")
        
        return "\n".join(lines)
    
    def _format_requirements(
        self,
        job_requirements: List[Dict[str, Any]],
        gap_analysis: Dict[str, Any]
    ) -> str:
        """Format job requirements and gaps."""
        lines = ["=== JOB REQUIREMENTS & GAPS ===\n"]
        
        # Focus on missing and weak evidence requirements
        gaps = gap_analysis.get("gaps", {})
        
        critical = gaps.get("critical", [])
        if critical:
            lines.append("CRITICAL GAPS (Missing Required Skills):")
            for gap in critical:
                lines.append(f"  - {gap['requirement']}")
                lines.append(f"    Type: {gap['type']}")
        
        important = gaps.get("important", [])
        if important:
            lines.append("\nIMPORTANT GAPS (Missing Preferred/Certs):")
            for gap in important[:5]:  # Limit to top 5
                lines.append(f"  - {gap['requirement']}")
        
        needs_improvement = gaps.get("needs_improvement", [])
        if needs_improvement:
            lines.append("\nNEEDS STRONGER EVIDENCE:")
            for gap in needs_improvement[:5]:
                lines.append(f"  - {gap['requirement']}")
        
        return "\n".join(lines)
    
    def _format_blocks(self, resume_blocks: List[Dict[str, Any]]) -> str:
        """Format resume blocks for optimization."""
        lines = ["=== CURRENT RESUME BLOCKS ===\n"]
        
        for block in resume_blocks:
            block_id = block["id"]
            content = block.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            block_type = block.get("block_type", "unknown")
            
            lines.append(f"[Block ID: {block_id}] [{block_type}]")
            lines.append(f"  {text}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_generation_prompt(
        self,
        fact_ledger_text: str,
        requirements_text: str,
        blocks_text: str
    ) -> str:
        """Build the constrained generation prompt."""
        return f"""You are an expert resume optimizer. Your task is to improve resume bullet points to better match job requirements while maintaining ABSOLUTE FACTUAL ACCURACY.

{fact_ledger_text}

{requirements_text}

{blocks_text}

CRITICAL RULES:

1. FACT TRACEABILITY:
   - Every claim in your optimized text MUST be traceable to a specific Fact Ledger entry
   - You MUST tag each edit with the fact_ledger_entry_id(s) it uses
   - If a fact is not in the ledger, you CANNOT add it

2. ALLOWED CHANGES (REPHRASING):
   - Use stronger action verbs
   - Make phrasing more concise
   - Improve sentence structure
   - Fix grammar/punctuation
   - Reorder information
   - These require NO fact_ledger_ids (edit_type: "rephrase")

3. ALLOWED ADDITIONS (CONTENT_ADDITION):
   - Highlight existing facts more prominently
   - Connect existing facts to job requirements
   - Add context from fact ledger metadata
   - These MUST include fact_ledger_ids (edit_type: "content_addition")

4. STRICTLY FORBIDDEN:
   - DO NOT invent companies, titles, dates, or metrics
   - DO NOT add skills/technologies not in the fact ledger
   - DO NOT fabricate accomplishments or numbers
   - DO NOT make unsupported claims
   - DO NOT change company names, job titles, or date ranges

5. ADDRESSING GAPS:
   - For MISSING requirements: DO NOT fabricate experience
   - Instead: Suggest highlighting related existing skills
   - Or: Note that this is a gap (we'll surface to user separately)

OUTPUT FORMAT (JSON):
{{
  "edits": [
    {{
      "block_id": "block-uuid",
      "original_text": "original text here",
      "proposed_text": "optimized text here",
      "edit_type": "rephrase" or "content_addition",
      "fact_ledger_ids": ["fact-id-1", "fact-id-2"],  // empty array for rephrase-only
      "reasoning": "why this edit helps",
      "target_requirement_ids": ["req-id-1"]  // which requirements this addresses
    }}
  ]
}}

Generate optimizations now. Focus on blocks with weak verbs, vague statements, or missing metrics that CAN be improved with facts from the ledger.

Return ONLY valid JSON, no other text."""
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Try to find JSON in the response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                return {"edits": []}
            
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Content: {content[:500]}")
            return {"edits": []}


def get_constrained_generator() -> ConstrainedGenerator:
    """Get or create constrained generator instance."""
    return ConstrainedGenerator()
