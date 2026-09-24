# Quick Start - Step 8 Integration

**TL;DR**: Editor page is done ✅. Analysis page and Version History need 3-5 hours of integration work. Follow the guides below.

---

## Current Status

| Component | Status | Time to Complete |
|-----------|--------|------------------|
| Editor Page | ✅ Done | 0 hours |
| Analysis Page | ⚠️ Pending | 2-3 hours |
| Version History | ⚠️ Pending | 1-2 hours |
| **Total** | **70% Complete** | **3-5 hours** |

---

## To Complete Analysis Page

### File: `apps/web/src/app/resumes/[id]/analysis/page.tsx`

### Quick Steps:
1. Add auth helper at top of component
2. Replace `loadAnalysisData()` mock with real API call
3. Replace `loadIssues()` mock with real API call
4. Add `loadResumePreview()` for blocks
5. Implement `reanalyze()` function
6. Map analysis data to tabs

### Copy-Paste Helper:
```typescript
// 1. Add auth helper
const getAuthHeaders = () => {
  const token = localStorage.getItem('supabase.auth.token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

// 2. Replace loadAnalysisData
const loadAnalysisData = async () => {
  setIsLoading(true);
  try {
    const resumeResponse = await fetch(`/api/resumes/${resumeId}`, {
      headers: getAuthHeaders(),
    });
    
    if (!resumeResponse.ok) throw new Error('Failed to load resume');
    
    const resumeData = await resumeResponse.json();
    const versionId = resumeData.data.current_version_id;
    
    // Run new analysis
    const analysisResponse = await fetch(`/api/analyses`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        analysis_type: 'ats',
        resume_version_id: versionId,
      }),
    });
    
    const analysis = await analysisResponse.json();
    
    // Get detailed results
    const detailsResponse = await fetch(`/api/analyses/${analysis.id}`, {
      headers: getAuthHeaders(),
    });
    
    const details = await detailsResponse.json();
    setAnalysisData(details.analysis);
    setIssues(details.issues);
  } catch (error) {
    console.error('Error loading analysis:', error);
    alert('Failed to load analysis');
  } finally {
    setIsLoading(false);
  }
};
```

**Full Guide**: See `STEP8_REMAINING_WORK.md` section "Analysis Page Integration"

---

## To Complete Version History

### File: `apps/web/src/components/VersionHistory.tsx`

### Quick Steps:
1. Add auth helper
2. Replace mock versions with API call
3. Implement restore action
4. Implement duplicate action
5. Implement rename action
6. Implement delete action

### Copy-Paste Helper:
```typescript
// 1. Add auth helper (same as above)
const getAuthHeaders = () => { ... };

// 2. Load versions
const loadVersions = async () => {
  setIsLoading(true);
  try {
    const response = await fetch(`/api/versions/resume/${resumeId}`, {
      headers: getAuthHeaders(),
    });
    
    if (!response.ok) throw new Error('Failed to load versions');
    
    const data = await response.json();
    setVersions(data.versions);
    setCurrentVersionId(data.current_version_id);
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to load versions');
  } finally {
    setIsLoading(false);
  }
};

// 3. Restore version
const restoreVersion = async (versionId: string) => {
  if (!confirm('Restore this version?')) return;
  
  try {
    const response = await fetch(`/api/versions/${versionId}/restore`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    
    if (!response.ok) throw new Error('Failed to restore');
    
    alert('✅ Restored!');
    await loadVersions();
    window.location.reload();
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to restore');
  }
};
```

**Full Guide**: See `STEP8_REMAINING_WORK.md` section "Version History Integration"

---

## API Endpoints Reference

### Block Editing (✅ Already Integrated)
- `GET /api/resumes/{id}` - Load resume
- `PATCH /api/resume-blocks/{id}` - Update block
- `POST /api/resume-blocks/{id}/ai-rewrite` - AI rewrite
- `POST /api/resume-blocks/{id}/apply-rewrite` - Apply rewrite
- `POST /api/resume-blocks/sections/{id}/blocks` - Create block
- `DELETE /api/resume-blocks/{id}` - Delete block

### Analysis (⚠️ Needs Integration)
- `POST /api/analyses` - Run analysis
- `GET /api/analyses/{id}` - Get results
- `GET /api/analyses/{id}/explain/{category}` - Category details

### Version History (⚠️ Needs Integration)
- `GET /api/versions/resume/{id}` - List versions
- `POST /api/versions/{id}/restore` - Restore
- `POST /api/versions/{id}/duplicate` - Duplicate
- `PATCH /api/versions/{id}/rename` - Rename
- `DELETE /api/versions/{id}` - Delete

---

## Testing Checklist

### After Completing Analysis Page
- [ ] Loads analysis on mount
- [ ] Shows overall score
- [ ] Shows issues in tabs
- [ ] Re-analyze button works
- [ ] Click issue highlights block
- [ ] Loading spinner appears
- [ ] Errors display properly

### After Completing Version History
- [ ] Loads version list
- [ ] Shows current version badge
- [ ] Restore creates new version
- [ ] Duplicate creates new resume
- [ ] Rename updates title
- [ ] Delete removes version
- [ ] Cannot delete current version
- [ ] All actions show loading states

---

## Common Patterns

### 1. Auth Headers
```typescript
const getAuthHeaders = () => {
  const token = localStorage.getItem('supabase.auth.token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};
```

### 2. Error Handling
```typescript
try {
  const response = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Operation failed');
  }
  
  const result = await response.json();
  // Handle success
} catch (error) {
  console.error('Error:', error);
  alert(error instanceof Error ? error.message : 'Operation failed');
}
```

### 3. Loading States
```typescript
const [isLoading, setIsLoading] = useState(false);

const doAction = async () => {
  setIsLoading(true);
  try {
    // API call
  } finally {
    setIsLoading(false);
  }
};

// In render
{isLoading ? <Spinner /> : <Content />}
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| `STEP8_COMPLETE.md` | Overall Step 8 documentation |
| `STEP8_API_INTEGRATION.md` | API integration details and patterns |
| `STEP8_REMAINING_WORK.md` | **⭐ Detailed implementation guide** |
| `SESSION_SUMMARY.md` | What was accomplished this session |
| `QUICK_START_STEP8.md` | This file - quick reference |

**Start Here** → `STEP8_REMAINING_WORK.md` for step-by-step instructions

---

## Time Estimates

| Task | Difficulty | Time |
|------|------------|------|
| Analysis - Load data | Easy | 30 min |
| Analysis - Re-analyze | Easy | 15 min |
| Analysis - Preview | Medium | 30 min |
| Analysis - Map to tabs | Medium | 60 min |
| **Analysis Total** | | **2-3 hours** |
| | | |
| Version - Load list | Easy | 20 min |
| Version - Restore | Easy | 15 min |
| Version - Duplicate | Easy | 15 min |
| Version - Rename | Medium | 20 min |
| Version - Delete | Easy | 15 min |
| **Version Total** | | **1-2 hours** |
| | | |
| Testing | Medium | 60 min |
| **Grand Total** | | **4-6 hours** |

---

## Success Criteria

### You're Done When:
1. ✅ Analysis page shows real data from API
2. ✅ Re-analyze button runs new analysis
3. ✅ All 9 tabs display correct information
4. ✅ Version history loads real versions
5. ✅ All version actions work (restore, duplicate, rename, delete)
6. ✅ No console errors
7. ✅ User-friendly error messages
8. ✅ Loading states for async operations

---

## Quick Debug Tips

### "Auth token not found"
```typescript
// Check localStorage
console.log(localStorage.getItem('supabase.auth.token'));

// If null, user needs to log in
```

### "404 Not Found"
```typescript
// Check endpoint path
// Check backend router registration
// Check user owns the resource
```

### "500 Internal Server Error"
```typescript
// Check backend logs
// Check database connection
// Check required fields in request body
```

---

## Next Steps After Completion

1. ✅ Mark Step 8 as 100% complete
2. ✅ Update `CURRENT_STATUS.md`
3. ✅ Manual testing with real data
4. ✅ Fix any bugs found
5. 🚀 Move to Step 9 (Applications Tracker)

---

## Need Help?

1. **Detailed instructions**: Read `STEP8_REMAINING_WORK.md`
2. **API reference**: Read `STEP8_API_INTEGRATION.md`
3. **Backend endpoints**: Check `apps/api/routers/` files
4. **Working example**: Look at editor page implementation

---

**Last Updated**: Editor page integration complete  
**Remaining Work**: 3-5 hours  
**Next Milestone**: Step 9 (Applications Tracker) - 75% progress

