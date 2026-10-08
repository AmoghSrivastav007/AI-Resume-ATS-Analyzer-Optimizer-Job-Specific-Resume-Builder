#!/usr/bin/env python3
"""
Validate that all benchmark files can be processed by the pipeline.

This script:
1. Tests structural parser on all resume PDFs
2. Tests JD extraction on all job description files
3. Reports success rate and any errors

Usage:
    python validate_benchmark.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.parser.structural import extract_structure
from services.file_validation import PDF_MIME


def validate_resume_pdfs():
    """Test structural parser on all resume PDFs."""
    
    resumes_dir = Path(__file__).parent / 'benchmark' / 'resumes'
    pdf_files = sorted(resumes_dir.glob('*.pdf'))
    
    print("\n" + "="*70)
    print("VALIDATING RESUME PDFs")
    print("="*70 + "\n")
    
    if not pdf_files:
        print("❌ No PDF files found!")
        return False
    
    print(f"Found {len(pdf_files)} PDF files to validate\n")
    
    success_count = 0
    error_count = 0
    results = []
    
    for pdf_file in pdf_files:
        try:
            # Read file content
            with open(pdf_file, 'rb') as f:
                file_content = f.read()
            
            # Test structural parser
            result = extract_structure(
                content=file_content,
                mime_type=PDF_MIME
            )
            
            # Check if we got text
            if result.plain_text and len(result.plain_text) > 50:
                print(f"✓ {pdf_file.name}")
                print(f"  • Extracted {len(result.plain_text)} characters")
                print(f"  • Blocks: {len(result.blocks)}")
                success_count += 1
                results.append({'file': pdf_file.name, 'status': 'success', 'chars': len(result.plain_text)})
            else:
                print(f"⚠ {pdf_file.name} - Extracted text too short")
                error_count += 1
                results.append({'file': pdf_file.name, 'status': 'warning', 'chars': len(result.plain_text or '')})
            
        except Exception as e:
            print(f"✗ {pdf_file.name} - Error: {e}")
            error_count += 1
            results.append({'file': pdf_file.name, 'status': 'error', 'error': str(e)})
    
    print(f"\n{'='*70}")
    print(f"Resume PDF Validation: {success_count}/{len(pdf_files)} successful")
    if error_count > 0:
        print(f"Errors/Warnings: {error_count}")
    print(f"{'='*70}\n")
    
    return success_count == len(pdf_files), results


def validate_job_descriptions():
    """Test that all job description files are readable."""
    
    jds_dir = Path(__file__).parent / 'benchmark' / 'job_descriptions'
    txt_files = sorted(jds_dir.glob('*.txt'))
    
    print("\n" + "="*70)
    print("VALIDATING JOB DESCRIPTIONS")
    print("="*70 + "\n")
    
    if not txt_files:
        print("❌ No job description files found!")
        return False, []
    
    print(f"Found {len(txt_files)} job description files to validate\n")
    
    success_count = 0
    error_count = 0
    results = []
    
    for txt_file in txt_files:
        try:
            # Read file content
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic validation: check content is reasonable
            if len(content) > 200 and 'Required' in content:
                print(f"✓ {txt_file.name}")
                print(f"  • Content length: {len(content)} characters")
                success_count += 1
                results.append({
                    'file': txt_file.name, 
                    'status': 'success', 
                    'chars': len(content)
                })
            else:
                print(f"⚠ {txt_file.name} - Content seems incomplete")
                error_count += 1
                results.append({'file': txt_file.name, 'status': 'warning'})
            
        except Exception as e:
            print(f"✗ {txt_file.name} - Error: {e}")
            error_count += 1
            results.append({'file': txt_file.name, 'status': 'error', 'error': str(e)})
    
    print(f"\n{'='*70}")
    print(f"Job Description Validation: {success_count}/{len(txt_files)} successful")
    if error_count > 0:
        print(f"Errors/Warnings: {error_count}")
    print(f"{'='*70}\n")
    
    return success_count == len(txt_files), results


def validate_ground_truth():
    """Validate ground truth label files."""
    
    gt_dir = Path(__file__).parent / 'benchmark' / 'ground_truth'
    json_files = sorted(gt_dir.glob('*.json'))
    
    print("\n" + "="*70)
    print("VALIDATING GROUND TRUTH LABELS")
    print("="*70 + "\n")
    
    if not json_files:
        print("❌ No ground truth files found!")
        return False
    
    print(f"Found {len(json_files)} ground truth label files\n")
    
    import json
    
    success_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            required_fields = ['resume_id', 'jd_id', 'expected_match_score', 'match_category']
            missing = [f for f in required_fields if f not in data]
            
            if not missing:
                print(f"✓ {json_file.name}")
                print(f"  • Score: {data['expected_match_score']}")
                print(f"  • Category: {data['match_category']}")
                success_count += 1
            else:
                print(f"⚠ {json_file.name} - Missing fields: {missing}")
                error_count += 1
                
        except Exception as e:
            print(f"✗ {json_file.name} - Error: {e}")
            error_count += 1
    
    print(f"\n{'='*70}")
    print(f"Ground Truth Validation: {success_count}/{len(json_files)} successful")
    if error_count > 0:
        print(f"Errors/Warnings: {error_count}")
    print(f"{'='*70}\n")
    
    return success_count == len(json_files)


def main():
    """Run all validation checks."""
    
    print("\n" + "="*70)
    print("BENCHMARK VALIDATION")
    print("="*70)
    
    # Run validations
    resume_ok, resume_results = validate_resume_pdfs()
    jd_ok, jd_results = validate_job_descriptions()
    gt_ok = validate_ground_truth()
    
    # Final summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Resume PDFs:        {'✓ PASS' if resume_ok else '✗ FAIL'}")
    print(f"Job Descriptions:   {'✓ PASS' if jd_ok else '✗ FAIL'}")
    print(f"Ground Truth:       {'✓ PASS' if gt_ok else '✗ FAIL'}")
    print("="*70)
    
    if resume_ok and jd_ok and gt_ok:
        print("\n✓ All validations passed! Benchmark is ready for use.\n")
        return 0
    else:
        print("\n⚠ Some validations failed. Please review errors above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
