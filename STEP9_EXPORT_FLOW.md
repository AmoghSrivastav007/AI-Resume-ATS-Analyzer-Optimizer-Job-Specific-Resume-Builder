# Step 9: Export System Flow Diagram

## User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                        RESUME EDITOR PAGE                        │
│                                                                  │
│  [Undo] [Redo]  [📥 Export]  [View Analysis]                   │
│                       ↓                                          │
│                  User clicks                                     │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                      EXPORT MODAL OPENS                          │
│                                                                  │
│  Export Format:                                                 │
│  ( ) PDF (with self-check validation)                          │
│  (•) DOCX (Microsoft Word)                                      │
│                                                                  │
│  [Export]  [Cancel]                                             │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
                  User clicks Export
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND: Loading State                       │
│                                                                  │
│  🔄 Generating and validating export...                         │
│                                                                  │
│  POST /api/exports/resumes/{id}/export                          │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND: Create Export Job                          │
│                                                                  │
│  1. Create export_jobs record (status: generating)              │
│  2. Fetch resume_blocks from database                           │
│  3. Generate file:                                              │
│     • DOCX: python-docx direct generation                       │
│     • PDF: WeasyPrint from HTML template                        │
│  4. Update status: validating                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│           BACKEND: Self-Check Validation (PDF only)             │
│                                                                  │
│  1. Upload generated file to temp storage                       │
│  2. Create temp resume_version record                           │
│  3. Run ResumeParsePipeline (Step 2 parser)                     │
│  4. Extract text from generated file                            │
│  5. Compare with original resume_blocks                         │
│  6. Calculate recovery rate                                     │
│  7. PASS if ≥80% fields recovered                               │
│  8. Clean up temp data                                          │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│             BACKEND: Store Results                               │
│                                                                  │
│  1. Upload file to Supabase Storage                             │
│     Path: exports/{user_id}/{job_id}.{format}                   │
│  2. Update export_jobs:                                         │
│     • status: completed                                         │
│     • validation_passed: true/false                             │
│     • validation_details: {...}                                 │
│     • storage_path: ...                                         │
│  3. Return job_id to frontend                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│          FRONTEND: Poll Job Status                               │
│                                                                  │
│  Loop (max 30 attempts):                                        │
│    GET /api/exports/{job_id}                                    │
│    If status === "completed" → break                            │
│    If status === "failed" → show error                          │
│    Wait 1 second                                                │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
              ┌────────┴────────┐
              ↓                 ↓
┌─────────────────────┐  ┌──────────────────────┐
│  VALIDATION PASSED  │  │  VALIDATION FAILED   │
│                     │  │                      │
│  ✅ Export Ready   │  │  ❌ Validation Failed│
│                     │  │                      │
│  Self-Check Results:│  │  Some content could  │
│  • 24/25 fields     │  │  not be recovered as │
│    recovered        │  │  selectable text.    │
│  • All content is   │  │                      │
│    selectable text  │  │  Fields Checked: 25  │
│                     │  │  Fields Recovered: 15│
│  [📥 Download]     │  │                      │
│  [Close]            │  │  Missing Fields:     │
│                     │  │  • Block 3: ...      │
│                     │  │  • Block 7: ...      │
│                     │  │                      │
│                     │  │  ⚠️ Download blocked │
│                     │  │                      │
│                     │  │  [Close]             │
└─────────┬───────────┘  └──────────────────────┘
          ↓
   User clicks Download
          ↓
┌─────────────────────────────────────────────────────────────────┐
│          FRONTEND: Download File                                 │
│                                                                  │
│  GET /api/exports/{job_id}/download                             │
│  • Receives binary file                                         │
│  • Creates blob URL                                             │
│  • Triggers browser download                                    │
│  • Filename: resume_{job_id}.{format}                           │
└─────────────────────────────────────────────────────────────────┘
```

## Validation Decision Tree

```
                    Generate File
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
           PDF File              DOCX File
              ↓                     ↓
       Run Self-Check        Skip Validation
       (Re-parse file)         (MVP scope)
              ↓                     ↓
       ┌──────┴──────┐             ↓
       ↓             ↓             ↓
   Recovery      Recovery       Always
   Rate ≥80%     Rate <80%      Pass
       ↓             ↓             ↓
   ✅ PASS       ❌ FAIL        ✅ PASS
       ↓             ↓             ↓
   Allow         Block          Allow
   Download      Download       Download
```

## Component Interaction Diagram

```
┌──────────────────┐
│  Editor Page     │
│  (React)         │
└────────┬─────────┘
         │ 1. POST /api/exports/resumes/{id}/export
         │    { format: "pdf", version_id: null }
         ↓
┌──────────────────┐
│  Exports Router  │
│  (FastAPI)       │
└────────┬─────────┘
         │ 2. Create job record
         │ 3. Call service methods
         ↓
┌──────────────────┐
│  Export Service  │
│  (Python)        │
├──────────────────┤
│ • generate_docx()│──→  python-docx
│ • generate_pdf() │──→  WeasyPrint ──→ HTML Template
│ • validate_export│──→  ResumeParsePipeline
└────────┬─────────┘
         │ 4. Fetch data
         ↓
┌──────────────────┐
│  Supabase Client │
├──────────────────┤
│ • resume_versions│
│ • resume_sections│
│ • resume_blocks  │
│ • export_jobs    │
│ • Storage        │
└──────────────────┘
```

## Data Flow

```
Database (Postgres)
    ↓
resume_blocks
    ↓
Export Service
    ↓
    ├─→ DOCX Generator ──→ python-docx ──→ .docx file
    │                                         ↓
    └─→ PDF Generator ──→ Jinja2 Template ─→ HTML
                              ↓
                          WeasyPrint
                              ↓
                          .pdf file
                              ↓
                          Validator
                              ↓
                       Re-parse Check
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
                 ✅ Pass            ❌ Fail
                    ↓                   ↓
             Supabase Storage      Block Download
                    ↓
               User Download
```

## Validation Process Detail

```
┌────────────────────────────────────────────────────────────┐
│  Original Resume Data                                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Section: Experience                                 │   │
│  │ Block 1: "Led team of 5 engineers..."              │   │
│  │ Block 2: "Increased performance by 40%..."         │   │
│  │ Block 3: "Implemented CI/CD pipeline..."           │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────┬────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  Generate PDF                                               │
│  • Render blocks as text in PDF                            │
│  • Apply formatting (fonts, spacing, bullets)              │
│  • Create real text layer (not images)                     │
└───────────────────────┬────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  Upload to Temp Storage                                     │
│  temp_exports/{user_id}/{timestamp}.pdf                     │
└───────────────────────┬────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  Re-run Step 2 Parser                                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Extract text from PDF                               │   │
│  │ Run LLM extraction                                  │   │
│  │ Populate resume_sections & resume_blocks            │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────┬────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  Re-parsed Resume Data                                      │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Section: Experience                                 │   │
│  │ Block 1: "Led team of 5 engineers..."   ✅         │   │
│  │ Block 2: "Increased performance by 40%..." ✅       │   │
│  │ Block 3: "Implemented CI/CD pipeline..."   ✅       │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────┬────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  Compare Original vs. Re-parsed                             │
│                                                             │
│  Original Blocks: 25                                        │
│  Recovered Blocks: 24                                       │
│  Missing Blocks: 1                                          │
│                                                             │
│  Recovery Rate: 24/25 = 96% ✅                             │
│  Threshold: 80%                                             │
│  Result: PASS                                               │
└───────────────────────┬────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  Update export_jobs                                         │
│  validation_passed: true                                    │
│  validation_details: {                                      │
│    fields_checked: 25,                                      │
│    fields_recovered: 24,                                    │
│    missing_fields: ["Block 17: ..."],                       │
│    recovery_rate: 0.96                                      │
│  }                                                          │
└────────────────────────────────────────────────────────────┘
```

## Error Scenarios

```
Scenario 1: Network Error
User clicks Export → Network fails
└─→ Show error: "Failed to create export job"
    [Close] modal

Scenario 2: Generation Error
User clicks Export → Service throws exception
└─→ Backend updates job status: failed
    └─→ Frontend polls → sees failed status
        └─→ Show error: error_message from job
            [Close] modal

Scenario 3: Validation Fails
User clicks Export → PDF generated → Parser extracts only 15/25 fields
└─→ validation_passed: false
    └─→ Frontend displays:
        ❌ Validation Failed
        Fields Recovered: 15/25
        Missing Fields: [list...]
        ⚠️ Download blocked
        [Close] modal

Scenario 4: Download Fails
User clicks Download → Storage error
└─→ Show error: "Failed to download file"
    [Try Again] [Close]
```

## Timeline

```
T+0ms:   User clicks Export button
T+50ms:  Modal opens
T+100ms: User selects format, clicks Export
T+150ms: Frontend sends POST request
T+200ms: Backend creates job record
T+300ms: Backend generates DOCX/PDF (varies by size)
T+2000ms: Backend runs validation (PDF only)
T+2500ms: Backend uploads to storage
T+2600ms: Backend updates job: completed
T+2700ms: Frontend poll gets completed status
T+2750ms: Frontend displays validation results
T+3000ms: User clicks Download
T+3100ms: File downloads to user's device
```

---

**Key Takeaways**:
- Export flow is synchronous but provides real-time feedback
- Validation is automatic and blocks bad exports
- Clear user feedback at every stage
- Error handling prevents silent failures
- Download only allowed after validation passes
