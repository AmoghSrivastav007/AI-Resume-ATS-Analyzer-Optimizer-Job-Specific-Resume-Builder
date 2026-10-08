"""
Independent Verification for Resume Optimization (Step 7 - Part 3 of Truth Guard).

Uses a SEPARATE model (Haiku) to independently verify proposed edits against the fact ledger.
This is deliberately a different, smaller model than the generator to reduce correlated failures.

Verification is done WITHOUT seeing the generator's reasoning or claimed fact IDs.
The verifier only sees: Fact Ledger + Proposed Text.

Classification (per §8 step 3):
- SUPPORTED: Every claim in proposed text is directly supported by fact ledger
- PARTIALLY_SUPPORTED: Some claims supported, but contains unverifiable statements
- UNSUPPORTED: Contains claims not in fact ledger (hallucination)
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from anthropic import Anthropic


@dataclass
class VerificationResult:
    """Result of independent verification."""
    verification_status: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED
    supported_claims: List[str]  # Claims that are supported
    unsupported_claims: List[str]  # Claims that are NOT supported
    confidence: float  # 0.0-1.0
    reasoning: str  # Explanation of verdict


class IndependentVerifier:
    """
    Independently verifies proposed edits against fact ledger.
    
    Uses Anthropic Haiku (different model from generator) to reduce correlated failures.
    Receives ONLY fact ledger and proposed text - NOT generator's reasoning.
    """
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.haiku_model = os.getenv("ANTHROPIC_HAIKU_MODEL", "claude-3-haiku-20240307")
        self.client = Anthropic(api_key=self.api_key)
    
    async def verify_edit(
        self,
        proposed_text: str,
        fact_ledger: List[Dict[str, Any]],
        original_text: Optional[str] = None
    ) -> VerificationResult:
        """
        Independently verify a proposed edit against the fact ledger.
        
        Args:
            proposed_text: The generated text to verify
            fact_ledger: Complete fact ledger (source of truth)
            original_text: Original text (for context)
            
        Returns:
            VerificationResult with classification
        """
        # Format fact ledger for verification
        fact_ledger_text = self._format_fact_ledger(fact_ledger)
        
        # Build verification prompt (deliberately does NOT include generator's reasoning)
        prompt = self._build_verification_prompt(
            fact_ledger_text,
            proposed_text,
            original_text
        )
        
        try:
            # Call Anthropic Haiku for independent verification
            response = self.client.messages.create(
                model=self.haiku_model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.0  # Zero temperature for consistent verification
            )
            
            # Parse structured response
            content = response.content[0].text
            result_data = self._parse_json_response(content)
            
            # Convert to VerificationResult
            return VerificationResult(
                verification_status=result_data.get("verification_status", "UNSUPPORTED"),
                supported_claims=result_data.get("supported_claims", []),
                unsupported_claims=result_data.get("unsupported_claims", []),
                confidence=result_data.get("confidence", 0.0),
                reasoning=result_data.get("reasoning", "")
            )
        
        except Exception as e:
            print(f"Error in independent verification: {e}")
            # On error, default to UNSUPPORTED (conservative)
            return VerificationResult(
                verification_status="UNSUPPORTED",
                supported_claims=[],
                unsupported_claims=["Verification failed"],
                confidence=0.0,
                reasoning=f"Verification error: {str(e)}"
            )
    
    def _format_fact_ledger(self, fact_ledger: List[Dict[str, Any]]) -> str:
        """Format fact ledger for verification."""
        lines = []
        
        for fact in fact_ledger:
            fact_type = fact["fact_type"]
            fact_text = fact["fact_text"]
            
            # Simple format - just the facts
            lines.append(f"- [{fact_type.upper()}] {fact_text}")
        
        return "\n".join(lines)
    
    def _build_verification_prompt(
        self,
        fact_ledger_text: str,
        proposed_text: str,
        original_text: Optional[str]
    ) -> str:
        """Build the independent verification prompt."""
        original_section = ""
        if original_text:
            original_section = f"""
ORIGINAL TEXT:
{original_text}

"""
        
        return f"""You are an independent fact-checker. Your ONLY job is to verify whether claims in proposed text are supported by the fact ledger.

FACT LEDGER (Source of Truth):
{fact_ledger_text}

{original_section}PROPOSED TEXT TO VERIFY:
{proposed_text}

VERIFICATION RULES:

1. SUPPORTED:
   - EVERY factual claim in proposed text is present in the fact ledger
   - Companies, titles, dates, skills, metrics all match exactly (or are obvious rephrases)
   - No new information added beyond what's in the ledger

2. PARTIALLY_SUPPORTED:
   - SOME claims are supported by the ledger
   - BUT contains vague statements like "excellent communicator" without evidence
   - OR makes inferences that aren't directly stated in facts

3. UNSUPPORTED:
   - Contains ANY company, title, date, skill, or metric NOT in the ledger
   - Fabricates accomplishments or numbers
   - Invents experience or technologies

ANALYSIS APPROACH:
1. Extract every factual claim from the proposed text
2. For each claim, search the fact ledger
3. Classify each claim as supported or unsupported
4. Determine overall verdict based on definitions above

OUTPUT FORMAT (JSON):
{{
  "verification_status": "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED",
  "supported_claims": ["claim 1", "claim 2"],
  "unsupported_claims": ["claim 3"],
  "confidence": 0.95,
  "reasoning": "explanation of verdict"
}}

Be STRICT. If you're unsure, classify as UNSUPPORTED. Return ONLY valid JSON."""
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Try to find JSON in the response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                # Default to UNSUPPORTED if can't parse
                return {
                    "verification_status": "UNSUPPORTED",
                    "supported_claims": [],
                    "unsupported_claims": ["Parse error"],
                    "confidence": 0.0,
                    "reasoning": "Failed to parse verification response"
                }
            
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            return {
                "verification_status": "UNSUPPORTED",
                "supported_claims": [],
                "unsupported_claims": ["Parse error"],
                "confidence": 0.0,
                "reasoning": f"JSON parse error: {str(e)}"
            }


def get_independent_verifier() -> IndependentVerifier:
    """Get or create independent verifier instance."""
    return IndependentVerifier()
