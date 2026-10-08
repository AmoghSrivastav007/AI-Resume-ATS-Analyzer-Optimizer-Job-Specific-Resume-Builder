"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

/**
 * Interactive Resume Editor (Step 8)
 * 
 * Features:
 * - Inline block editing
 * - AI-powered rewrites with Truth Guard
 * - Add/remove bullets
 * - Drag-and-drop reordering
 * - Undo/redo (client-side)
 * - Version history
 */

interface Block {
  id: string;
  resume_version_id: string;
  section_id: string;
  block_type: string;
  content: { text: string; [key: string]: any };
  sort_order: number;
}

interface Section {
  id: string;
  section_type: string;
  title: string | null;
  sort_order: number;
  blocks: Block[];
}

interface AIRewriteResult {
  original_text: string;
  proposed_text: string;
  verification_status: "supported" | "partially_supported" | "unsupported";
  guardrails_passed: boolean;
  reasoning: string;
  warnings: string[];
  supported_claims: string[];
  unsupported_claims: string[];
}

export default function EditorPage() {
  const params = useParams();
  const router = useRouter();
  const resumeId = params.id as string;

  const [sections, setSections] = useState<Section[]>([]);
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null);
  const [aiRewriteResult, setAiRewriteResult] = useState<AIRewriteResult | null>(null);
  const [isLoadingRewrite, setIsLoadingRewrite] = useState(false);
  const [editingBlockId, setEditingBlockId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  
  // Export state
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<"pdf" | "docx">("pdf");
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{
    jobId: string;
    validationPassed: boolean | null;
    validationDetails: any;
    errorMessage: string | null;
  } | null>(null);

  // Undo/Redo state
  const [history, setHistory] = useState<Section[][]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Helper to get auth headers
  const getAuthHeaders = () => {
    const token = localStorage.getItem('supabase.auth.token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    };
  };

  // Load resume data
  useEffect(() => {
    loadResumeData();
  }, [resumeId]);

  const loadResumeData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/resumes/${resumeId}`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to load resume: ${response.statusText}`);
      }
      
      const result = await response.json();
      const resumeData = result.data;
      
      // Transform API response to sections format
      const transformedSections: Section[] = resumeData.sections.map((section: any) => ({
        id: section.id,
        section_type: section.section_type,
        title: section.title,
        sort_order: section.sort_order,
        blocks: section.blocks.map((block: any) => ({
          id: block.id,
          resume_version_id: resumeData.current_version_id || resumeData.version.id,
          section_id: section.id,
          block_type: block.block_type,
          content: block.content,
          sort_order: block.sort_order,
        })),
      }));
      
      // Sort sections and blocks by sort_order
      transformedSections.sort((a, b) => a.sort_order - b.sort_order);
      transformedSections.forEach(section => {
        section.blocks.sort((a, b) => a.sort_order - b.sort_order);
      });
      
      setSections(transformedSections);
      pushToHistory(transformedSections);
    } catch (error) {
      console.error("Error loading resume:", error);
      alert("Failed to load resume. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // History management
  const pushToHistory = (newSections: Section[]) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(JSON.parse(JSON.stringify(newSections)));
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setSections(JSON.parse(JSON.stringify(history[historyIndex - 1])));
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setSections(JSON.parse(JSON.stringify(history[historyIndex + 1])));
    }
  };

  // Block editing
  const startEditing = (block: Block) => {
    setEditingBlockId(block.id);
    setEditText(block.content.text);
  };

  const saveEdit = async (blockId: string) => {
    try {
      const response = await fetch(`/api/resume-blocks/${blockId}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          content: { text: editText },
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update block");
      }

      // Update local state
      const updatedSections = sections.map((section) => ({
        ...section,
        blocks: section.blocks.map((block) =>
          block.id === blockId
            ? { ...block, content: { ...block.content, text: editText } }
            : block
        ),
      }));

      setSections(updatedSections);
      pushToHistory(updatedSections);
      setEditingBlockId(null);
    } catch (error) {
      console.error("Error saving edit:", error);
      alert(error instanceof Error ? error.message : "Failed to save edit");
    }
  };

  const cancelEdit = () => {
    setEditingBlockId(null);
    setEditText("");
  };

  // AI Rewrite
  const requestAIRewrite = async (
    block: Block,
    instruction: "shorten" | "expand" | "fix_grammar" | "improve"
  ) => {
    setIsLoadingRewrite(true);
    setSelectedBlock(block);
    setAiRewriteResult(null);

    try {
      const response = await fetch(`/api/resume-blocks/${block.id}/ai-rewrite`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ instruction }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate rewrite");
      }

      const result: AIRewriteResult = await response.json();
      setAiRewriteResult(result);
    } catch (error) {
      console.error("Error requesting AI rewrite:", error);
      alert(error instanceof Error ? error.message : "Failed to generate AI rewrite");
      setSelectedBlock(null);
    } finally {
      setIsLoadingRewrite(false);
    }
  };

  const applyAIRewrite = async () => {
    if (!selectedBlock || !aiRewriteResult) return;

    // Check if user confirmation is needed
    if (
      aiRewriteResult.verification_status === "partially_supported" &&
      !confirm(
        `⚠️ Verification Warning\n\nThis rewrite contains claims that aren't fully supported:\n\n${aiRewriteResult.warnings.join(
          "\n"
        )}\n\nDo you have genuine experience demonstrating this? Only add if true.`
      )
    ) {
      return;
    }

    // Don't allow unsupported rewrites
    if (aiRewriteResult.verification_status === "unsupported") {
      alert(
        "❌ This rewrite contains hallucinations and cannot be applied.\n\n" +
          (aiRewriteResult.warnings.join("\n") || "Content could not be verified")
      );
      return;
    }

    try {
      const response = await fetch(`/api/resume-blocks/${selectedBlock.id}/apply-rewrite`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ proposed_text: aiRewriteResult.proposed_text }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to apply rewrite");
      }

      // Update local state
      const updatedSections = sections.map((section) => ({
        ...section,
        blocks: section.blocks.map((block) =>
          block.id === selectedBlock.id
            ? { ...block, content: { ...block.content, text: aiRewriteResult.proposed_text } }
            : block
        ),
      }));

      setSections(updatedSections);
      pushToHistory(updatedSections);
      setAiRewriteResult(null);
      setSelectedBlock(null);
    } catch (error) {
      console.error("Error applying rewrite:", error);
      alert(error instanceof Error ? error.message : "Failed to apply rewrite");
    }
  };

  // Block operations
  const addBlock = async (sectionId: string) => {
    try {
      const response = await fetch(`/api/resume-blocks/sections/${sectionId}/blocks`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          content: { text: "New bullet point..." },
          block_type: "bullet",
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create block");
      }

      const newBlock: Block = await response.json();

      // Update local state
      const updatedSections = sections.map((section) =>
        section.id === sectionId
          ? { ...section, blocks: [...section.blocks, newBlock] }
          : section
      );

      setSections(updatedSections);
      pushToHistory(updatedSections);
    } catch (error) {
      console.error("Error adding block:", error);
      alert(error instanceof Error ? error.message : "Failed to add block");
    }
  };

  const deleteBlock = async (blockId: string, sectionId: string) => {
    if (!confirm("Delete this block?")) return;

    try {
      const response = await fetch(`/api/resume-blocks/${blockId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete block");
      }

      // Update local state
      const updatedSections = sections.map((section) =>
        section.id === sectionId
          ? { ...section, blocks: section.blocks.filter((block) => block.id !== blockId) }
          : section
      );

      setSections(updatedSections);
      pushToHistory(updatedSections);
    } catch (error) {
      console.error("Error deleting block:", error);
      alert(error instanceof Error ? error.message : "Failed to delete block");
    }
  };

  // Export functions
  const handleExport = async () => {
    setIsExporting(true);
    setExportResult(null);

    try {
      // Create export job
      const response = await fetch(`/api/exports/resumes/${resumeId}/export`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          format: exportFormat,
          version_id: null, // Use current version
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create export job");
      }

      const { job_id } = await response.json();

      // Poll for job completion
      const jobStatus = await pollExportJob(job_id);

      setExportResult({
        jobId: job_id,
        validationPassed: jobStatus.validation_passed,
        validationDetails: jobStatus.validation_details,
        errorMessage: jobStatus.error_message,
      });
    } catch (error) {
      console.error("Error exporting resume:", error);
      alert(error instanceof Error ? error.message : "Failed to export resume");
    } finally {
      setIsExporting(false);
    }
  };

  const pollExportJob = async (jobId: string, maxAttempts = 30): Promise<any> => {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await fetch(`/api/exports/${jobId}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error("Failed to check export status");
      }

      const jobStatus = await response.json();

      if (jobStatus.status === "completed" || jobStatus.status === "failed") {
        return jobStatus;
      }

      // Wait 1 second before next poll
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    throw new Error("Export job timed out");
  };

  const downloadExport = async () => {
    if (!exportResult?.jobId) return;

    try {
      const response = await fetch(`/api/exports/${exportResult.jobId}/download`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to download export");
      }

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${exportResult.jobId}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Close modal
      setShowExportModal(false);
      setExportResult(null);
    } catch (error) {
      console.error("Error downloading export:", error);
      alert(error instanceof Error ? error.message : "Failed to download export");
    }
  };

  const getVerificationBadge = (status: string) => {
    switch (status) {
      case "supported":
        return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">✅ Supported</span>;
      case "partially_supported":
        return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">⚠️ Partially Supported</span>;
      case "unsupported":
        return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">❌ Unsupported</span>;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push(`/resumes/${resumeId}`)}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Resume Editor</h1>
          </div>

          <div className="flex items-center gap-2">
            {/* Undo/Redo */}
            <button
              onClick={undo}
              disabled={historyIndex <= 0 || isLoading}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Undo (Cmd+Z)"
            >
              ↶ Undo
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1 || isLoading}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Redo (Cmd+Shift+Z)"
            >
              ↷ Redo
            </button>

            <button
              onClick={() => setShowExportModal(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700"
            >
              📥 Export
            </button>

            <button
              onClick={() => router.push(`/resumes/${resumeId}/analysis`)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
            >
              View Analysis
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-[calc(100vh-73px)]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading resume...</p>
          </div>
        </div>
      ) : (
        <div className="flex h-[calc(100vh-73px)]">
          {/* Left: Sections */}
          <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Sections</h2>
            <div className="space-y-1">
              {sections.map((section) => (
                <div
                  key={section.id}
                  className="px-3 py-2 text-sm text-gray-700 rounded hover:bg-gray-100 cursor-pointer"
                >
                  {section.title || section.section_type}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center: Editor */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            {sections.map((section) => (
              <div key={section.id} className="mb-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900">
                    {section.title || section.section_type}
                  </h2>
                  <button
                    onClick={() => addBlock(section.id)}
                    className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700"
                  >
                    + Add Bullet
                  </button>
                </div>

                <div className="space-y-2">
                  {section.blocks.map((block) => (
                    <div
                      key={block.id}
                      className="group relative p-3 rounded border border-gray-200 hover:border-blue-300"
                    >
                      {editingBlockId === block.id ? (
                        // Editing mode
                        <div>
                          <textarea
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                            autoFocus
                          />
                          <div className="flex items-center gap-2 mt-2">
                            <button
                              onClick={() => saveEdit(block.id)}
                              className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                            >
                              Save
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        // View mode
                        <>
                          <p className="text-gray-700">{block.content.text}</p>
                          
                          {/* Action buttons (show on hover) */}
                          <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => startEditing(block)}
                              className="px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                              title="Edit"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => deleteBlock(block.id, section.id)}
                              className="px-2 py-1 text-xs font-medium text-red-600 bg-white border border-red-300 rounded hover:bg-red-50"
                              title="Delete"
                            >
                              🗑️
                            </button>
                          </div>

                          {/* AI Rewrite buttons */}
                          <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="text-xs text-gray-500">AI Rewrite:</span>
                            <button
                              onClick={() => requestAIRewrite(block, "improve")}
                              className="px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                              disabled={isLoadingRewrite}
                            >
                              Improve
                            </button>
                            <button
                              onClick={() => requestAIRewrite(block, "shorten")}
                              className="px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                              disabled={isLoadingRewrite}
                            >
                              Shorten
                            </button>
                            <button
                              onClick={() => requestAIRewrite(block, "expand")}
                              className="px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                              disabled={isLoadingRewrite}
                            >
                              Expand
                            </button>
                            <button
                              onClick={() => requestAIRewrite(block, "fix_grammar")}
                              className="px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                              disabled={isLoadingRewrite}
                            >
                              Fix Grammar
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: AI Rewrite Panel */}
        {(isLoadingRewrite || aiRewriteResult) && (
          <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Rewrite</h2>

            {isLoadingRewrite && (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600 mt-4">Generating rewrite...</p>
              </div>
            )}

            {aiRewriteResult && (
              <div className="space-y-4">
                {/* Verification Badge */}
                <div>
                  {getVerificationBadge(aiRewriteResult.verification_status)}
                </div>

                {/* Original */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Original:</h3>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                    {aiRewriteResult.original_text}
                  </p>
                </div>

                {/* Proposed */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Proposed:</h3>
                  <p className="text-sm text-gray-900 bg-blue-50 p-3 rounded border border-blue-200">
                    {aiRewriteResult.proposed_text}
                  </p>
                </div>

                {/* Warnings */}
                {aiRewriteResult.warnings.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                    <h4 className="text-sm font-medium text-yellow-900 mb-2">⚠️ Warnings:</h4>
                    <ul className="text-sm text-yellow-800 space-y-1">
                      {aiRewriteResult.warnings.map((warning, idx) => (
                        <li key={idx} className="list-disc list-inside">
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Reasoning */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Reasoning:</h4>
                  <p className="text-sm text-gray-600">{aiRewriteResult.reasoning}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-4 border-t border-gray-200">
                  <button
                    onClick={applyAIRewrite}
                    disabled={aiRewriteResult.verification_status === "unsupported"}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => setAiRewriteResult(null)}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Export Resume</h2>

            {!exportResult ? (
              <>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Export Format
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="pdf"
                        checked={exportFormat === "pdf"}
                        onChange={(e) => setExportFormat(e.target.value as "pdf" | "docx")}
                        className="mr-2"
                        disabled={isExporting}
                      />
                      <span className="text-gray-700">PDF (with self-check validation)</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="docx"
                        checked={exportFormat === "docx"}
                        onChange={(e) => setExportFormat(e.target.value as "pdf" | "docx")}
                        className="mr-2"
                        disabled={isExporting}
                      />
                      <span className="text-gray-700">DOCX (Microsoft Word)</span>
                    </label>
                  </div>
                </div>

                {isExporting && (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600">Generating and validating export...</p>
                  </div>
                )}

                <div className="flex items-center gap-2 mt-6">
                  <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isExporting ? "Exporting..." : "Export"}
                  </button>
                  <button
                    onClick={() => {
                      setShowExportModal(false);
                      setExportResult(null);
                    }}
                    disabled={isExporting}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Export Result */}
                {exportResult.errorMessage ? (
                  <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
                    <h3 className="text-sm font-medium text-red-900 mb-2">❌ Export Failed</h3>
                    <p className="text-sm text-red-800">{exportResult.errorMessage}</p>
                  </div>
                ) : exportResult.validationPassed === false ? (
                  <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
                    <h3 className="text-sm font-medium text-red-900 mb-2">❌ Validation Failed</h3>
                    <p className="text-sm text-red-800 mb-3">
                      The generated file failed the self-check validation. Some content could not be
                      recovered as selectable text.
                    </p>
                    {exportResult.validationDetails && (
                      <div className="text-sm text-red-800 space-y-1">
                        <p>
                          <strong>Fields Checked:</strong>{" "}
                          {exportResult.validationDetails.fields_checked}
                        </p>
                        <p>
                          <strong>Fields Recovered:</strong>{" "}
                          {exportResult.validationDetails.fields_recovered}
                        </p>
                        {exportResult.validationDetails.missing_fields?.length > 0 && (
                          <div>
                            <strong>Missing Fields:</strong>
                            <ul className="list-disc list-inside mt-1">
                              {exportResult.validationDetails.missing_fields.map(
                                (field: string, idx: number) => (
                                  <li key={idx} className="text-xs">
                                    {field}
                                  </li>
                                )
                              )}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    <p className="text-sm text-red-800 mt-3 font-medium">
                      ⚠️ Download is blocked to prevent ATS issues.
                    </p>
                  </div>
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded p-4 mb-4">
                    <h3 className="text-sm font-medium text-green-900 mb-2">
                      ✅ Export Ready
                    </h3>
                    <p className="text-sm text-green-800 mb-3">
                      Your resume has been generated and validated successfully.
                    </p>
                    {exportResult.validationDetails && exportFormat === "pdf" && (
                      <div className="text-sm text-green-800 space-y-1">
                        <p>
                          <strong>Self-Check Results:</strong>
                        </p>
                        <p>
                          • {exportResult.validationDetails.fields_recovered} /{" "}
                          {exportResult.validationDetails.fields_checked} fields recovered
                        </p>
                        <p>• All content is selectable text (ATS-friendly)</p>
                      </div>
                    )}
                    {exportFormat === "docx" && (
                      <p className="text-sm text-green-800 mt-2">
                        <em>Note: DOCX validation was skipped in MVP.</em>
                      </p>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  {!exportResult.errorMessage && exportResult.validationPassed !== false && (
                    <button
                      onClick={downloadExport}
                      className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700"
                    >
                      📥 Download
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setShowExportModal(false);
                      setExportResult(null);
                    }}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Close
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
