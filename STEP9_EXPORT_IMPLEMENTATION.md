# Step 9: Export System Implementation

## Overview

Step 9 implements a complete resume export system with PDF/DOCX generation and machine-readability self-check validation. The system generates ATS-friendly documents directly from structured resume_blocks data and validates that all content is recoverable as selectable text.

## Architecture

### Backend Components

#### 1. Database Migration (`010_export_jobs.sql`)
- **Table**: `export_jobs`
- **Purpose**: Track export generation status and validation results
- **Key Fields**:
  - `format`: pdf | docx
  - `status`: pending | generating | validating | completed | failed
  - `validation_passed`: Boolean indicating self-check result
  - `validation_details`: JSONB with detailed validation metrics
  - `storage_path`: Location of generated file in Supabase Storage

#### 2. Export Service (`services/export_service.py`)

**Key Methods**:

- **`generate_docx(user_id, resume_version_id)`**
  - Generates DOCX directly using `python-docx` library
  - Uses Word's built-in Heading styles (Heading 1, Heading 2)
  - Single column layout with standard fonts (Calibri)
  - Structured sections: contact, summary, experience, education, skills, etc.
  - Returns: bytes of generated DOCX file

- **`generate_pdf(user_id, resume_version_id)`**
  - Generates PDF using WeasyPrint from HTML/CSS template
  - Loads `templates/resume_pdf.html` with professional styling
  - Renders structured data through Jinja2 templating
  - Returns: bytes of generated PDF file

- **`validate_export(file_bytes, original_version_id, user_id)`**
  - **Self-Check Validation**: Re-runs Step 2 parser on generated file
  - Compares original resume_blocks content with re-parsed content
  - Verifies at least 80% of fields are recoverable as text
  - Returns validation result with:
    - `validation_passed`: Boolean
    - `fields_checked`: Total fields in original
    - `fields_recovered`: Fields successfully re-parsed
    - `missing_fields`: List of unrecovered content
    - `parsing_errors`: Any errors during re-parsing

**Validation Logic**:
1. Fetch original resume data from database
2. Upload generated file to temporary storage
3. Create temporary resume_version record
4. Run ResumeParsePipeline on generated file
5. Compare original text blocks with re-parsed blocks
6. Calculate recovery rate (recovered/checked)
7. Pass if ≥80% recovery rate
8. Clean up temporary data

#### 3. Export Router (`routers/exports.py`)

**Endpoints**:

- **`POST /api/exports/resumes/{resume_id}/export`**
  - **Body**: `{ format: "pdf" | "docx", version_id?: UUID }`
  - **Returns**: `{ job_id: UUID, message: string }`
  - **Process**:
    1. Create export_job record (status: generating)
    2. Generate file using ExportService
    3. Update status to validating
    4. Run self-check validation (PDF only in MVP)
    5. Store file in Supabase Storage
    6. Update job with results (status: completed/failed)
  - **Authentication**: JWT required
  - **Authorization**: User must own the resume version

- **`GET /api/exports/{job_id}`**
  - **Returns**: Export job status and validation details
  - **Response**: `{ id, status, format, validation_passed, validation_details, error_message, created_at }`

- **`GET /api/exports/{job_id}/download`**
  - **Returns**: File download (binary response)
  - **Validation**: Only allows download if validation passed
  - **Error**: 400 Bad Request if validation failed
  - **Headers**: `Content-Disposition: attachment` with filename

#### 4. HTML/CSS Template (`templates/resume_pdf.html`)

**Features**:
- Professional single-column layout
- Letter size (8.5" x 11") with 0.75" margins
- Standard fonts: Calibri, Arial (fallback)
- Structured sections with consistent formatting
- Contact section: centered with name prominence
- Section headers: uppercase, bold, with underline
- Experience/Education: header + dates + bullets
- Skills: flexible grid layout
- All text is real, selectable content (no images)

**Styling Highlights**:
- `@page` rules for PDF pagination
- Semantic HTML structure
- Professional typography (11pt body, 13pt headers)
- Print-friendly colors (black text, minimal backgrounds)
- Page break controls to avoid orphans

### Frontend Components

#### Updated Editor Page (`apps/web/src/app/resumes/[id]/editor/page.tsx`)

**New Features**:

1. **Export Button**
   - Added to header toolbar (green, with 📥 icon)
   - Opens export modal on click

2. **Export Modal**
   - Format selection: PDF or DOCX (radio buttons)
   - Export button with loading state
   - Progress indicator during generation/validation
   - Results display with validation details

3. **Export Flow**:
   ```
   User clicks Export → Modal opens → Select format → Click Export
   → Loading state (generating + validating)
   → Poll job status until completed/failed
   → Show validation results
   → Download button (if passed) or error message (if failed)
   ```

4. **Validation Result Display**:
   - ✅ **Success**: Green panel with self-check metrics, download button
   - ❌ **Failed Validation**: Red panel with missing fields, blocked download
   - ⚠️ **Error**: Red panel with error message

5. **Self-Check Information**:
   - Fields checked vs. recovered count
   - List of missing fields (if any)
   - Clear pass/fail indication
   - Explanation of ATS implications

**Key Functions**:
- `handleExport()`: Creates export job via API
- `pollExportJob(jobId)`: Polls status until completion
- `downloadExport()`: Downloads validated file
- Modal state management

## Data Flow

### Export Generation Flow

```
1. User clicks "Export" button
2. Frontend opens modal, user selects format (PDF/DOCX)
3. Frontend POSTs to /api/exports/resumes/{id}/export
4. Backend creates export_jobs record (status: generating)
5. Backend generates file using ExportService
   - DOCX: python-docx directly from resume_blocks
   - PDF: WeasyPrint from HTML template
6. Backend updates status to validating
7. Backend runs self-check validation (PDF only)
   - Upload to temp storage
   - Re-run parser
   - Compare with original
   - Calculate recovery rate
8. Backend stores file in Supabase Storage
9. Backend updates export_jobs (status: completed, validation results)
10. Frontend polls GET /api/exports/{job_id} until completed
11. Frontend displays validation results
12. If passed: User clicks download
13. Frontend GETs /api/exports/{job_id}/download
14. Browser downloads file
```

### Validation Flow

```
Original Resume Data
  ↓
Generate File (DOCX/PDF)
  ↓
Upload to Temp Storage
  ↓
Create Temp resume_version Record
  ↓
Run ResumeParsePipeline
  ↓
Extract Text Content
  ↓
Compare with Original Blocks
  ↓
Calculate Recovery Rate
  ↓
Pass if ≥80% Recovered
  ↓
Clean Up Temp Data
  ↓
Return Validation Result
```

## Key Design Decisions

### 1. DOCX Generation: python-docx Direct Approach
- **Why**: Direct generation ensures ATS-friendly structure
- **Alternative rejected**: HTML → Word conversion (less reliable)
- **Benefits**: 
  - Full control over styles
  - Word's native Heading styles (not fake bolded text)
  - Consistent formatting across platforms

### 2. PDF Generation: WeasyPrint from HTML
- **Why**: WeasyPrint produces high-quality PDFs with real text layers
- **Alternative available**: LibreOffice headless (fallback option)
- **Benefits**:
  - CSS-based styling (easier to maintain)
  - Professional typography
  - Guaranteed text layer (no image flattening)

### 3. Self-Check Validation via Parser Re-run
- **Why**: Leverages existing Step 2 parser infrastructure
- **How**: Re-parse generated file and compare with original
- **Threshold**: 80% field recovery rate
- **Rationale**: Catches common ATS issues (images, unselectable text, formatting problems)

### 4. Validation Only for PDF (MVP)
- **Why**: DOCX validation requires LibreOffice conversion to PDF first
- **MVP Scope**: Focus on PDF validation (most critical for ATS)
- **Future**: Add DOCX → PDF → validation flow in post-MVP

### 5. Blocking Downloads on Validation Failure
- **Why**: Prevent users from submitting broken files to ATS systems
- **UX**: Clear error message explaining the issue
- **Guidance**: Shows which fields are missing/unrecoverable

## Security & Authorization

### Row-Level Security (RLS)
- Users can only view their own export_jobs
- Users can only create exports for their own resumes
- Download endpoint verifies job ownership

### Storage Access
- Exports stored in user-scoped paths: `exports/{user_id}/{job_id}.{format}`
- Temporary validation files cleaned up after use
- Service role used for storage operations

### JWT Authentication
- All endpoints require valid JWT token
- Token validated via Supabase Auth
- User ID extracted from token claims

## Error Handling

### Backend Errors
1. **Resume Not Found**: 404 if resume_id or version_id invalid
2. **Generation Failure**: Catches exceptions, updates job status to failed
3. **Validation Failure**: Records validation_passed = false with details
4. **Storage Failure**: 500 if file upload/download fails
5. **Parser Failure**: Captured in validation_details.parsing_errors

### Frontend Errors
1. **API Errors**: Extracts error.detail from response
2. **Network Errors**: Generic fallback message
3. **Timeout**: Max 30 polling attempts (30 seconds)
4. **Validation Failure**: Blocks download, shows clear message

## Testing Strategy

### Manual Testing Checklist
- [ ] Export PDF with valid resume → validation passes → download works
- [ ] Export DOCX with valid resume → skips validation → download works
- [ ] Check self-check metrics displayed correctly
- [ ] Verify downloaded PDF has selectable text (not images)
- [ ] Verify DOCX opens in Word with proper styles
- [ ] Test validation failure handling (artificially break content)
- [ ] Verify blocked download when validation fails
- [ ] Test with resume containing all section types
- [ ] Test with minimal resume (only contact + summary)
- [ ] Test error handling (invalid resume_id, network issues)

### Validation Testing
To test validation failure detection:
1. Temporarily modify `export_service.py` to inject image content
2. Generate export
3. Verify validation_passed = false
4. Verify download is blocked
5. Check missing_fields list is populated

## Configuration

### Environment Variables
- `SUPABASE_URL`: For storage access
- `SUPABASE_SERVICE_ROLE_KEY`: For service operations
- `ANTHROPIC_API_KEY`: For parser validation (LLM extraction)
- `ANTHROPIC_HAIKU_MODEL`: Model for parser

### Dependencies (requirements.txt)
```
python-docx>=1.1.0     # DOCX generation
weasyprint>=62.0       # PDF generation
jinja2                 # HTML templating (included with FastAPI)
```

### Storage Bucket
- **Bucket**: `resumes` (existing)
- **Paths**:
  - `exports/{user_id}/{job_id}.pdf`
  - `exports/{user_id}/{job_id}.docx`
  - `temp_exports/{user_id}/{timestamp}.pdf` (validation temp files)

## Future Enhancements

### Post-MVP
1. **DOCX Validation**: Add LibreOffice headless conversion for DOCX self-check
2. **Custom Templates**: Allow users to choose from multiple resume templates
3. **Batch Export**: Export multiple versions at once
4. **Preview**: Show preview before download
5. **Export History**: List all past exports in UI
6. **Format Options**: Allow font/color customization
7. **ATS Scoring**: Display predicted ATS score for exported file
8. **Direct Submit**: Integration with job application APIs

### Performance Optimizations
1. **Async Processing**: Move to RQ background jobs for large resumes
2. **Caching**: Cache generated exports for 24 hours
3. **CDN**: Serve downloads through CDN for faster access
4. **Compression**: Optimize PDF file size

## Troubleshooting

### Common Issues

**Issue**: WeasyPrint fails to install
- **Cause**: Missing system dependencies (Cairo, Pango)
- **Fix**: Install system libs: `apt-get install libpango-1.0-0 libpangocairo-1.0-0` (Linux)
- **Windows**: Use `weasyprint` binary installer or WSL

**Issue**: Validation always fails
- **Cause**: Parser can't extract text from generated PDF
- **Debug**: Check PDF text layer with `pdftotext` command
- **Fix**: Verify WeasyPrint configuration, check font availability

**Issue**: Download button not appearing
- **Cause**: Frontend not polling long enough
- **Fix**: Increase `maxAttempts` in `pollExportJob()`

**Issue**: Missing fields in validation
- **Cause**: Content too short or special characters
- **Fix**: Check `_compare_parsed_data()` logic, adjust threshold

## Files Created/Modified

### New Files
- `apps/api/migrations/010_export_jobs.sql` - Database migration
- `apps/api/models/export.py` - Pydantic models
- `apps/api/services/export_service.py` - Export generation & validation
- `apps/api/routers/exports.py` - API endpoints
- `apps/api/templates/resume_pdf.html` - PDF template

### Modified Files
- `apps/api/requirements.txt` - Added weasyprint
- `apps/api/main.py` - Registered exports router
- `apps/web/src/app/resumes/[id]/editor/page.tsx` - Added export UI

## API Documentation

### POST /api/exports/resumes/{resume_id}/export

**Request**:
```json
{
  "format": "pdf",
  "version_id": "optional-uuid-or-null-for-current"
}
```

**Response (201)**:
```json
{
  "job_id": "uuid",
  "message": "Export completed successfully"
}
```

### GET /api/exports/{job_id}

**Response (200)**:
```json
{
  "id": "uuid",
  "status": "completed",
  "format": "pdf",
  "validation_passed": true,
  "validation_details": {
    "fields_checked": 25,
    "fields_recovered": 24,
    "missing_fields": [],
    "parsing_errors": []
  },
  "error_message": null,
  "created_at": "2026-09-16T10:30:00Z"
}
```

### GET /api/exports/{job_id}/download

**Response (200)**:
- Binary file content
- Headers:
  - `Content-Type`: application/pdf or application/vnd.openxmlformats-officedocument.wordprocessingml.document
  - `Content-Disposition`: attachment; filename="resume_{job_id}.{format}"
  - `Content-Length`: file size in bytes

**Error (400)**: Validation failed, download blocked
```json
{
  "detail": "Export failed validation self-check. The generated file does not contain recoverable text. Please contact support."
}
```

## Success Criteria

✅ **Definition of Done**:
1. Both PDF and DOCX exports produce files with real, selectable text (not images)
2. Consistent professional formatting across both formats
3. Self-check validation correctly detects validation failures
4. Self-check validation passes for properly-formatted exports
5. User sees clear pass/fail result before download
6. Download is blocked if validation fails
7. Export button integrated into editor page
8. Modal shows validation details and download option
9. All API endpoints properly authenticated and authorized
10. Error handling covers all edge cases

## Next Steps

After Step 9 completion:
1. Run manual testing checklist
2. Test with diverse resume content (long, short, special characters)
3. Verify WeasyPrint installation on deployment environment
4. Consider adding export analytics/tracking
5. Document export best practices for users
6. Plan Step 10 features based on user feedback
