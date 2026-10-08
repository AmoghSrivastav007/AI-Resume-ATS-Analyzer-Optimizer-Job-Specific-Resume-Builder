#!/usr/bin/env python3
"""
Convert text-based resume files to PDF format for evaluation benchmark.

This script reads all .txt resume files and generates properly formatted PDFs
that can be parsed by the structural parser.

Usage:
    python convert_resumes_to_pdf.py
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def create_pdf_from_text(text_file_path: Path, pdf_file_path: Path):
    """
    Convert a text resume file to a formatted PDF.
    
    Args:
        text_file_path: Path to the input .txt file
        pdf_file_path: Path to the output .pdf file
    """
    # Read the text content
    with open(text_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(pdf_file_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles for resume sections
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#2C3E50',
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor='#34495E',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor='#2C3E50',
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor='#2C3E50',
        borderPadding=2,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#2C3E50',
        spaceAfter=6,
        fontName='Helvetica',
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#2C3E50',
        leftIndent=20,
        spaceAfter=4,
        fontName='Helvetica',
        leading=13
    )
    
    # Build the PDF content
    story = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines at the start
        if not line and not story:
            i += 1
            continue
        
        # First non-empty line is the name (title)
        if not story and line:
            story.append(Paragraph(line, title_style))
            i += 1
            continue
        
        # Second line might be job title (subtitle)
        if len(story) == 1 and line and not line.isupper() and not line.startswith('Email'):
            story.append(Paragraph(line, subtitle_style))
            i += 1
            continue
        
        # Contact information line
        if 'Email' in line or '@' in line or 'Phone' in line:
            story.append(Paragraph(line, subtitle_style))
            i += 1
            continue
        
        # Section headings (ALL CAPS or specific keywords)
        if line.isupper() and len(line) > 2 and len(line) < 50:
            if story:  # Add space before section
                story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(line, section_heading_style))
            i += 1
            continue
        
        # Bullet points
        if line.startswith('•') or line.startswith('-'):
            # Clean up the bullet
            clean_line = line.lstrip('•-').strip()
            story.append(Paragraph(f"• {clean_line}", bullet_style))
            i += 1
            continue
        
        # Job title with location (contains |)
        if '|' in line and len(line) < 100:
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(f"<b>{line}</b>", body_style))
            i += 1
            continue
        
        # Date ranges (e.g., "March 2020 - Present")
        if any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                                            'July', 'August', 'September', 'October', 'November', 'December']) \
           and ('-' in line or 'to' in line.lower()):
            story.append(Paragraph(f"<i>{line}</i>", body_style))
            i += 1
            continue
        
        # Empty lines - add small space
        if not line:
            story.append(Spacer(1, 0.05*inch))
            i += 1
            continue
        
        # Regular paragraph text
        if line:
            story.append(Paragraph(line, body_style))
            i += 1
            continue
        
        i += 1
    
    # Build the PDF
    doc.build(story)
    print(f"✓ Created: {pdf_file_path.name}")


def main():
    """Main function to convert all text resumes to PDFs."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    resumes_dir = script_dir / 'benchmark' / 'resumes'
    
    if not resumes_dir.exists():
        print(f"Error: Resumes directory not found: {resumes_dir}")
        return
    
    print("Converting text resumes to PDF format...\n")
    
    # Find all .txt files
    txt_files = sorted(resumes_dir.glob('*.txt'))
    
    if not txt_files:
        print(f"No .txt files found in {resumes_dir}")
        return
    
    print(f"Found {len(txt_files)} resume files to convert\n")
    
    converted = 0
    errors = 0
    
    for txt_file in txt_files:
        try:
            # Generate PDF filename
            pdf_file = txt_file.with_suffix('.pdf')
            
            # Convert to PDF
            create_pdf_from_text(txt_file, pdf_file)
            converted += 1
            
        except Exception as e:
            print(f"✗ Error converting {txt_file.name}: {e}")
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"  ✓ Successfully converted: {converted}")
    if errors:
        print(f"  ✗ Errors: {errors}")
    print(f"{'='*60}\n")
    
    # List created PDFs
    pdf_files = sorted(resumes_dir.glob('*.pdf'))
    if pdf_files:
        print(f"Created PDF files ({len(pdf_files)}):")
        for pdf_file in pdf_files:
            size_kb = pdf_file.stat().st_size / 1024
            print(f"  • {pdf_file.name} ({size_kb:.1f} KB)")


if __name__ == '__main__':
    main()
