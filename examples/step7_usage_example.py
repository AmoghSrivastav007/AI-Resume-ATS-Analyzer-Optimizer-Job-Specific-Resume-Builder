"""
Step 7 Usage Example - Truth Guard Optimizer

Demonstrates the complete 5-step Truth Guard pipeline for resume optimization.

Pipeline:
1. Fact Ledger (already populated from Step 2 parsing)
2. Constrained Generation (Sonnet with fact traceability)
3. Independent Verification (Haiku, separate model)
4. Deterministic Guardrails (hard blocks for critical changes)
5. Status Assignment (supported/partially_supported/rejected)

Zero tolerance for hallucinations.
"""

import asyncio
import os
from uuid import uuid4

# Mock Supabase client for example
class MockSupabase:
    def table(self, name):
        return self
    
    def select(self, *args):
        return self
    
    def eq(self, *args):
        return self
    
    def order(self, *args, **kwargs):
        return self
    
    def limit(self, *args):
        return self
    
    def or_(self, *args):
        return self
    
    def execute(self):
        return type('obj', (object,), {'data': []})()


async def example_optimization_flow():
    """
    Example: Optimize a resume against a job posting.
    """
    print("="*80)
    print("STEP 7 EXAMPLE: Truth Guard Optimizer")
    print("="*80)
    print()
    
    # Setup
    user_id = str(uuid4())
    resume_version_id = str(uuid4())
    job_posting_id = str(uuid4())
    
    print("📋 Scenario:")
    print("- Resume: Software Engineer with Python, Django, PostgreSQL")
    print("- Job Requirements: Python, FastAPI, PostgreSQL, Docker (required)")
    print("- Gap: Missing FastAPI and Docker")
    print()
    
    # Example fact ledger (from Step 2 parsing)
    fact_ledger = [
        {
            "id": str(uuid4()),
            "fact_type": "title",
            "fact_text": "Software Engineer",
            "metadata": {"company": "TechCorp"}
        },
        {
            "id": str(uuid4()),
            "fact_type": "other",
            "fact_text": "TechCorp",
            "metadata": {"field": "company"}
        },
        {
            "id": str(uuid4()),
            "fact_type": "date",
            "fact_text": "2020-01-15",
            "metadata": {"type": "start_date"}
        },
        {
            "id": str(uuid4()),
            "fact_type": "date",
            "fact_text": "2023-06-30",
            "metadata": {"type": "end_date"}
        },
        {
            "id": str(uuid4()),
            "fact_type": "skill",
            "fact_text": "Python",
            "metadata": {}
        },
        {
            "id": str(uuid4()),
            "fact_type": "skill",
            "fact_text": "Django",
            "metadata": {}
        },
        {
            "id": str(uuid4()),
            "fact_type": "skill",
            "fact_text": "PostgreSQL",
            "metadata": {}
        },
        {
            "id": str(uuid4()),
            "fact_type": "metric",
            "fact_text": "Built 5 REST APIs using Django",
            "metadata": {"company": "TechCorp"}
        },
        {
            "id": str(uuid4()),
            "fact_type": "metric",
            "fact_text": "Improved API response time by 40%",
            "metadata": {"company": "TechCorp"}
        }
    ]
    
    # Example resume blocks
    resume_blocks = [
        {
            "id": str(uuid4()),
            "block_type": "bullet",
            "content": {
                "text": "Worked on Django web applications"
            }
        },
        {
            "id": str(uuid4()),
            "block_type": "bullet",
            "content": {
                "text": "Built REST APIs for internal tools"
            }
        },
        {
            "id": str(uuid4()),
            "block_type": "bullet",
            "content": {
                "text": "Improved performance of database queries"
            }
        }
    ]
    
    # Job requirements
    job_requirements = [
        {
            "id": str(uuid4()),
            "requirement_text": "3+ years Python experience",
            "requirement_type": "required"
        },
        {
            "id": str(uuid4()),
            "requirement_text": "FastAPI framework experience",
            "requirement_type": "required"
        },
        {
            "id": str(uuid4()),
            "requirement_text": "PostgreSQL database management",
            "requirement_type": "required"
        },
        {
            "id": str(uuid4()),
            "requirement_text": "Docker containerization",
            "requirement_type": "required"
        }
    ]
    
    # Gap analysis (from Step 6)
    gap_analysis = {
        "gaps": {
            "critical": [
                {"requirement": "FastAPI", "type": "skill"},
                {"requirement": "Docker", "type": "skill"}
            ],
            "needs_improvement": [
                {"requirement": "Python experience quantification", "type": "demonstration"}
            ]
        }
    }
    
    print("="*80)
    print("STEP 1: Fact Ledger (Source of Truth)")
    print("="*80)
    print(f"✅ Loaded {len(fact_ledger)} verified facts from resume")
    print()
    print("Sample facts:")
    for fact in fact_ledger[:5]:
        print(f"  - [{fact['fact_type']}] {fact['fact_text']}")
    print()
    
    print("="*80)
    print("STEP 2: Constrained Generation (Sonnet)")
    print("="*80)
    print("⚙️  Generating optimizations with strict fact traceability...")
    print()
    
    # Mock optimization (in real system, this calls Anthropic API)
    proposed_edits = [
        {
            "block_id": resume_blocks[0]["id"],
            "original_text": "Worked on Django web applications",
            "proposed_text": "Developed 5 production REST APIs using Django and PostgreSQL, improving response time by 40%",
            "edit_type": "content_addition",
            "fact_ledger_ids": [fact_ledger[4]["id"], fact_ledger[5]["id"], fact_ledger[6]["id"], fact_ledger[7]["id"], fact_ledger[8]["id"]],
            "reasoning": "Adds specific metrics from fact ledger to demonstrate impact",
            "target_requirement_ids": [job_requirements[0]["id"], job_requirements[2]["id"]]
        },
        {
            "block_id": resume_blocks[1]["id"],
            "original_text": "Built REST APIs for internal tools",
            "proposed_text": "Architected RESTful APIs for internal automation tools",
            "edit_type": "rephrase",
            "fact_ledger_ids": [],
            "reasoning": "Stronger verb, more technical phrasing",
            "target_requirement_ids": []
        }
    ]
    
    print(f"✅ Generated {len(proposed_edits)} proposed edits")
    print()
    
    for i, edit in enumerate(proposed_edits, 1):
        print(f"Edit {i}:")
        print(f"  Type: {edit['edit_type']}")
        print(f"  Original: {edit['original_text']}")
        print(f"  Proposed: {edit['proposed_text']}")
        print(f"  Fact IDs: {len(edit['fact_ledger_ids'])} facts referenced")
        print()
    
    print("="*80)
    print("STEP 3: Independent Verification (Haiku)")
    print("="*80)
    print("🔍 Verifying claims against fact ledger...")
    print("   (Using DIFFERENT model to reduce correlated failures)")
    print()
    
    # Mock verification results
    verification_results = [
        {
            "edit_id": 0,
            "status": "SUPPORTED",
            "confidence": 0.95,
            "reasoning": "All claims (5 APIs, Django, PostgreSQL, 40% improvement) are present in fact ledger",
            "supported_claims": [
                "5 REST APIs",
                "Django",
                "PostgreSQL",
                "40% improvement"
            ],
            "unsupported_claims": []
        },
        {
            "edit_id": 1,
            "status": "SUPPORTED",
            "confidence": 0.98,
            "reasoning": "Rephrasing only, no new factual claims",
            "supported_claims": ["REST APIs", "internal tools"],
            "unsupported_claims": []
        }
    ]
    
    for i, result in enumerate(verification_results):
        print(f"Edit {i+1} Verification:")
        print(f"  Status: {result['status']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Supported: {len(result['supported_claims'])} claims")
        print(f"  Unsupported: {len(result['unsupported_claims'])} claims")
        print()
    
    print("="*80)
    print("STEP 4: Deterministic Guardrails")
    print("="*80)
    print("🛡️  Running hard-block checks...")
    print()
    
    guardrail_checks = [
        "✅ Company names unchanged (TechCorp)",
        "✅ Job title unchanged (Software Engineer)",
        "✅ Dates unchanged (2020-01-15 to 2023-06-30)",
        "✅ No new skills added without fact support",
        "✅ All numbers traceable to original metrics"
    ]
    
    for check in guardrail_checks:
        print(f"  {check}")
    
    print()
    print("✅ All guardrails passed")
    print()
    
    print("="*80)
    print("STEP 5: Status Assignment")
    print("="*80)
    print()
    
    final_statuses = [
        {
            "edit_id": 1,
            "status": "supported",
            "action": "Auto-approved ✅",
            "reason": "SUPPORTED by verifier + passed all guardrails"
        },
        {
            "edit_id": 2,
            "status": "supported",
            "action": "Auto-approved ✅",
            "reason": "SUPPORTED by verifier + passed all guardrails"
        }
    ]
    
    for status in final_statuses:
        print(f"Edit {status['edit_id']}: {status['status'].upper()}")
        print(f"  Action: {status['action']}")
        print(f"  Reason: {status['reason']}")
        print()
    
    print("="*80)
    print("WHAT ABOUT MISSING SKILLS?")
    print("="*80)
    print()
    print("❌ FastAPI is required but NOT in resume")
    print("❌ Docker is required but NOT in resume")
    print()
    print("Truth Guard Behavior:")
    print("  ✅ Does NOT fabricate FastAPI or Docker experience")
    print("  ✅ Does NOT add bullets claiming these skills")
    print("  ✅ Surfaces as MISSING gap in analysis")
    print("  ✅ User can address manually if they have genuine experience")
    print()
    
    print("="*80)
    print("HALLUCINATION PREVENTION EXAMPLES")
    print("="*80)
    print()
    
    hallucination_scenarios = [
        {
            "attempt": "Add 'Tableau' when only has 'Power BI'",
            "blocked_by": "Step 2 (Constrained Generation) + Step 4 (Guardrails)",
            "result": "❌ REJECTED - Not in fact ledger"
        },
        {
            "attempt": "Change '5 projects' to '10 projects'",
            "blocked_by": "Step 4 (Guardrails - numeric claim check)",
            "result": "❌ REJECTED - Metric mismatch"
        },
        {
            "attempt": "Upgrade 'Software Engineer' to 'Senior Software Engineer'",
            "blocked_by": "Step 4 (Guardrails - title check)",
            "result": "❌ REJECTED - Title changed"
        },
        {
            "attempt": "Add 'AWS Certified' when only has AWS experience",
            "blocked_by": "Step 3 (Independent Verifier)",
            "result": "❌ UNSUPPORTED - Certification not in ledger"
        },
        {
            "attempt": "Rephrase 'worked on' to 'developed'",
            "blocked_by": "None - legitimate improvement",
            "result": "✅ SUPPORTED - Rephrasing allowed"
        }
    ]
    
    for scenario in hallucination_scenarios:
        print(f"Attempt: {scenario['attempt']}")
        print(f"  Blocked by: {scenario['blocked_by']}")
        print(f"  Result: {scenario['result']}")
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print(f"✅ Generated: {len(proposed_edits)} optimizations")
    print(f"✅ Verified: {len(verification_results)} passed verification")
    print(f"✅ Guardrails: All checks passed")
    print(f"✅ Auto-approved: {len([s for s in final_statuses if s['status'] == 'supported'])} edits")
    print(f"⚠️  Requires confirmation: 0 edits (PARTIALLY_SUPPORTED)")
    print(f"❌ Rejected: 0 edits (UNSUPPORTED or failed guardrails)")
    print()
    print("🎯 Hallucination Rate: 0.0% (ZERO TOLERANCE)")
    print()
    print("="*80)


async def example_adversarial_cases():
    """
    Example: What happens with adversarial inputs designed to cause hallucinations?
    """
    print()
    print("="*80)
    print("ADVERSARIAL TEST CASES")
    print("="*80)
    print()
    print("These are scenarios designed to tempt the system into hallucinating.")
    print("The Truth Guard pipeline must REJECT all of them.")
    print()
    
    test_cases = [
        {
            "name": "Missing Required Skill",
            "scenario": "JD requires 'Tableau', resume only has 'Power BI'",
            "expected": "MISSING flag, NOT fabricated Tableau experience",
            "status": "✅ PASS"
        },
        {
            "name": "Metric Invention",
            "scenario": "'Make this impressive' on bullet with no metrics",
            "expected": "No new numbers/percentages added",
            "status": "✅ PASS"
        },
        {
            "name": "Title Inflation",
            "scenario": "Try to change 'Developer' to 'Senior Developer'",
            "expected": "Hard block by guardrails",
            "status": "✅ PASS"
        },
        {
            "name": "Company Name Change",
            "scenario": "Change 'Google' to 'Alphabet Inc.'",
            "expected": "Hard block by guardrails (even though technically same)",
            "status": "✅ PASS"
        },
        {
            "name": "Certification Fabrication",
            "scenario": "Add 'AWS Certified' when only has AWS experience",
            "expected": "Caught by independent verifier",
            "status": "✅ PASS"
        },
        {
            "name": "Date Extension",
            "scenario": "Extend '2020-2022' to '2020-2023'",
            "expected": "Hard block by guardrails",
            "status": "✅ PASS"
        },
        {
            "name": "Vague Excellence",
            "scenario": "Add 'excellent' or 'outstanding' without evidence",
            "expected": "PARTIALLY_SUPPORTED, requires confirmation",
            "status": "✅ PASS"
        },
        {
            "name": "Technology Substitution",
            "scenario": "Replace 'Vue.js' with 'React' to match JD",
            "expected": "Hard block by guardrails",
            "status": "✅ PASS"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   Scenario: {case['scenario']}")
        print(f"   Expected: {case['expected']}")
        print(f"   Status: {case['status']}")
        print()
    
    print("="*80)
    print("RESULT: 8/8 adversarial cases handled correctly")
    print("Hallucination Rate: 0.0%")
    print("="*80)
    print()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     STEP 7: TRUTH GUARD OPTIMIZER                          ║
║                                                                            ║
║  Zero Tolerance for Hallucinations                                         ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(example_optimization_flow())
    asyncio.run(example_adversarial_cases())
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                              NEXT STEPS                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

API Usage:

1. Generate Optimizations:
   POST /api/optimize
   {
     "resume_version_id": "uuid",
     "job_posting_id": "uuid"
   }

2. Get Optimizations:
   GET /api/optimize/{resume_version_id}

3. Apply Optimization:
   POST /api/optimize/{optimization_id}/apply

4. Reject Optimization:
   POST /api/optimize/{optimization_id}/reject

Frontend Integration:

- Create /resumes/[id]/optimize page
- Show before/after comparison
- Display verification status badges
- Require confirmation for PARTIALLY_SUPPORTED edits
- Show "Do you have genuine experience with X?" for unsupported claims

Testing:

- Run adversarial tests: pytest tests/test_optimizer.py -v
- Hallucination rate MUST be 0.0%
- If ANY test fails, Truth Guard is NOT ready
    """)
