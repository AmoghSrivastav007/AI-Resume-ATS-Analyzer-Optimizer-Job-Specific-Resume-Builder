# Step 8 - Remaining Integration Work

**Last Updated**: December 2024  
**Estimated Time**: 3-5 hours total

---

## ✅ Completed

### Editor Page Integration
- ✅ Load resume data from API
- ✅ Save manual edits (PATCH `/api/resume-blocks/{id}`)
- ✅ AI rewrites (POST `/api/resume-blocks/{id}/ai-rewrite`)
- ✅ Apply rewrites (POST `/api/resume-blocks/{id}/apply-rewrite`)
- ✅ Add blocks (POST `/api/resume-blocks/sections/{id}/blocks`)
- ✅ Delete blocks (DELETE `/api/resume-blocks/{id}`)
- ✅ Loading states
- ✅ Error handling with backend error messages
- ✅ Authentication headers

---

## ⚠️ TODO: Analysis Page Integration (2-3 hours)

### File: `apps/web/src/app/resumes/[id]/analysis/page.tsx`

### Current Issues
- Using mock data for analysis
- Re-analyze button not connected
- Issues not loaded from database

### Implementation Steps

#### 1. Load Analysis Data (30 mins)

**Current Mock**:
```typescript
const mockData: AnalysisData = {
  overall_score: 78,
  summary: { ... }
};
```

**Replace with**:
```typescript
const loadAnalysisData = async () => {
  setIsLoading(true);
  try {
    // First, get resume to find its current version
    const resumeResponse = await fetch(`/api/resumes/${resumeId}`, {
      headers: getAuthHeaders(),
    });
    
    if (!resumeResponse.ok) throw new Error('Failed to load resume');
    
    const resumeData = await resumeResponse.json();
    const versionId = resumeData.data.current_version_id || resumeData.data.version.id;
    
    // Find the most recent analysis for this version
    // Option 1: If backend provides /api/resumes/{id}/latest-analysis
    const analysisResponse = await fetch(`/api/analyses/resume-version/${versionId}/latest`, {
      headers: getAuthHeaders(),
    });
    
    // Option 2: If not, run a new analysis
    if (analysisResponse.status === 404) {
      // No analysis exists yet, run one
      const newAnalysisResponse = await fetch(`/api/analyses`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          analysis_type: 'ats',
          resume_version_id: versionId,
        }),
      });
      
      if (!newAnalysisResponse.ok) throw new Error('Failed to run analysis');
      
      const newAnalysis = await newAnalysisResponse.json();
      
      // Now fetch the detailed results
      const detailsResponse = await fetch(`/api/analyses/${newAnalysis.id}`, {
        headers: getAuthHeaders(),
      });
      
      const details = await detailsResponse.json();
      setAnalysisData(details.analysis);
      setIssues(details.issues);
    } else {
      const analysis = await analysisResponse.json();
      setAnalysisData(analysis.analysis);
      setIssues(analysis.issues);
    }
  } catch (error) {
    console.error('Error loading analysis:', error);
    alert('Failed to load analysis. Please try again.');
  } finally {
    setIsLoading(false);
  }
};
```

#### 2. Implement Re-Analyze (15 mins)

```typescript
const reanalyze = async () => {
  setIsReanalyzing(true);
  try {
    const resumeResponse = await fetch(`/api/resumes/${resumeId}`, {
      headers: getAuthHeaders(),
    });
    
    const resumeData = await resumeResponse.json();
    const versionId = resumeData.data.current_version_id || resumeData.data.version.id;
    
    // Run new analysis
    const newAnalysisResponse = await fetch(`/api/analyses`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        analysis_type: 'ats',
        resume_version_id: versionId,
      }),
    });
    
    if (!newAnalysisResponse.ok) throw new Error('Failed to run analysis');
    
    const newAnalysis = await newAnalysisResponse.json();
    
    // Fetch detailed results
    const detailsResponse = await fetch(`/api/analyses/${newAnalysis.id}`, {
      headers: getAuthHeaders(),
    });
    
    const details = await detailsResponse.json();
    setAnalysisData(details.analysis);
    setIssues(details.issues);
    
    alert('✅ Analysis complete!');
  } catch (error) {
    console.error('Error reanalyzing:', error);
    alert('Failed to reanalyze. Please try again.');
  } finally {
    setIsReanalyzing(false);
  }
};
```

#### 3. Load Resume Preview (30 mins)

You'll need the resume sections/blocks for the preview:

```typescript
const [sections, setSections] = useState<Section[]>([]);

const loadResumePreview = async () => {
  try {
    const response = await fetch(`/api/resumes/${resumeId}`, {
      headers: getAuthHeaders(),
    });
    
    if (!response.ok) throw new Error('Failed to load resume');
    
    const result = await response.json();
    const resumeData = result.data;
    
    // Transform sections like in editor page
    const transformedSections: Section[] = resumeData.sections.map((section: any) => ({
      id: section.id,
      section_type: section.section_type,
      title: section.title,
      sort_order: section.sort_order,
      blocks: section.blocks.map((block: any) => ({
        id: block.id,
        content: block.content,
        sort_order: block.sort_order,
      })),
    }));
    
    transformedSections.sort((a, b) => a.sort_order - b.sort_order);
    transformedSections.forEach(section => {
      section.blocks.sort((a, b) => a.sort_order - b.sort_order);
    });
    
    setSections(transformedSections);
  } catch (error) {
    console.error('Error loading resume preview:', error);
  }
};
```

#### 4. Add Auth Helper (5 mins)

```typescript
const getAuthHeaders = () => {
  const token = localStorage.getItem('supabase.auth.token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};
```

#### 5. Update useEffect (5 mins)

```typescript
useEffect(() => {
  loadResumePreview();
  loadAnalysisData();
}, [resumeId]);
```

#### 6. Map Analysis Data to Tabs (60 mins)

Each tab needs to display different data from the analysis:

**Overview Tab**:
```typescript
<div>
  <h3>Overall Score: {analysisData?.overall_score || 0}/100</h3>
  <div>
    <h4>ATS Score: {analysisData?.summary?.ats_score?.overall_score || 0}/100</h4>
    <h4>Quality Score: {analysisData?.summary?.general_quality_score?.overall_score || 0}/100</h4>
  </div>
</div>
```

**ATS Tab**:
```typescript
const atsIssues = issues.filter(i => i.issue_type === 'ats' || i.issue_type === 'formatting');
```

**Keywords Tab**:
```typescript
const keywordIssues = issues.filter(i => i.issue_type === 'keyword');
// Display keyword analysis from analysisData.summary.ats_score.subscores.keyword_optimization
```

**Skills Tab**:
```typescript
const skillIssues = issues.filter(i => i.issue_type === 'skill');
```

And so on for each tab...

---

## ⚠️ TODO: Version History Integration (1-2 hours)

### File: `apps/web/src/components/VersionHistory.tsx`

### Current Issues
- Using mock data for version list
- Actions not connected to API

### Implementation Steps

#### 1. Load Versions (20 mins)

**Current Mock**:
```typescript
const mockVersions = [ ... ];
```

**Replace with**:
```typescript
const [versions, setVersions] = useState<Version[]>([]);
const [isLoading, setIsLoading] = useState(true);

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
    console.error('Error loading versions:', error);
    alert('Failed to load versions. Please try again.');
  } finally {
    setIsLoading(false);
  }
};

useEffect(() => {
  if (resumeId) {
    loadVersions();
  }
}, [resumeId]);
```

#### 2. Restore Version (15 mins)

```typescript
const restoreVersion = async (versionId: string) => {
  if (!confirm('Restore this version? This will create a new version with this content.')) {
    return;
  }
  
  setRestoring(versionId);
  try {
    const response = await fetch(`/api/versions/${versionId}/restore`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to restore version');
    }
    
    alert('✅ Version restored successfully!');
    
    // Reload versions
    await loadVersions();
    
    // Optionally reload the page to show new version
    window.location.reload();
  } catch (error) {
    console.error('Error restoring version:', error);
    alert(error instanceof Error ? error.message : 'Failed to restore version');
  } finally {
    setRestoring(null);
  }
};
```

#### 3. Duplicate Version (15 mins)

```typescript
const duplicateVersion = async (versionId: string) => {
  const newTitle = prompt('Enter title for duplicated resume:');
  if (!newTitle) return;
  
  setDuplicating(versionId);
  try {
    const response = await fetch(`/api/versions/${versionId}/duplicate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ new_title: newTitle }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to duplicate version');
    }
    
    const newVersion = await response.json();
    alert(`✅ Resume duplicated as "${newTitle}"!`);
    
    // Optionally navigate to new resume
    router.push(`/resumes/${newVersion.resume_id}`);
  } catch (error) {
    console.error('Error duplicating version:', error);
    alert(error instanceof Error ? error.message : 'Failed to duplicate version');
  } finally {
    setDuplicating(null);
  }
};
```

#### 4. Rename Version (20 mins)

```typescript
const [editingVersionId, setEditingVersionId] = useState<string | null>(null);
const [editTitle, setEditTitle] = useState('');

const startRename = (versionId: string, currentTitle: string) => {
  setEditingVersionId(versionId);
  setEditTitle(currentTitle);
};

const saveRename = async (versionId: string) => {
  if (!editTitle.trim()) {
    alert('Title cannot be empty');
    return;
  }
  
  try {
    const response = await fetch(`/api/versions/${versionId}/rename`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ title: editTitle }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to rename version');
    }
    
    alert('✅ Renamed successfully!');
    await loadVersions();
    setEditingVersionId(null);
  } catch (error) {
    console.error('Error renaming version:', error);
    alert(error instanceof Error ? error.message : 'Failed to rename version');
  }
};

const cancelRename = () => {
  setEditingVersionId(null);
  setEditTitle('');
};
```

#### 5. Delete Version (15 mins)

```typescript
const deleteVersion = async (versionId: string) => {
  if (!confirm('Delete this version? This cannot be undone.')) {
    return;
  }
  
  setDeleting(versionId);
  try {
    const response = await fetch(`/api/versions/${versionId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete version');
    }
    
    alert('✅ Version deleted!');
    await loadVersions();
  } catch (error) {
    console.error('Error deleting version:', error);
    alert(error instanceof Error ? error.message : 'Failed to delete version');
  } finally {
    setDeleting(null);
  }
};
```

#### 6. Add Auth Helper (5 mins)

```typescript
const getAuthHeaders = () => {
  const token = localStorage.getItem('supabase.auth.token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};
```

---

## Testing Checklist

### Analysis Page
- [ ] Load analysis data on mount
- [ ] Display overall score
- [ ] Display issues in appropriate tabs
- [ ] Click issue → highlight block in preview
- [ ] Re-analyze button creates new analysis
- [ ] Loading states during analysis
- [ ] Error handling

### Version History
- [ ] Load version list on mount
- [ ] Display current version badge
- [ ] Restore version creates new version
- [ ] Duplicate version creates new resume
- [ ] Rename updates resume title
- [ ] Delete removes version (but not current)
- [ ] Cannot delete current version
- [ ] Loading states for each action
- [ ] Error handling

---

## Optional Enhancements

### Analysis Page
1. **Keyboard shortcuts**: `/` to focus search, `j/k` to navigate issues
2. **Export report**: Download analysis as PDF
3. **Comparison mode**: Compare before/after analysis
4. **Progress tracking**: Show improvement over time

### Version History
1. **Visual diff**: Show changes between versions
2. **Tagging**: Add tags to versions ("Interview Ready", "Draft", etc.)
3. **Comments**: Add notes to versions
4. **Timeline view**: Visual timeline of all versions

---

## Quick Start Guide

### To Complete Analysis Page Integration:

1. Open `apps/web/src/app/resumes/[id]/analysis/page.tsx`
2. Add `getAuthHeaders()` helper
3. Replace `loadAnalysisData()` mock with real API calls
4. Replace `loadIssues()` mock with real API calls
5. Add `loadResumePreview()` for resume blocks
6. Implement `reanalyze()` function
7. Update `useEffect` to call all load functions
8. Map analysis data to each tab
9. Test with real resume

### To Complete Version History Integration:

1. Open `apps/web/src/components/VersionHistory.tsx`
2. Add `getAuthHeaders()` helper
3. Replace mock data with `loadVersions()` API call
4. Implement `restoreVersion()` function
5. Implement `duplicateVersion()` function
6. Implement `renameVersion()` with inline editing
7. Implement `deleteVersion()` function
8. Add loading states for each action
9. Test all actions with real resume

---

## Estimated Time Breakdown

| Task | Time | Difficulty |
|------|------|------------|
| Analysis page - Load data | 30 mins | Easy |
| Analysis page - Re-analyze | 15 mins | Easy |
| Analysis page - Resume preview | 30 mins | Medium |
| Analysis page - Map to tabs | 60 mins | Medium |
| Version history - Load list | 20 mins | Easy |
| Version history - Restore | 15 mins | Easy |
| Version history - Duplicate | 15 mins | Easy |
| Version history - Rename | 20 mins | Medium |
| Version history - Delete | 15 mins | Easy |
| Testing all features | 60 mins | Medium |
| **Total** | **4.5 hours** | - |

---

## Success Criteria

### Analysis Page ✅ Complete When:
- [ ] Loads real analysis data from API
- [ ] Re-analyze button works
- [ ] All 9 tabs display correct data
- [ ] Click issue highlights block
- [ ] Loading states work
- [ ] Error handling is user-friendly

### Version History ✅ Complete When:
- [ ] Loads real version list from API
- [ ] Restore creates new version and reloads page
- [ ] Duplicate creates new resume with custom title
- [ ] Rename updates title inline
- [ ] Delete removes version (with confirmation)
- [ ] Current version cannot be deleted
- [ ] Loading states for all actions
- [ ] Error handling is user-friendly

---

## Next Steps After Completion

1. ✅ Update `STEP8_COMPLETE.md` status
2. ✅ Update `CURRENT_STATUS.md` to 100% Step 8 complete
3. ✅ Create `STEP8_FULLY_INTEGRATED.md` summary
4. 🚀 Move to Step 9 (Applications Tracker)

---

**Last Updated**: Editor Page Integration Complete  
**Remaining**: Analysis Page (2-3h) + Version History (1-2h) = 3-5 hours total

