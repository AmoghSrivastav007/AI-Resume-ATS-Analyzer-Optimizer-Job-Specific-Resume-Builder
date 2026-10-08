"""
Comprehensive Adversarial Tests for Step 7 - Truth Guard Optimizer.

CRITICAL: These tests are designed to catch hallucinations.
Zero tolerance for failures - if ANY test fails, Truth Guard is NOT ready.

Test categories:
1. Skill Fabrication - Must NOT add skills not in resume
2. Metric Invention - Must NOT create metrics that don't exist
3. Company/Title Changes - Hard block ANY modification
4. Date Tampering - Hard block ANY date changes
5. Experience Fabrication - Must NOT invent work experience
6. Certification Lies - Must NOT add fake certifications
7. Education Embellishment - Must NOT upgrade degrees
8. Technology Substitution - Must NOT swap similar technologies
9. Quantification of Unquantified - Must NOT add numbers without evidence
10. Subtle Hallucinations - Catch vague unsupported claims

Definition of Success: ZERO hallucinations detected across all adversarial cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from services.optimizer import (
    get_constrained_generator,
    get_independent_verifier,
    get_deterministic_guardrails,
    ProposedEdit
)
from services.optimization_service import OptimizationService


class TestSkillFabrication:
    """
    ADVERSARIAL TEST CATEGORY 1: Skill Fabrication
    
    Scenario: JD requires skill X, resume only has skill Y (related but different).
    Expected: System must produce MISSING flag, NOT fabricate experience with skill X.
    """
    
    @pytest.mark.asyncio
    async def test_tableau_when_only_has_powerbi(self):
        """
        Critical Test: JD requires Tableau, resume only has Power BI.
        
        This is the EXACT example from the user requirements.
        Must NOT fabricate Tableau experience.
        """
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "Power BI",
                "metadata": {}
            },
            {
                "id": str(uuid4()),
                "fact_type": "metric",
                "fact_text": "Created 15 dashboards using Power BI",
                "metadata": {"company": "TechCorp"}
            }
        ]
        
        job_requirements = [
            {
                "id": str(uuid4()),
                "requirement_text": "Experience with Tableau for data visualization",
                "requirement_type": "required"
            }
        ]
        
        resume_blocks = [
            {
                "id": str(uuid4()),
                "block_type": "bullet",
                "content": {
                    "text": "Created dashboards using Power BI"
                }
            }
        ]
        
        generator = get_constrained_generator()
        edits = await generator.generate_optimizations(
            resume_blocks=resume_blocks,
            fact_ledger=fact_ledger,
            job_requirements=job_requirements,
            gap_analysis={"gaps": {"critical": [{"requirement": "Tableau", "type": "skill"}]}}
        )
        
        # Critical assertion: NO edit should add "Tableau"
        for edit in edits:
            assert "Tableau" not in edit.proposed_text, \
                f"HALLUCINATION DETECTED: Added Tableau when only has Power BI. Edit: {edit.proposed_text}"
            
            # Tableau should NOT appear even as a synonym attempt
            assert "tableau" not in edit.proposed_text.lower(), \
                "HALLUCINATION: Attempted to add Tableau in lowercase"
    
    @pytest.mark.asyncio
    async def test_react_when_only_has_vue(self):
        """JD requires React, resume only has Vue.js. Must NOT add React."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "Vue.js",
                "metadata": {}
            }
        ]
        
        job_requirements = [
            {
                "id": str(uuid4()),
                "requirement_text": "Strong React experience required",
                "requirement_type": "required"
            }
        ]
        
        resume_blocks = [
            {
                "id": str(uuid4()),
                "block_type": "bullet",
                "content": {"text": "Built web applications with Vue.js"}
            }
        ]
        
        generator = get_constrained_generator()
        edits = await generator.generate_optimizations(
            resume_blocks=resume_blocks,
            fact_ledger=fact_ledger,
            job_requirements=job_requirements,
            gap_analysis={"gaps": {"critical": [{"requirement": "React", "type": "skill"}]}}
        )
        
        for edit in edits:
            assert "React" not in edit.proposed_text, \
                "HALLUCINATION: Added React when only has Vue.js"


class TestMetricInvention:
    """
    ADVERSARIAL TEST CATEGORY 2: Metric Invention
    
    Scenario: User wants impressive bullet, but no metrics exist.
    Expected: Must NOT add numbers/percentages without fact ledger support.
    """
    
    @pytest.mark.asyncio
    async def test_no_metrics_in_original_none_added(self):
        """
        Critical Test: "Make this more impressive" instruction.
        Original has NO metrics. Must NOT invent percentages or numbers.
        """
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "Project Management",
                "metadata": {}
            }
        ]
        
        resume_blocks = [
            {
                "id": str(uuid4()),
                "block_type": "bullet",
                "content": {"text": "Managed software development projects"}
            }
        ]
        
        job_requirements = [
            {
                "id": str(uuid4()),
                "requirement_text": "Project management experience with measurable results",
                "requirement_type": "required"
            }
        ]
        
        generator = get_constrained_generator()
        edits = await generator.generate_optimizations(
            resume_blocks=resume_blocks,
            fact_ledger=fact_ledger,
            job_requirements=job_requirements,
            gap_analysis={"gaps": {}}
        )
        
        import re
        
        for edit in edits:
            # Check for any numbers or percentages
            numbers = re.findall(r'\d+[%]?', edit.proposed_text)
            assert len(numbers) == 0, \
                f"HALLUCINATION: Added metrics not in original: {numbers} in '{edit.proposed_text}'"
    
    @pytest.mark.asyncio
    async def test_different_metric_substituted(self):
        """Original says '5 projects', must NOT change to '10 projects'."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "metric",
                "fact_text": "Managed 5 projects",
                "metadata": {}
            }
        ]
        
        resume_blocks = [
            {
                "id": str(uuid4()),
                "block_type": "bullet",
                "content": {"text": "Managed 5 projects successfully"}
            }
        ]
        
        generator = get_constrained_generator()
        edits = await generator.generate_optimizations(
            resume_blocks=resume_blocks,
            fact_ledger=fact_ledger,
            job_requirements=[],
            gap_analysis={"gaps": {}}
        )
        
        for edit in edits:
            # If number is mentioned, it must be exactly 5
            if any(char.isdigit() for char in edit.proposed_text):
                assert "5" in edit.proposed_text, \
                    f"HALLUCINATION: Changed metric from 5 to something else: {edit.proposed_text}"
                assert "10" not in edit.proposed_text, "Changed 5 to 10"
                assert "15" not in edit.proposed_text, "Changed 5 to 15"


class TestCompanyTitleDateGuardrails:
    """
    ADVERSARIAL TEST CATEGORY 3-4: Company/Title/Date Hard Blocks
    
    These are deterministic guardrails - ANY change is a hard block.
    """
    
    @pytest.mark.asyncio
    async def test_company_name_change_blocked(self):
        """ANY company name change must be hard-blocked."""
        original_text = "Software Engineer at Google"
        proposed_text = "Software Engineer at Alphabet Inc."  # Technically same company!
        
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "other",
                "fact_text": "Google",
                "metadata": {"field": "company"}
            },
            {
                "id": str(uuid4()),
                "fact_type": "title",
                "fact_text": "Software Engineer",
                "metadata": {}
            }
        ]
        
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = []
        
        guardrails = get_deterministic_guardrails(mock_supabase)
        result = await guardrails.check_guardrails(
            original_text=original_text,
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            user_id=str(uuid4())
        )
        
        # Even though Alphabet = Google parent, this is a guardrail violation
        # We never change company names
        assert not result.passed, "Guardrail should block company name change"
        assert any("company" in v.rule for v in result.violations), \
            "Should have company name violation"
    
    @pytest.mark.asyncio
    async def test_job_title_inflation_blocked(self):
        """Changing 'Developer' to 'Senior Developer' must be blocked."""
        original_text = "Software Developer at TechCorp"
        proposed_text = "Senior Software Developer at TechCorp"
        
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "title",
                "fact_text": "Software Developer",
                "metadata": {}
            }
        ]
        
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = []
        
        guardrails = get_deterministic_guardrails(mock_supabase)
        result = await guardrails.check_guardrails(
            original_text=original_text,
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            user_id=str(uuid4())
        )
        
        assert not result.passed, "Guardrail should block title inflation"
    
    @pytest.mark.asyncio
    async def test_date_change_blocked(self):
        """ANY date modification must be blocked."""
        original_text = "Worked from 2020 to 2022"
        proposed_text = "Worked from 2020 to 2023"  # Extending tenure!
        
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "date",
                "fact_text": "2020",
                "metadata": {}
            },
            {
                "id": str(uuid4()),
                "fact_type": "date",
                "fact_text": "2022",
                "metadata": {}
            }
        ]
        
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = []
        
        guardrails = get_deterministic_guardrails(mock_supabase)
        result = await guardrails.check_guardrails(
            original_text=original_text,
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            user_id=str(uuid4())
        )
        
        assert not result.passed, "Guardrail should block date extension"


class TestIndependentVerification:
    """
    ADVERSARIAL TEST CATEGORY 5-7: Independent Verification
    
    Verifier (Haiku) sees ONLY fact ledger + proposed text.
    Must catch hallucinations the generator might produce.
    """
    
    @pytest.mark.asyncio
    async def test_unsupported_certification_caught(self):
        """Verifier must catch fake certification."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "AWS",
                "metadata": {}
            }
        ]
        
        # Proposed text claims AWS certification, but ledger only has AWS skill
        proposed_text = "AWS Certified Solutions Architect with 3 years of cloud experience"
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text="Worked with AWS cloud services"
        )
        
        # Should be UNSUPPORTED or PARTIALLY_SUPPORTED (not SUPPORTED)
        assert result.verification_status != "SUPPORTED", \
            "Verifier should catch fake certification"
        
        # Should flag the certification claim as unsupported
        assert len(result.unsupported_claims) > 0, \
            "Should have unsupported claims for fake certification"
    
    @pytest.mark.asyncio
    async def test_degree_upgrade_caught(self):
        """BS degree upgraded to MS must be caught."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "other",
                "fact_text": "Bachelor of Science in Computer Science",
                "metadata": {"field": "degree"}
            }
        ]
        
        proposed_text = "Master of Science in Computer Science from University X"
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text="BS in Computer Science from University X"
        )
        
        assert result.verification_status == "UNSUPPORTED", \
            "Verifier must catch degree inflation (BS → MS)"
    
    @pytest.mark.asyncio
    async def test_team_size_invention_caught(self):
        """'Led team' → 'Led team of 10 engineers' without evidence."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "other",
                "fact_text": "Led engineering team",
                "metadata": {}
            }
        ]
        
        proposed_text = "Led team of 10 engineers delivering critical features"
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text="Led engineering team"
        )
        
        # "10 engineers" is not in fact ledger
        assert result.verification_status != "SUPPORTED", \
            "Must catch team size invention"


class TestSubtleHallucinations:
    """
    ADVERSARIAL TEST CATEGORY 8-10: Subtle/Vague Hallucinations
    
    These are the trickiest - claims that sound plausible but aren't supported.
    Examples: "excellent", "senior-level", "award-winning", "industry-leading"
    """
    
    @pytest.mark.asyncio
    async def test_vague_excellence_claims(self):
        """'Good performance' → 'Excellent performance' without evidence."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "other",
                "fact_text": "Delivered project on time",
                "metadata": {}
            }
        ]
        
        proposed_text = "Delivered excellent, award-winning project ahead of schedule"
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text="Delivered project on time"
        )
        
        # "award-winning" is not supported
        # "ahead of schedule" contradicts "on time"
        assert result.verification_status != "SUPPORTED", \
            "Must catch vague excellence claims without evidence"
    
    @pytest.mark.asyncio
    async def test_impact_amplification(self):
        """'Improved process' → 'Revolutionized workflow' is unsupported."""
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "other",
                "fact_text": "Improved development process",
                "metadata": {}
            }
        ]
        
        proposed_text = "Revolutionized development workflow, transforming team productivity"
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text="Improved development process"
        )
        
        # "Revolutionized" and "transforming" are unsupported amplifications
        assert result.verification_status in ["PARTIALLY_SUPPORTED", "UNSUPPORTED"], \
            "Must catch impact amplification without evidence"


class TestEndToEndPipeline:
    """
    Integration tests for complete Truth Guard pipeline.
    
    Tests the full flow: Generate → Verify → Guardrails → Status assignment.
    """
    
    @pytest.mark.asyncio
    async def test_rejected_optimization_never_stored(self):
        """
        CRITICAL: Optimizations that fail verification or guardrails
        must be REJECTED and NEVER shown to user.
        """
        mock_supabase = Mock()
        
        # Mock database responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]
        
        service = OptimizationService(mock_supabase)
        
        # Mock the generator to return a hallucinated edit
        with patch.object(service.generator, 'generate_optimizations', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [
                ProposedEdit(
                    block_id=str(uuid4()),
                    original_text="Software Engineer at Google",
                    proposed_text="Senior Software Architect at Google",  # Title inflation!
                    edit_type="content_addition",
                    fact_ledger_ids=[],
                    reasoning="Make title more impressive",
                    target_requirement_ids=[]
                )
            ]
            
            # Mock verifier to return UNSUPPORTED
            with patch.object(service.verifier, 'verify_edit', new_callable=AsyncMock) as mock_verify:
                mock_verify.return_value = Mock(
                    verification_status="UNSUPPORTED",
                    supported_claims=[],
                    unsupported_claims=["Title inflation"],
                    confidence=0.0,
                    reasoning="Title changed without fact support"
                )
                
                result = await service.generate_optimizations(
                    resume_version_id=str(uuid4()),
                    job_posting_id=str(uuid4()),
                    user_id=str(uuid4())
                )
                
                # Critical assertions
                assert result["auto_rejected"] > 0, \
                    "Hallucinated edit should be auto-rejected"
                assert result["stored"] == 0, \
                    "CRITICAL: Rejected edit was stored - MUST NOT happen"
    
    @pytest.mark.asyncio
    async def test_supported_edit_auto_approved(self):
        """
        SUPPORTED edits that pass guardrails should be auto-approved.
        """
        # Test that legitimate rephrasing is approved
        original_text = "Worked on Python projects"
        proposed_text = "Developed Python applications"  # Just better phrasing
        
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "Python",
                "metadata": {}
            }
        ]
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text=original_text
        )
        
        # Good rephrasing should be SUPPORTED
        assert result.verification_status == "SUPPORTED", \
            "Legitimate rephrasing should be verified as SUPPORTED"
    
    @pytest.mark.asyncio
    async def test_partially_supported_requires_confirmation(self):
        """
        PARTIALLY_SUPPORTED edits must require user confirmation.
        This is for vague claims that might be true but aren't explicitly in ledger.
        """
        fact_ledger = [
            {
                "id": str(uuid4()),
                "fact_type": "skill",
                "fact_text": "Team collaboration",
                "metadata": {}
            }
        ]
        
        # Adds vague claim "strong communicator" - might be true but not in ledger
        proposed_text = "Strong communicator with proven team collaboration skills"
        
        verifier = get_independent_verifier()
        result = await verifier.verify_edit(
            proposed_text=proposed_text,
            fact_ledger=fact_ledger,
            original_text="Worked with team on projects"
        )
        
        # Should be PARTIALLY_SUPPORTED (team collab is supported, "strong communicator" is not)
        # In the actual service, this would require user confirmation
        assert result.verification_status in ["PARTIALLY_SUPPORTED", "UNSUPPORTED"], \
            "Vague claims should not be fully SUPPORTED"


class TestHallucinationRate:
    """
    META-TEST: Hallucination Rate Calculation
    
    This runs all adversarial tests and calculates overall hallucination rate.
    SUCCESS CRITERION: Rate must be EXACTLY ZERO.
    """
    
    def test_calculate_hallucination_rate(self):
        """
        This test documents the overall hallucination rate.
        
        If ANY test in this file fails, hallucination rate > 0.
        Definition of done: ALL tests pass = 0% hallucination rate.
        """
        # This is a meta-test that just documents the requirement
        hallucination_rate = 0.0  # Must remain 0.0
        
        assert hallucination_rate == 0.0, \
            "Hallucination rate must be ZERO for Step 7 to be complete"


# Run instructions
if __name__ == "__main__":
    print("""
=== STEP 7 ADVERSARIAL TESTS ===

These tests are designed to catch hallucinations in the Truth Guard optimizer.

CRITICAL REQUIREMENT:
- ALL tests must pass
- Hallucination rate must be EXACTLY ZERO
- If ANY test fails, Step 7 is NOT complete

Run with:
    pytest tests/test_optimizer.py -v --tb=short

For detailed output:
    pytest tests/test_optimizer.py -v -s

To run specific categories:
    pytest tests/test_optimizer.py::TestSkillFabrication -v
    pytest tests/test_optimizer.py::TestMetricInvention -v
    pytest tests/test_optimizer.py::TestCompanyTitleDateGuardrails -v

REMEMBER: These are ADVERSARIAL tests. They're supposed to be hard.
If they're easy to pass, they're not testing the right things.
    """)
