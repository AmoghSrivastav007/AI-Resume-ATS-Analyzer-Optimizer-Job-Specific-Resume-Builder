"""
Resume Optimizer with Truth Guard (Step 7).

Truth Guard: 5-step hallucination prevention pipeline.

1. Fact Ledger: Already populated in Step 2 (companies, titles, dates, skills, metrics, certs)
2. Constrained Generation: Sonnet generates edits tagged with fact IDs
3. Independent Verification: Haiku (different model) independently classifies as SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED
4. Deterministic Guardrails: Hard blocks for company/title/date/skill/number changes
5. Pipeline: generation → verification → guardrails → status assignment

Verification Status:
- SUPPORTED + passed guardrails = auto-approved
- PARTIALLY_SUPPORTED = requires user confirmation
- UNSUPPORTED or failed guardrails = auto-rejected, regenerate
"""

from .generate import ConstrainedGenerator, ProposedEdit, get_constrained_generator
from .verify import IndependentVerifier, VerificationResult, get_independent_verifier
from .guardrails import DeterministicGuardrails, GuardrailResult, GuardrailViolation, get_deterministic_guardrails

__all__ = [
    "ConstrainedGenerator",
    "ProposedEdit",
    "get_constrained_generator",
    "IndependentVerifier",
    "VerificationResult",
    "get_independent_verifier",
    "DeterministicGuardrails",
    "GuardrailResult",
    "GuardrailViolation",
    "get_deterministic_guardrails",
]
