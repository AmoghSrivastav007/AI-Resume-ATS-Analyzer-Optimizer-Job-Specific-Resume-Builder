#!/usr/bin/env python3
"""
Evaluation script for measuring resume-JD matching quality.

This script:
1. Loads ground truth labels from benchmark
2. Runs the full pipeline on each resume-JD pair
3. Compares results against expected scores
4. Calculates accuracy metrics
5. Generates a quality report

Usage:
    python run_eval.py [--pairs N] [--verbose]

Options:
    --pairs N    Only evaluate first N pairs (for testing)
    --verbose    Show detailed output for each pair
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.parser.structural import extract_structure
from services.job_posting_extractor import extract_job_description
from services.file_validation import PDF_MIME
from config import Settings


def load_ground_truth_labels(benchmark_dir: Path) -> list[dict[str, Any]]:
    """Load all ground truth label files."""
    gt_dir = benchmark_dir / 'ground_truth'
    labels = []
    
    for json_file in sorted(gt_dir.glob('*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            labels.append(data)
    
    return labels


def run_pipeline_on_pair(
    resume_path: Path,
    jd_path: Path,
    settings: Settings
) -> dict[str, Any]:
    """
    Run the full extraction pipeline on a resume-JD pair.
    
    Returns:
        Dictionary with extracted data and calculated scores
    """
    # Extract resume
    with open(resume_path, 'rb') as f:
        resume_content = f.read()
    
    resume_doc = extract_structure(resume_content, PDF_MIME)
    resume_text = resume_doc.plain_text
    
    # Extract JD
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    jd_extraction = extract_job_description(jd_text, settings)
    
    # TODO: Run full matching pipeline
    # For now, return basic extraction results
    # In real implementation, this would call the matching service
    
    return {
        'resume_chars': len(resume_text),
        'resume_blocks': len(resume_doc.blocks),
        'jd_required_skills': len(jd_extraction.required_skills),
        'jd_preferred_skills': len(jd_extraction.preferred_skills),
        # Placeholder - would come from matching service
        'calculated_match_score': 0.0,
        'extraction_success': True
    }


def calculate_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    """
    Calculate evaluation metrics from results.
    
    Metrics:
    - Accuracy: % of predictions within ±5% of ground truth
    - MAE: Mean Absolute Error
    - RMSE: Root Mean Square Error
    - Category Accuracy: % matching strong/moderate/weak category
    """
    if not results:
        return {}
    
    # Extract prediction errors
    errors = []
    absolute_errors = []
    category_matches = 0
    
    for result in results:
        if 'error' in result:
            continue
        
        expected = result['expected_score']
        actual = result['calculated_score']
        
        error = actual - expected
        errors.append(error)
        absolute_errors.append(abs(error))
        
        # Check if within ±5% range
        score_range = result.get('score_range', [expected - 0.05, expected + 0.05])
        within_range = score_range[0] <= actual <= score_range[1]
        
        # Check category match
        expected_cat = result['expected_category']
        actual_cat = categorize_score(actual)
        if expected_cat == actual_cat:
            category_matches += 1
    
    n = len(absolute_errors)
    if n == 0:
        return {}
    
    # Calculate metrics
    mae = sum(absolute_errors) / n
    mse = sum(e ** 2 for e in errors) / n
    rmse = mse ** 0.5
    
    # Accuracy: within ±5%
    within_5pct = sum(1 for ae in absolute_errors if ae <= 0.05) / n
    
    # Category accuracy
    category_acc = category_matches / n
    
    return {
        'mae': mae,
        'rmse': rmse,
        'accuracy_5pct': within_5pct,
        'category_accuracy': category_acc,
        'mean_error': sum(errors) / n,
        'num_evaluated': n
    }


def categorize_score(score: float) -> str:
    """Categorize a match score into strong/moderate/weak."""
    if score >= 0.75:
        return 'strong_match'
    elif score >= 0.50:
        return 'moderate_match'
    else:
        return 'weak_match'


def generate_report(results: list[dict[str, Any]], metrics: dict[str, float]) -> str:
    """Generate a human-readable evaluation report."""
    
    report = []
    report.append("=" * 80)
    report.append("EVALUATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Summary metrics
    report.append("OVERALL METRICS")
    report.append("-" * 80)
    if metrics:
        report.append(f"  Evaluated Pairs:        {metrics['num_evaluated']}")
        report.append(f"  Mean Absolute Error:    {metrics['mae']:.3f}")
        report.append(f"  Root Mean Square Error: {metrics['rmse']:.3f}")
        report.append(f"  Accuracy (±5%):         {metrics['accuracy_5pct']:.1%}")
        report.append(f"  Category Accuracy:      {metrics['category_accuracy']:.1%}")
        report.append(f"  Mean Error (bias):      {metrics['mean_error']:.3f}")
    else:
        report.append("  No metrics available")
    report.append("")
    
    # Detailed results
    report.append("DETAILED RESULTS")
    report.append("-" * 80)
    
    for i, result in enumerate(results, 1):
        if 'error' in result:
            report.append(f"\n{i}. {result['resume_id']} → {result['jd_id']}")
            report.append(f"   ✗ ERROR: {result['error']}")
            continue
        
        resume_id = result['resume_id']
        jd_id = result['jd_id']
        expected = result['expected_score']
        actual = result['calculated_score']
        error = actual - expected
        
        # Status indicator
        if abs(error) <= 0.05:
            status = "✓"
        elif abs(error) <= 0.10:
            status = "~"
        else:
            status = "✗"
        
        report.append(f"\n{i}. {resume_id} → {jd_id}")
        report.append(f"   Expected: {expected:.2f} ({result['expected_category']})")
        report.append(f"   Actual:   {actual:.2f} ({categorize_score(actual)})")
        report.append(f"   Error:    {error:+.3f} {status}")
        
        if result.get('notes'):
            report.append(f"   Notes:    {result['notes']}")
    
    report.append("")
    report.append("=" * 80)
    
    # Quality assessment
    if metrics:
        if metrics['accuracy_5pct'] >= 0.90 and metrics['mae'] < 0.05:
            assessment = "✓ EXCELLENT - High accuracy and low error"
        elif metrics['accuracy_5pct'] >= 0.75 and metrics['mae'] < 0.10:
            assessment = "✓ GOOD - Acceptable accuracy"
        elif metrics['accuracy_5pct'] >= 0.60:
            assessment = "~ FAIR - Needs improvement"
        else:
            assessment = "✗ POOR - Significant quality issues"
        
        report.append(f"QUALITY ASSESSMENT: {assessment}")
    
    report.append("=" * 80)
    report.append("")
    
    return "\n".join(report)


def main():
    """Main evaluation function."""
    
    parser = argparse.ArgumentParser(description='Evaluate resume-JD matching quality')
    parser.add_argument('--pairs', type=int, help='Number of pairs to evaluate (default: all)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--output', type=str, help='Output file for report (default: stdout)')
    args = parser.parse_args()
    
    # Setup paths
    script_dir = Path(__file__).parent
    benchmark_dir = script_dir / 'benchmark'
    
    print("Loading ground truth labels...")
    labels = load_ground_truth_labels(benchmark_dir)
    
    if args.pairs:
        labels = labels[:args.pairs]
    
    print(f"Found {len(labels)} ground truth pairs to evaluate\n")
    
    # Load settings
    settings = Settings()
    
    # Evaluate each pair
    results = []
    
    for i, label in enumerate(labels, 1):
        resume_file = label['resume_file']
        jd_file = label['jd_file']
        
        print(f"[{i}/{len(labels)}] Evaluating {resume_file} → {jd_file}...")
        
        try:
            # Get file paths
            resume_path = benchmark_dir / 'resumes' / resume_file.replace('.txt', '.pdf')
            jd_path = benchmark_dir / 'job_descriptions' / jd_file
            
            if not resume_path.exists():
                raise FileNotFoundError(f"Resume not found: {resume_path}")
            if not jd_path.exists():
                raise FileNotFoundError(f"JD not found: {jd_path}")
            
            # Run pipeline
            pipeline_result = run_pipeline_on_pair(resume_path, jd_path, settings)
            
            # Store result
            result = {
                'resume_id': label['resume_id'],
                'jd_id': label['jd_id'],
                'resume_file': resume_file,
                'jd_file': jd_file,
                'expected_score': label['expected_match_score'],
                'score_range': label.get('score_range', []),
                'expected_category': label['match_category'],
                'calculated_score': pipeline_result.get('calculated_match_score', 0.0),
                'pipeline_result': pipeline_result,
                'notes': label.get('notes', '')
            }
            
            results.append(result)
            
            if args.verbose:
                print(f"  Expected: {result['expected_score']:.2f}")
                print(f"  Calculated: {result['calculated_score']:.2f}")
                print(f"  Extraction: {pipeline_result['resume_chars']} chars, "
                      f"{pipeline_result['jd_required_skills']} required skills")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                'resume_id': label.get('resume_id', 'unknown'),
                'jd_id': label.get('jd_id', 'unknown'),
                'error': str(e)
            })
    
    print("\nCalculating metrics...")
    metrics = calculate_metrics(results)
    
    print("\nGenerating report...")
    report = generate_report(results, metrics)
    
    # Output report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding='utf-8')
        print(f"\n✓ Report saved to: {output_path}")
    else:
        print("\n" + report)
    
    # Save detailed results as JSON
    results_file = script_dir / 'evaluation_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': metrics,
            'results': results
        }, f, indent=2)
    print(f"✓ Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    if metrics and metrics['accuracy_5pct'] >= 0.75:
        return 0  # Success
    else:
        return 1  # Quality issues


if __name__ == '__main__':
    sys.exit(main())
