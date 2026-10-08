# Step 8 Backend Complete: Interactive Editor API

**Status**: ✅ Backend API Complete, Frontend Implementation Required  
**Date**: December 2024  
**Components**: Block editing, AI rewrites with Truth Guard, Version history

---

## Overview

Step 8 implements the backend API for an interactive resume editor. All components follow the requirements:
- ✅ Block-level editing (PATCH /api/resume-blocks/:id)
- ✅ AI rewrites with Truth Guard integration (POST /api/resume-blocks/:id/ai-rewrite)
- ✅ Version history management (restore, duplicate, rename, delete)
- ✅ Block operations (create, delete, reorder)

**Key Feature**: All AI rewrites go through the same Truth Guard pipeline as Step 7, preventing hallucinations.

---

## API Endpoints

### Block Editing

#### GET /api/resume-blocks/{block_id}
Get a single block by ID.

**Response**:
```json
{
  "id": "uuid",
  "resume_version_id": "uuid",
  "section_id": "uuid",
  "user_id": "uuid",
  "block_type": "bullet",
  "content": {"text": "Built 5 REST APIs..."},
  "sort_order": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### PATCH /api/resume-blocks/{block_id}
Manually update a block (direct user editing).

**Request**:
```json
{
  "content": {"text": "Updated text..."},
  "block_type": "bullet"  // optional
}
```

**Response**: Updated block

---

### AI-Powered Rewrites (Truth Guard)

#### POST /api/resume-blocks/{block_id}/ai-rewrite
AI-powered rewrite with hallucination prevention.

**Request**:
```json
{
  "instruction": "shorten",  // shorten|expand|fix_grammar|improve
  "context": "Optional additional context"  // optional
}
```

**Response**:
```json
{
  "original_text": "Original bullet text...",
  "proposed_text": "Improved bullet text...",
  "verification_status": "supported",  // supported|partially_supported|unsupported
  "guardrails_passed": true,
  "reasoning": "Explanation from verifier",
  "warnings": [],
  "supported_claims": ["claim 1", "claim 2"],
  "unsupported_claims": []
}
```

**Instructions**:
- `shorten`: Make more concise (uses Haiku)
- `expand`: Add detail from fact ledger only (uses Sonnet)
- `fix_grammar`: Fix grammar/punctuation (uses Haiku)
- `improve`: Better verbs and phrasing (uses Sonnet)

**Truth Guard Process**:
1. Fetch block and fact ledger
2. Generate rewrite (Haiku for simple, Sonnet for complex)
3. Independent verification (Haiku)
4. Deterministic guardrails (hard blocks)
5. Return proposed rewrite with status

**Verification Statuses**:
- `supported`: Auto-approved, safe to apply
- `partially_supported`: Requires user confirmation (vague claims)
- `unsupported`: Contains hallucinations, should NOT be applied

#### POST /api/resume-blocks/{block_id}/apply-rewrite
Apply an AI-generated rewrite.

**Request**:
```json
{
  "proposed_text": "Text from ai-rewrite response"
}
```

**Response**: Updated block

---

### Block Operations

#### POST /api/resume-blocks/sections/{section_id}/blocks
Create a new block in a section.

**Request**:
```json
{
  "content": {"text": "New bullet point..."},
  "block_type": "bullet"
}
```

**Response**: Created block (201)

#### DELETE /api/resume-blocks/{block_id}
Delete a block.

**Response**: 204 No Content

#### POST /api/resume-blocks/sections/{section_id}/reorder
Reorder blocks within a section (drag-and-drop).

**Request**:
```json
{
  "block_ids": ["uuid1", "uuid2", "uuid3"]  // New order
}
```

**Response**:
```json
{
  "success": true,
  "message": "Blocks reordered successfully"
}
```

---

### Version History

#### GET /api/versions/resume/{resume_id}
List all versions for a resume.

**Response**:
```json
{
  "resume_id": "uuid",
  "resume_title": "Software Engineer Resume",
  "current_version_id": "uuid",
  "versions": [
    {
      "id": "uuid",
      "resume_id": "uuid",
      "user_id": "uuid",
      "version_number": 3,
      "status": "parsed",
      "storage_path": "path/to/file.pdf",
      "original_filename": "resume.pdf",
      "mime_type": "application/pdf",
      "file_size_bytes": 102400,
      "needs_ocr": false,
      "parse_error": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /api/versions/{version_id}
Get a specific version by ID.

**Response**: Single version object

#### POST /api/versions/{version_id}/restore
Restore a previous version (creates new version with old content).

**Response**: New version (201)

**Process**:
1. Fetch old version and all its content
2. Create new version with incremented version_number
3. Copy all sections, blocks, and fact ledger
4. Set as current version

#### POST /api/versions/{version_id}/duplicate
Duplicate a version as a new resume.

**Request**:
```json
{
  "new_title": "Data Analyst Resume"  // optional
}
```

**Response**: New version (201)

**Process**:
1. Create new resume with new title
2. Create version 1 of new resume
3. Copy all content from source version
4. Useful for creating job-specific variations

#### PATCH /api/versions/{version_id}/rename
Rename a resume.

**Request**:
```json
{
  "title": "Senior Software Engineer Resume"
}
```

**Response**: Updated version

#### DELETE /api/versions/{version_id}
Delete a version.

**Response**: 204 No Content

**Rules**:
- Cannot delete the current version
- Must set a different version as current first

---

## Implementation Details

### Files Created

**Routers**:
- `apps/api/routers/blocks.py` - Block editing endpoints
- `apps/api/routers/versions.py` - Version history endpoints

**Services**:
- `apps/api/services/block_editor_service.py` - Block editing logic
- `apps/api/services/version_service.py` - Version control logic

**Updated**:
- `apps/api/main.py` - Router registration

---

## Truth Guard Integration

All AI rewrites use the same hallucination prevention pipeline as Step 7:

### 1. Constrained Generation
- Haiku for simple instructions (shorten, fix_grammar)
- Sonnet for complex instructions (expand, improve)
- Prompt explicitly forbids fabrication
- Only allows rephrasing or additions from fact ledger

### 2. Independent Verification
- Uses Haiku (different model)
- Sees only fact ledger + proposed text
- No access to generator's reasoning
- Classifies as SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED

### 3. Deterministic Guardrails
- Hard blocks for company/title/date changes
- Skill/technology verification against ledger
- Numeric claim validation
- Runs regardless of verifier verdict

### 4. Status Assignment
- SUPPORTED + guardrails passed = auto-approved
- PARTIALLY_SUPPORTED = requires confirmation
- UNSUPPORTED or failed guardrails = do not apply

**Zero tolerance for hallucinations applies to ALL rewrites.**

---

## Model Selection

Instruction complexity determines model choice:

| Instruction | Model | Reason |
|-------------|-------|--------|
| `shorten` | Haiku | Simple text reduction |
| `fix_grammar` | Haiku | Mechanical fixes only |
| `expand` | Sonnet | Needs to find relevant facts |
| `improve` | Sonnet | Complex phrasing decisions |

**Cost optimization**: Use cheaper Haiku where possible, Sonnet where needed.

---

## Version Control Strategy

### Undo/Redo (Client-Side Recommended)

For Step 8 MVP, implement **client-side undo/redo**:
- Track state changes in React state
- Simple undo/redo stack
- No server-side complexity

**Why client-side**:
- Simpler implementation
- Faster UX (no network calls)
- No need for complex server-side history tracking
- Sufficient for MVP

**Server-side alternative** (future):
- Use `resume_versions.parent_version_id` chain
- Track every change as micro-version
- More complex, overkill for MVP

### Version History (Server-Side)

Version history is **server-side**:
- Each save creates a new version
- User can restore to any previous version
- Versions are immutable snapshots

**Use cases**:
- "I want to go back to yesterday's version"
- "Compare current vs last week"
- "Duplicate for different job application"

---

## Real-Time Re-Analysis

Per architecture §3 correction:

### Deterministic Scores (Instant)
Recompute **locally/instantly** on edit:
- ATS keyword matching
- Formatting checks
- Length validation
- Contact info presence

**Implementation**: Frontend calculates after each edit

### LLM-Dependent Scores (Debounced)
Recompute only on:
- Explicit "Re-analyze" button
- Or 10+ seconds of no typing (debounce)

**LLM-dependent scores**:
- Content Quality (requires Anthropic call)
- JD Match semantic layers (requires embedding + LLM)

**Why debounced**:
- Expensive ($0.10-0.50 per analysis)
- Slow (5-15 seconds)
- Wasteful on every keystroke

**DO NOT** fire LLM calls on every keystroke.

---

## Frontend Requirements (Step 8 Next)

### 1. Editor Page: /resumes/[id]/editor

**Layout**:
- Left: Section tree (Header, Summary, Experience, etc.)
- Center: Editable blocks
- Right: AI rewrite panel (optional)

**Features**:
- Inline editing (contentEditable or textarea)
- Add/remove bullets
- Drag-and-drop section reordering
- Block operations (create, delete, reorder)

**Components**:
- `<ResumeEditor>` - Main editor container
- `<SectionList>` - Section navigation
- `<BlockEditor>` - Individual block editing
- `<AIRewritePanel>` - AI suggestions

### 2. AI Rewrite Panel

**Flow**:
1. Select block
2. Choose instruction (shorten/expand/fix_grammar/improve)
3. Click "Rewrite"
4. Show loading state
5. Display proposed rewrite with verification badge
6. Show warnings if any
7. Apply/Edit/Reject buttons

**Verification Badges**:
- 🟢 **SUPPORTED**: Safe to apply (auto-approved)
- 🟡 **PARTIALLY_SUPPORTED**: Review carefully (requires confirmation)
- 🔴 **UNSUPPORTED**: Do not apply (hallucination detected)

**Confirmation Modal** (for PARTIALLY_SUPPORTED):
```
⚠️ Verification Warning

This rewrite contains claims that aren't fully supported by your resume:
- "Excellent communicator" (vague, no evidence)

Do you have genuine experience demonstrating this? Only add if true.

[Cancel] [Yes, I have this experience]
```

### 3. Version History Panel

**Features**:
- List all versions (newest first)
- Show version number, date, status
- Current version badge
- Actions: View, Restore, Duplicate, Rename, Delete

**Layout**:
```
📄 Version 3 (Current)
   Created: 2024-01-15
   Status: Parsed
   [View] [Rename]

📄 Version 2
   Created: 2024-01-10
   Status: Parsed
   [View] [Restore] [Duplicate] [Delete]

📄 Version 1
   Created: 2024-01-01
   Status: Parsed
   [View] [Restore] [Duplicate] [Delete]
```

### 4. Tabbed Analysis Screen

**Tabs** (using data from Steps 4-7):
- Overview (General Quality Score + summary)
- ATS (ATS compatibility score + issues)
- Keywords (Keyword analysis)
- Skills (Skills assessment)
- Experience (Experience evaluation)
- Formatting (Formatting issues)
- Grammar (Grammar/content quality issues)
- JD Match (JD Match Score + gaps) - if JD uploaded
- Recommendations (Optimization suggestions)

**Layout**:
```
┌─────────────────┬───────────────────────────────┐
│                 │                               │
│  Resume Preview │   Analysis Panel              │
│                 │                               │
│  (Read-only)    │   [Overview|ATS|Keywords|...] │
│                 │                               │
│                 │   Score: 85/100               │
│                 │                               │
│                 │   Issues:                     │
│                 │   • Missing phone number      │
│                 │   • Weak action verbs         │
│                 │                               │
│                 │   Click issue → highlight     │
│                 │   in preview                  │
│                 │                               │
└─────────────────┴───────────────────────────────┘
```

**Issue Highlighting**:
- Click issue in panel → highlights affected block in preview
- Uses `affected_block_id` from issues table

### 5. Undo/Redo

**Client-Side Implementation**:
```typescript
const [history, setHistory] = useState<State[]>([initialState]);
const [currentIndex, setCurrentIndex] = useState(0);

const undo = () => {
  if (currentIndex > 0) {
    setCurrentIndex(currentIndex - 1);
  }
};

const redo = () => {
  if (currentIndex < history.length - 1) {
    setCurrentIndex(currentIndex + 1);
  }
};

const pushState = (newState: State) => {
  // Truncate future history
  const newHistory = history.slice(0, currentIndex + 1);
  newHistory.push(newState);
  setHistory(newHistory);
  setCurrentIndex(newHistory.length - 1);
};
```

**UI**:
```
[↶ Undo] [↷ Redo]  Cmd+Z / Cmd+Shift+Z
```

---

## Testing

### Manual Testing Checklist

**Block Editing**:
- [ ] Can edit block text (PATCH /api/resume-blocks/:id)
- [ ] Can create new block (POST /sections/:id/blocks)
- [ ] Can delete block (DELETE /api/resume-blocks/:id)
- [ ] Can reorder blocks (POST /sections/:id/reorder)

**AI Rewrites**:
- [ ] Can shorten text (Haiku, Truth Guard)
- [ ] Can expand text (Sonnet, Truth Guard)
- [ ] Can fix grammar (Haiku, Truth Guard)
- [ ] Can improve phrasing (Sonnet, Truth Guard)
- [ ] Verify SUPPORTED status for good rewrites
- [ ] Verify PARTIALLY_SUPPORTED for vague claims
- [ ] Verify UNSUPPORTED for hallucinations
- [ ] Guardrails block company/title/date changes

**Version History**:
- [ ] Can list versions (GET /versions/resume/:id)
- [ ] Can view specific version (GET /versions/:id)
- [ ] Can restore version (POST /versions/:id/restore)
- [ ] Can duplicate version (POST /versions/:id/duplicate)
- [ ] Can rename resume (PATCH /versions/:id/rename)
- [ ] Can delete version (DELETE /versions/:id)
- [ ] Cannot delete current version

### API Testing

```bash
# Get block
curl http://localhost:8000/api/resume-blocks/{block_id} \
  -H "Authorization: Bearer $TOKEN"

# Update block
curl -X PATCH http://localhost:8000/api/resume-blocks/{block_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": {"text": "Updated text"}}'

# AI rewrite
curl -X POST http://localhost:8000/api/resume-blocks/{block_id}/ai-rewrite \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instruction": "improve"}'

# List versions
curl http://localhost:8000/api/versions/resume/{resume_id} \
  -H "Authorization: Bearer $TOKEN"

# Restore version
curl -X POST http://localhost:8000/api/versions/{version_id}/restore \
  -H "Authorization: Bearer $TOKEN"
```

---

## Performance Considerations

### AI Rewrite Latency
- **Haiku** (shorten, fix_grammar): 2-5 seconds
- **Sonnet** (expand, improve): 5-10 seconds
- Show loading spinner during rewrite

### Version Operations
- **Restore**: 5-10 seconds (copying all content)
- **Duplicate**: 5-10 seconds (creating new resume)
- Show progress indicator

### Re-Analysis
- **Deterministic**: Instant (client-side)
- **LLM-dependent**: 10-30 seconds (debounced)
- Only on "Re-analyze" button or 10s debounce

---

## Cost Optimization

### AI Rewrites
- Use Haiku where possible ($0.25 per 1M input tokens)
- Sonnet only for complex instructions ($3 per 1M)
- Typical cost per rewrite: $0.001-0.01

### Re-Analysis
- Don't fire on every keystroke
- Debounce to 10+ seconds
- Or explicit "Re-analyze" button
- Typical cost per analysis: $0.10-0.50

---

## Security

### Authorization
- All endpoints require JWT auth
- All queries filter by `user_id`
- Users can only edit their own blocks

### Input Validation
- Block content validated (max length)
- Instruction must be one of: shorten, expand, fix_grammar, improve
- Block IDs validated as UUIDs

### Rate Limiting (Future)
- Limit AI rewrites per user per hour
- Prevent abuse of expensive operations

---

## Next Steps

### Immediate: Frontend Implementation

1. **Create editor page**: `apps/web/src/app/resumes/[id]/editor/page.tsx`
2. **Create components**:
   - ResumeEditor
   - SectionList
   - BlockEditor
   - AIRewritePanel
   - VersionHistoryPanel
3. **Create analysis page**: `apps/web/src/app/resumes/[id]/analysis/page.tsx`
4. **Implement tabbed interface**
5. **Add issue highlighting**
6. **Implement undo/redo**

### Testing

1. **Unit tests** for services
2. **Integration tests** for API endpoints
3. **E2E tests** for editor flow
4. **Manual testing** with real resumes

### Future Enhancements

1. **Real-time collaboration** (multiple users editing)
2. **Comments and annotations**
3. **Compare versions side-by-side**
4. **Export to different formats**
5. **Template library**

---

## Definition of Done

### ✅ Backend (COMPLETE)
- [x] Block editing endpoints (GET, PATCH, DELETE, POST)
- [x] AI rewrite with Truth Guard (POST /ai-rewrite, POST /apply-rewrite)
- [x] Block operations (create, reorder)
- [x] Version history (list, get, restore, duplicate, rename, delete)
- [x] Services implemented (BlockEditorService, VersionService)
- [x] Routers registered in main.py
- [x] Documentation complete

### 🔲 Frontend (TODO)
- [ ] Editor page created
- [ ] Block editing UI
- [ ] AI rewrite panel
- [ ] Version history panel
- [ ] Tabbed analysis screen
- [ ] Issue highlighting
- [ ] Undo/redo
- [ ] Real-time re-analysis (debounced)

### 🔲 Testing (TODO)
- [ ] API tests for all endpoints
- [ ] Service tests
- [ ] Integration tests
- [ ] E2E tests

---

## Conclusion

**Step 8 Backend**: ✅ COMPLETE

The backend API provides all necessary endpoints for:
- Interactive block editing
- AI-powered rewrites with hallucination prevention
- Version history management
- Block operations

**All AI rewrites go through Truth Guard (Step 7)**, ensuring zero tolerance for hallucinations even in inline editing.

**Next**: Implement the frontend editor UI to provide a complete interactive editing experience.

---

**Last Updated**: Step 8 Backend Implementation  
**Next Milestone**: Step 8 Frontend Implementation  
**Project Progress**: 7/12 steps (58%) → 8/12 steps (67%) after frontend
