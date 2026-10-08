import io
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt, Inches
from jinja2 import Template

# Optional import - WeasyPrint requires GTK libraries on Windows
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_ERROR = str(e)

from config import Settings
from services.parser.pipeline import ResumeParsePipeline
from services.supabase_client import create_service_client


class ExportService:
    """Service for generating DOCX and PDF exports with self-check validation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = create_service_client(settings)
        self.template_dir = Path(__file__).resolve().parents[1] / "templates"

    def generate_docx(self, user_id: str, resume_version_id: str) -> bytes:
        """
        Generate a DOCX file directly from resume_blocks using python-docx.
        Uses Word's built-in Heading styles for section headers.
        """
        # Fetch resume data
        resume_data = self._fetch_resume_data(user_id, resume_version_id)
        
        # Create document
        doc = Document()
        
        # Set default font for Normal style
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        
        # Process contact section first (if exists)
        contact_section = next(
            (s for s in resume_data['sections'] if s['section_type'] == 'contact'),
            None
        )
        
        if contact_section:
            self._add_contact_section(doc, contact_section)
        
        # Process remaining sections
        for section in resume_data['sections']:
            if section['section_type'] == 'contact':
                continue  # Already processed
            
            self._add_section_to_docx(doc, section)
        
        # Save to bytes
        doc_bytes = io.BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)
        return doc_bytes.read()

    def generate_pdf(self, user_id: str, resume_version_id: str) -> bytes:
        """
        Generate a PDF file from HTML/CSS template using WeasyPrint.
        Raises RuntimeError if WeasyPrint is not available.
        """
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError(
                f"WeasyPrint is not available: {WEASYPRINT_ERROR}\n"
                "On Windows, WeasyPrint requires GTK libraries. "
                "See VERIFICATION_REPORT.md for installation instructions."
            )
        
        # Fetch resume data
        resume_data = self._fetch_resume_data(user_id, resume_version_id)
        
        # Prepare template data
        template_data = self._prepare_template_data(resume_data)
        
        # Load and render template
        template_path = self.template_dir / "resume_pdf.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        html_content = template.render(**template_data)
        
        # Generate PDF with WeasyPrint
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

    def validate_export(self, file_bytes: bytes, original_resume_version_id: str, user_id: str) -> dict[str, Any]:
        """
        Self-check validation: re-run Step 2 parser on generated file
        and verify all fields are recoverable as text.
        """
        # Get original parsed data
        original_data = self._fetch_resume_data(user_id, original_resume_version_id)
        
        # Create temporary file and parse it
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            # Re-parse the generated file using the same pipeline
            pipeline = ResumeParsePipeline(self.settings)
            
            # Upload temp file to storage for parsing
            storage_path = f"temp_exports/{user_id}/{datetime.utcnow().isoformat()}.pdf"
            self.client.storage.from_("resumes").upload(
                storage_path,
                file_bytes,
                file_options={"content-type": "application/pdf"}
            )
            
            # Create temporary version record for parsing
            temp_version = self.client.table("resume_versions").insert({
                "resume_id": original_data['resume_id'],
                "user_id": user_id,
                "version_number": 9999,  # Temporary marker
                "status": "parsing",
                "storage_path": storage_path,
                "original_filename": "export_validation.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": len(file_bytes),
            }).execute()
            
            temp_version_id = temp_version.data[0]['id']
            
            # Run parser
            parse_result = pipeline.run(
                user_id=user_id,
                resume_id=original_data['resume_id'],
                resume_version_id=temp_version_id,
                access_token=None
            )
            
            # Clean up temporary records
            self._cleanup_temp_validation_data(temp_version_id, storage_path)
            
            # Compare parsed result with original
            validation_result = self._compare_parsed_data(
                original_data,
                parse_result.parsed if parse_result.parsed else {}
            )
            
            return {
                "validation_passed": validation_result['passed'],
                "fields_checked": validation_result['fields_checked'],
                "fields_recovered": validation_result['fields_recovered'],
                "missing_fields": validation_result['missing_fields'],
                "parsing_errors": validation_result.get('errors', []),
            }
            
        except Exception as e:
            return {
                "validation_passed": False,
                "fields_checked": 0,
                "fields_recovered": 0,
                "missing_fields": [],
                "parsing_errors": [str(e)],
            }
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    def _fetch_resume_data(self, user_id: str, resume_version_id: str) -> dict[str, Any]:
        """Fetch complete resume data including sections and blocks."""
        # Get version info
        version = self.client.table("resume_versions").select("*").eq("id", resume_version_id).eq("user_id", user_id).single().execute()
        
        if not version.data:
            raise ValueError("Resume version not found")
        
        # Get sections with blocks
        sections = self.client.table("resume_sections").select("*, resume_blocks(*)").eq(
            "resume_version_id", resume_version_id
        ).eq("user_id", user_id).order("sort_order").execute()
        
        # Transform data
        sections_data = []
        for section in sections.data:
            blocks = sorted(section.get('resume_blocks', []), key=lambda b: b['sort_order'])
            sections_data.append({
                'id': section['id'],
                'section_type': section['section_type'],
                'title': section['title'],
                'sort_order': section['sort_order'],
                'blocks': blocks,
            })
        
        return {
            'resume_id': version.data['resume_id'],
            'version_id': resume_version_id,
            'sections': sections_data,
        }

    def _add_contact_section(self, doc: Document, section: dict[str, Any]) -> None:
        """Add contact information at the top of the document."""
        # Extract contact info from blocks
        contact_info = {}
        for block in section['blocks']:
            content = block.get('content', {})
            if 'name' in content:
                contact_info['name'] = content['name']
            if 'email' in content:
                contact_info['email'] = content['email']
            if 'phone' in content:
                contact_info['phone'] = content['phone']
            if 'location' in content:
                contact_info['location'] = content['location']
            if 'linkedin' in content:
                contact_info['linkedin'] = content['linkedin']
        
        # Name (centered, large, bold)
        if contact_info.get('name'):
            name_para = doc.add_paragraph()
            name_run = name_para.add_run(contact_info['name'])
            name_run.font.size = Pt(18)
            name_run.bold = True
            name_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Contact details (centered, smaller)
        contact_parts = []
        if contact_info.get('email'):
            contact_parts.append(contact_info['email'])
        if contact_info.get('phone'):
            contact_parts.append(contact_info['phone'])
        if contact_info.get('location'):
            contact_parts.append(contact_info['location'])
        if contact_info.get('linkedin'):
            contact_parts.append(contact_info['linkedin'])
        
        if contact_parts:
            contact_para = doc.add_paragraph(' • '.join(contact_parts))
            contact_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            contact_run = contact_para.runs[0]
            contact_run.font.size = Pt(10)
        
        # Add spacing
        doc.add_paragraph()

    def _add_section_to_docx(self, doc: Document, section: dict[str, Any]) -> None:
        """Add a section with its blocks to the document."""
        # Section header using Heading 1 style
        section_title = section['title'] or section['section_type'].replace('_', ' ').title()
        heading = doc.add_heading(section_title, level=1)
        heading.style = doc.styles['Heading 1']
        
        # Process blocks
        for block in section['blocks']:
            self._add_block_to_docx(doc, block, section['section_type'])

    def _add_block_to_docx(self, doc: Document, block: dict[str, Any], section_type: str) -> None:
        """Add a single block to the document."""
        block_type = block.get('block_type', 'paragraph')
        content = block.get('content', {})
        text = content.get('text', '')
        
        if block_type == 'heading':
            # Sub-heading within section
            para = doc.add_heading(text, level=2)
            para.style = doc.styles['Heading 2']
        
        elif block_type == 'bullet':
            # Bullet point
            para = doc.add_paragraph(text, style='List Bullet')
        
        elif block_type == 'paragraph':
            # Regular paragraph
            para = doc.add_paragraph(text)
        
        else:
            # Default to paragraph
            para = doc.add_paragraph(text)

    def _prepare_template_data(self, resume_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare data for HTML template rendering."""
        # Extract contact section
        contact_section = None
        sections_for_template = []
        
        for section in resume_data['sections']:
            if section['section_type'] == 'contact':
                # Parse contact blocks
                contact_info = {}
                for block in section['blocks']:
                    content = block.get('content', {})
                    contact_info.update({
                        'name': content.get('name', ''),
                        'email': content.get('email', ''),
                        'phone': content.get('phone', ''),
                        'location': content.get('location', ''),
                        'linkedin': content.get('linkedin', ''),
                    })
                contact_section = contact_info
            else:
                # Process section blocks for template
                blocks_data = []
                for block in section['blocks']:
                    content = block.get('content', {})
                    block_data = {
                        'block_type': block.get('block_type', 'paragraph'),
                        'text': content.get('text', ''),
                        'title': content.get('title'),
                        'organization': content.get('organization'),
                        'date_range': content.get('date_range'),
                        'is_entry_header': content.get('is_entry_header', False),
                    }
                    blocks_data.append(block_data)
                
                sections_for_template.append({
                    'section_type': section['section_type'],
                    'title': section['title'] or section['section_type'].replace('_', ' ').title(),
                    'blocks': blocks_data,
                })
        
        return {
            'contact_section': contact_section,
            'sections': sections_for_template,
        }

    def _compare_parsed_data(self, original: dict[str, Any], reparsed: dict[str, Any]) -> dict[str, Any]:
        """Compare original and re-parsed data to verify field recovery."""
        fields_checked = 0
        fields_recovered = 0
        missing_fields = []
        
        # Get all text content from original
        original_texts = []
        for section in original['sections']:
            for block in section['blocks']:
                content = block.get('content', {})
                if 'text' in content and content['text']:
                    original_texts.append(content['text'].strip().lower())
                    fields_checked += 1
        
        # Check if texts appear in reparsed sections
        if reparsed and 'sections' in reparsed:
            reparsed_texts = []
            for section in reparsed.get('sections', []):
                for block in section.get('blocks', []):
                    content = block.get('content', {})
                    if 'text' in content and content['text']:
                        reparsed_texts.append(content['text'].strip().lower())
            
            # Check recovery
            for idx, orig_text in enumerate(original_texts):
                # Check if substantial portion of text is recovered
                found = any(
                    orig_text[:50] in reparsed_text or reparsed_text[:50] in orig_text
                    for reparsed_text in reparsed_texts
                )
                if found:
                    fields_recovered += 1
                else:
                    missing_fields.append(f"Block {idx + 1}: {orig_text[:100]}")
        
        # Pass if at least 80% of fields recovered
        recovery_rate = fields_recovered / fields_checked if fields_checked > 0 else 0
        passed = recovery_rate >= 0.8
        
        return {
            'passed': passed,
            'fields_checked': fields_checked,
            'fields_recovered': fields_recovered,
            'missing_fields': missing_fields[:10],  # Limit to first 10
            'recovery_rate': recovery_rate,
        }

    def _cleanup_temp_validation_data(self, version_id: str, storage_path: str) -> None:
        """Clean up temporary data created during validation."""
        try:
            # Delete version record
            self.client.table("resume_versions").delete().eq("id", version_id).execute()
            # Delete storage file
            self.client.storage.from_("resumes").remove([storage_path])
        except Exception:
            # Best effort cleanup
            pass
