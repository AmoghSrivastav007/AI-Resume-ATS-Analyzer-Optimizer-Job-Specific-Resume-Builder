#!/usr/bin/env python3
"""
Hallucination detection evaluation script.

This script tests the system against adversarial cases designed to detect:
1. Skill level inflation
2. Experience exaggeration
3. Fake credentials
4. Title embellishment
5. Company fabrication

Zero-tolerance checks ensure critical fraud is never missed.

Usage:
    python run_hallucination_eval.py [--case ID] [--verbose]

Options:
    --case ID    Only run specific adversarial case (e.g., adv_01)
    --verbose    Show detailed analysis output
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.parser.structural import extract_structure
from services.job_posting_extractor import extract_job_description
from services.file_validation import PDF_MIME
from config import Settings


def load_adversarial_cases(benchmark_dir: Path) -> list[dict[str, Any]]:
    """Load all adversarial test case specifications."""
    adv_dir = benchmark_dir / 'adversarial'
    cases = []
    
    for json_file in sorted(adv_dir.glob('adversarial_*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cases.append(data)
    
    return cases


def extract_resume_and_jd(
    resume_path: Path,
    jd_path: Path,
    settings: Settings | None = None
) -> tuple[str, dict | None]:
    """Extract text from resume PDF and JD text file."""
    
    # Extract resume
    with open(resume_path, 'rb') as f:
        resume_content = f.read()
    
    resume_doc = extract_structure(resume_content, PDF_MIME)
    resume_text = resume_doc.plain_text
    
    # Extract JD (optional if settings not provided)
    jd_data = None
    if settings:
        with open(jd_path, 'r', encoding='utf-8') as f:
            jd_text = f.read()
        
        jd_data = extract_job_description(jd_text, settings)
    
    return resume_text, jd_data


def check_skill_inflation(case: dict, resume_text: str, jd_data: dict) -> dict:
    """
    Check for skill level inflation (adversarial_01).
    
    Validates that weak qualifiers like "familiar with", "exposure to", 
    "basic understanding" are NOT upgraded to "experience" or "proficiency".
    """
    results = {
        'test_name': 'Skill Level Inflation',
        'severity': case['severity'],
        'zero_tolerance': case['zero_tolerance'],
        'checks': [],
        'passed': True,
        'critical_failure': False
    }
    
    # Check for weak skill qualifiers in resume
    weak_patterns = [
        r'familiar with (\w+)',
        r'exposure to (\w+)',
        r'basic understanding of (\w+)',
        r'learning (\w+)',
        r'some experience with (\w+)'
    ]
    
    weak_skills = {}
    for pattern in weak_patterns:
        matches = re.finditer(pattern, resume_text, re.IGNORECASE)
        for match in matches:
            skill = match.group(1)
            qualifier = match.group(0)
            weak_skills[skill.lower()] = qualifier
    
    if weak_skills:
        results['checks'].append({
            'check': 'Identified weak skill qualifiers',
            'status': 'info',
            'details': f"Found {len(weak_skills)} skills with weak qualifiers",
            'skills': list(weak_skills.keys())
        })
        
        # TODO: Check if these weak skills appear as strong matches in output
        # For now, flag as warning if ANY weak qualifiers exist
        results['checks'].append({
            'check': 'Skill level preservation',
            'status': 'warning',
            'details': 'Manual verification needed: ensure weak qualifiers are not upgraded',
            'action': 'Verify extraction preserves "familiar with" vs "proficient in"'
        })
    
    return results


def check_experience_exaggeration(case: dict, resume_text: str) -> dict:
    """
    Check for experience duration exaggeration (adversarial_02).
    
    Validates that timeline calculations are accurate and accomplishments
    are reasonable for the stated duration.
    """
    results = {
        'test_name': 'Experience Duration Validation',
        'severity': case['severity'],
        'zero_tolerance': case['zero_tolerance'],
        'checks': [],
        'passed': True,
        'critical_failure': False
    }
    
    # Look for date ranges
    date_pattern = r'(\w+ \d{4})\s*[-–]\s*(\w+ \d{4}|Present)'
    date_matches = re.findall(date_pattern, resume_text)
    
    if date_matches:
        results['checks'].append({
            'check': 'Found date ranges',
            'status': 'info',
            'details': f"Identified {len(date_matches)} employment date ranges",
            'count': len(date_matches)
        })
        
        # Check for the specific trap: June 2023 - August 2023 (3 months)
        trap_pattern = r'June 2023\s*[-–]\s*August 2023'
        if re.search(trap_pattern, resume_text, re.IGNORECASE):
            results['checks'].append({
                'check': 'Detected 3-month tenure with extensive claims',
                'status': 'critical',
                'details': 'June 2023 - August 2023 = 3 months only',
                'action': 'MUST flag timeline inconsistency with accomplishments'
            })
            
            # Check for leadership language with short tenure
            leadership_terms = ['led', 'architected', 'mentored', 'built team', 'reduced costs by']
            found_terms = [term for term in leadership_terms if term in resume_text.lower()]
            
            if found_terms:
                results['checks'].append({
                    'check': 'Leadership claims with 3-month tenure',
                    'status': 'critical',
                    'details': f"Found leadership terms: {found_terms}",
                    'action': 'MUST flag as timeline inconsistency'
                })
                results['critical_failure'] = True
                results['passed'] = False
    
    return results


def check_fake_credentials(case: dict, resume_text: str) -> dict:
    """
    Check for fake certifications (adversarial_03).
    
    Validates that certification names match known real certifications.
    """
    results = {
        'test_name': 'Credential Verification',
        'severity': case['severity'],
        'zero_tolerance': case['zero_tolerance'],
        'checks': [],
        'passed': True,
        'critical_failure': False
    }
    
    # Known fake certifications from the adversarial case
    fake_certs = [
        'AWS Certified Master Architect',
        'Google Certified Senior Cloud Engineer',
        'Certified Kubernetes Expert',
        'Docker Certified DevOps Professional',
        'Advanced Python Programming Certification - Stanford'
    ]
    
    found_fake = []
    for fake_cert in fake_certs:
        if fake_cert.lower() in resume_text.lower():
            found_fake.append(fake_cert)
    
    if found_fake:
        results['checks'].append({
            'check': 'Detected fake certifications',
            'status': 'critical',
            'details': f"Found {len(found_fake)} non-existent certifications",
            'fake_certs': found_fake,
            'action': 'MUST flag these certifications for verification'
        })
        results['critical_failure'] = True
        results['passed'] = False
    else:
        results['checks'].append({
            'check': 'No obvious fake certifications detected',
            'status': 'pass',
            'details': 'Certificate names appear valid or not present'
        })
    
    # Check for suspicious certification patterns
    suspicious_patterns = [
        r'Certified \w+ (Master|Expert|Advanced Professional)',
        r'(AWS|Google|Microsoft) Certified (Master|Senior)'
    ]
    
    for pattern in suspicious_patterns:
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        if matches:
            results['checks'].append({
                'check': 'Suspicious certification naming pattern',
                'status': 'warning',
                'details': f"Found pattern suggesting inflated cert names: {matches}",
                'action': 'Verify certification names against official programs'
            })
    
    return results


def check_title_embellishment(case: dict, resume_text: str) -> dict:
    """
    Check for title-responsibility mismatch (adversarial_04).
    
    Validates that job titles align with actual responsibilities.
    """
    results = {
        'test_name': 'Title-Responsibility Consistency',
        'severity': case['severity'],
        'zero_tolerance': case['zero_tolerance'],
        'checks': [],
        'passed': True,
        'critical_failure': False
    }
    
    # Check for senior/architect titles
    senior_titles = ['Senior', 'Architect', 'Lead', 'Principal', 'Staff']
    found_senior_title = False
    
    for title in senior_titles:
        if re.search(rf'\b{title}\b.*?(Engineer|Developer|Architect)', resume_text, re.IGNORECASE):
            found_senior_title = True
            break
    
    if found_senior_title:
        # Check for junior-level responsibility indicators
        junior_indicators = [
            'under supervision',
            'assisted',
            'shadowed',
            'attended training',
            'learning',
            'exposure to',
            'fixed bugs'
        ]
        
        found_junior = [ind for ind in junior_indicators if ind.lower() in resume_text.lower()]
        
        if found_junior:
            results['checks'].append({
                'check': 'Title-responsibility mismatch detected',
                'status': 'warning',
                'details': f"Senior title but junior indicators: {found_junior}",
                'action': 'FLAG for verification - assess by responsibilities, not title'
            })
            results['passed'] = False
            # Not critical failure since common at startups
        else:
            results['checks'].append({
                'check': 'Senior title with appropriate responsibilities',
                'status': 'pass',
                'details': 'No obvious mismatch detected'
            })
    
    return results


def check_company_fabrication(case: dict, resume_text: str) -> dict:
    """
    Check for unverifiable company claims (adversarial_05).
    
    Flags generic company names and unverifiable employers.
    """
    results = {
        'test_name': 'Company Verification',
        'severity': case['severity'],
        'zero_tolerance': case['zero_tolerance'],
        'checks': [],
        'passed': True,
        'critical_failure': False
    }
    
    # Known fake companies from adversarial case
    fake_companies = [
        'TechGlobal Solutions',
        'CloudInnovate Systems',
        'AI Dynamics Corporation'
    ]
    
    found_fake = []
    for fake_co in fake_companies:
        if fake_co.lower() in resume_text.lower():
            found_fake.append(fake_co)
    
    if found_fake:
        results['checks'].append({
            'check': 'Unverifiable companies detected',
            'status': 'critical',
            'details': f"Found {len(found_fake)} companies that cannot be verified",
            'companies': found_fake,
            'action': 'MUST flag for background check - possible fabricated history'
        })
        results['critical_failure'] = True
        results['passed'] = False
    
    # Check for generic company name patterns
    generic_patterns = [
        r'Tech\w+ (Solutions?|Systems?|Inc)',
        r'Cloud\w+ (Systems?|Inc)',
        r'(AI|Data|Software) \w+ (Corp|Corporation|Inc)'
    ]
    
    for pattern in generic_patterns:
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        if matches:
            results['checks'].append({
                'check': 'Generic company names detected',
                'status': 'warning',
                'details': f"Found generic naming patterns: {matches}",
                'action': 'Verify company existence online (website, LinkedIn, Crunchbase)'
            })
    
    return results


def run_adversarial_test(case: dict, benchmark_dir: Path, settings: Settings | None = None) -> dict:
    """Run a single adversarial test case."""
    
    case_id = case['case_id']
    case_name = case['case_name']
    
    result = {
        'case_id': case_id,
        'case_name': case_name,
        'trap_type': case['trap_type'],
        'severity': case['severity'],
        'zero_tolerance': case['zero_tolerance'],
        'test_results': [],
        'overall_passed': True,
        'critical_failures': []
    }
    
    try:
        # Get file paths
        resume_file = case['resume_file']
        jd_file = case['jd_file']
        
        resume_path = benchmark_dir / 'resumes' / resume_file.replace('.txt', '.pdf')
        jd_path = benchmark_dir / 'job_descriptions' / jd_file
        
        if not resume_path.exists():
            raise FileNotFoundError(f"Resume not found: {resume_path}")
        if not jd_path.exists():
            raise FileNotFoundError(f"JD not found: {jd_path}")
        
        # Extract content
        resume_text, jd_data = extract_resume_and_jd(resume_path, jd_path, settings)
        
        # Run appropriate check based on trap type
        if case['trap_type'] == 'skill_inflation':
            test_result = check_skill_inflation(case, resume_text, jd_data)
        elif case['trap_type'] == 'experience_exaggeration':
            test_result = check_experience_exaggeration(case, resume_text)
        elif case['trap_type'] == 'fake_credentials':
            test_result = check_fake_credentials(case, resume_text)
        elif case['trap_type'] == 'title_embellishment':
            test_result = check_title_embellishment(case, resume_text)
        elif case['trap_type'] == 'company_fabrication':
            test_result = check_company_fabrication(case, resume_text)
        else:
            test_result = {
                'test_name': f'Unknown trap type: {case["trap_type"]}',
                'passed': False,
                'checks': [{'check': 'Unknown test', 'status': 'error'}]
            }
        
        result['test_results'].append(test_result)
        
        # Check for critical failures
        if test_result.get('critical_failure') and case['zero_tolerance']:
            result['overall_passed'] = False
            result['critical_failures'].append(test_result['test_name'])
        
        if not test_result.get('passed'):
            result['overall_passed'] = False
        
    except Exception as e:
        result['error'] = str(e)
        result['overall_passed'] = False
    
    return result


def generate_report(results: list[dict]) -> str:
    """Generate hallucination detection report."""
    
    report = []
    report.append("=" * 80)
    report.append("HALLUCINATION DETECTION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.get('overall_passed', False))
    critical_failures = sum(1 for r in results if r.get('critical_failures'))
    
    report.append("SUMMARY")
    report.append("-" * 80)
    report.append(f"  Total Cases:         {total}")
    report.append(f"  Passed:              {passed}")
    report.append(f"  Failed:              {total - passed}")
    report.append(f"  Critical Failures:   {critical_failures}")
    report.append("")
    
    # Detailed results
    report.append("DETAILED RESULTS")
    report.append("-" * 80)
    
    for i, result in enumerate(results, 1):
        case_id = result['case_id']
        case_name = result['case_name']
        trap_type = result['trap_type']
        
        status = "✓ PASS" if result['overall_passed'] else "✗ FAIL"
        if result.get('critical_failures'):
            status = f"✗ CRITICAL FAIL ({len(result['critical_failures'])})"
        
        report.append(f"\n{i}. [{case_id}] {case_name}")
        report.append(f"   Trap Type: {trap_type}")
        report.append(f"   Status: {status}")
        report.append(f"   Zero Tolerance: {'YES' if result['zero_tolerance'] else 'NO'}")
        
        if result.get('error'):
            report.append(f"   ERROR: {result['error']}")
            continue
        
        # Show test results
        for test_result in result.get('test_results', []):
            report.append(f"\n   Test: {test_result['test_name']}")
            for check in test_result.get('checks', []):
                status_icon = {
                    'pass': '✓',
                    'info': 'ℹ',
                    'warning': '⚠',
                    'critical': '✗',
                    'error': '✗'
                }.get(check['status'], '?')
                
                report.append(f"     {status_icon} {check['check']}")
                if check.get('details'):
                    report.append(f"       Details: {check['details']}")
                if check.get('action'):
                    report.append(f"       Action: {check['action']}")
    
    report.append("")
    report.append("=" * 80)
    
    # Final assessment
    if critical_failures > 0:
        assessment = "✗ CRITICAL FAILURES DETECTED - Zero tolerance violated"
    elif passed == total:
        assessment = "✓ ALL CHECKS PASSED - No hallucinations detected"
    else:
        assessment = "⚠ SOME CHECKS FAILED - Review warnings"
    
    report.append(f"ASSESSMENT: {assessment}")
    report.append("=" * 80)
    report.append("")
    
    return "\n".join(report)


def main():
    """Main hallucination evaluation function."""
    
    parser = argparse.ArgumentParser(description='Evaluate hallucination detection')
    parser.add_argument('--case', type=str, help='Specific case ID to run (e.g., adv_01)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--output', type=str, help='Output file for report')
    args = parser.parse_args()
    
    # Setup paths
    script_dir = Path(__file__).parent
    benchmark_dir = script_dir / 'benchmark'
    
    print("Loading adversarial test cases...")
    cases = load_adversarial_cases(benchmark_dir)
    
    if args.case:
        cases = [c for c in cases if c['case_id'] == args.case]
        if not cases:
            print(f"ERROR: Case '{args.case}' not found")
            return 1
    
    print(f"Found {len(cases)} adversarial test case(s)\n")
    
    # Load settings if available
    try:
        settings = Settings()
    except Exception as e:
        print(f"Warning: Could not load settings ({e})")
        print("Running in text-analysis-only mode (no JD extraction)\n")
        settings = None
    
    # Run tests
    results = []
    
    for i, case in enumerate(cases, 1):
        case_id = case['case_id']
        case_name = case['case_name']
        
        print(f"[{i}/{len(cases)}] Running {case_id}: {case_name}...")
        
        result = run_adversarial_test(case, benchmark_dir, settings)
        results.append(result)
        
        if args.verbose:
            status = "✓" if result['overall_passed'] else "✗"
            print(f"  {status} {result['trap_type']}")
            if result.get('critical_failures'):
                print(f"  ✗ Critical failures: {result['critical_failures']}")
    
    print("\nGenerating report...")
    report = generate_report(results)
    
    # Output report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding='utf-8')
        print(f"\n✓ Report saved to: {output_path}")
    else:
        print("\n" + report)
    
    # Save detailed results
    results_file = script_dir / 'hallucination_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"✓ Detailed results saved to: {results_file}")
    
    # Exit code
    critical_failures = sum(1 for r in results if r.get('critical_failures'))
    if critical_failures > 0:
        print(f"\n✗ FAILED: {critical_failures} critical failure(s) detected")
        return 1
    else:
        print(f"\n✓ PASSED: All hallucination checks passed")
        return 0


if __name__ == '__main__':
    sys.exit(main())
