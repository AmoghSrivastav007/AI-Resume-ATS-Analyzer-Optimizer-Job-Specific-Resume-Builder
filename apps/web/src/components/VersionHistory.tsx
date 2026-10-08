"use client";

import { useState, useEffect } from "react";

/**
 * Version History Component (Step 8)
 * 
 * Features:
 * - List all versions
 * - View version
 * - Restore previous version
 * - Duplicate version
 * - Rename resume
 * - Delete version
 */

interface Version {
  id: string;
  resume_id: string;
  version_number: number;
  status: string;
  original_filename: string;
  created_at: string;
  updated_at: string;
}

interface VersionListResponse {
  resume_id: string;
  resume_title: string;
  current_version_id: string | null;
  versions: Version[];
}

interface VersionHistoryProps {
  resumeId: string;
  onVersionRestored?: () => void;
}

export default function VersionHistory({ resumeId, onVersionRestored }: VersionHistoryProps) {
  const [data, setData] = useState<VersionListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  // Helper to get auth headers
  const getAuthHeaders = () => {
    const token = localStorage.getItem('supabase.auth.token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    };
  };

  useEffect(() => {
    loadVersions();
  }, [resumeId]);

  const loadVersions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/versions/resume/${resumeId}`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to load versions");
      }

      const result: VersionListResponse = await response.json();
      setData(result);
      setNewTitle(result.resume_title);
    } catch (error) {
      console.error("Error loading versions:", error);
      alert(error instanceof Error ? error.message : "Failed to load version history");
    } finally {
      setIsLoading(false);
    }
  };

  const restoreVersion = async (versionId: string) => {
    if (!confirm("Restore this version? This will create a new version with this content.")) {
      return;
    }

    setActionLoading(versionId);
    try {
      const response = await fetch(`/api/versions/${versionId}/restore`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to restore version");
      }

      await loadVersions();
      onVersionRestored?.();
      alert("✅ Version restored successfully");
    } catch (error) {
      console.error("Error restoring version:", error);
      alert(error instanceof Error ? error.message : "Failed to restore version");
    } finally {
      setActionLoading(null);
    }
  };

  const duplicateVersion = async (versionId: string) => {
    const title = prompt("Enter title for the duplicated resume:");
    if (!title) return;

    setActionLoading(versionId);
    try {
      const response = await fetch(`/api/versions/${versionId}/duplicate`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ new_title: title }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to duplicate version");
      }

      alert("✅ Resume duplicated successfully");
      // Optionally reload versions to show it was created
      await loadVersions();
    } catch (error) {
      console.error("Error duplicating version:", error);
      alert(error instanceof Error ? error.message : "Failed to duplicate version");
    } finally {
      setActionLoading(null);
    }
  };

  const renameResume = async () => {
    if (!data?.versions[0]?.id) return;

    try {
      const response = await fetch(`/api/versions/${data.versions[0].id}/rename`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ title: newTitle }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to rename resume");
      }

      await loadVersions();
      setIsRenaming(false);
      alert("✅ Resume renamed successfully");
    } catch (error) {
      console.error("Error renaming resume:", error);
      alert(error instanceof Error ? error.message : "Failed to rename resume");
    }
  };

  const deleteVersion = async (versionId: string) => {
    if (!confirm("Delete this version? This action cannot be undone.")) {
      return;
    }

    setActionLoading(versionId);
    try {
      const response = await fetch(`/api/versions/${versionId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete version");
      }

      await loadVersions();
      alert("✅ Version deleted successfully");
    } catch (error: any) {
      console.error("Error deleting version:", error);
      alert(error.message || "Failed to delete version");
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "parsed":
        return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">Parsed</span>;
      case "parsing":
        return <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">Parsing...</span>;
      case "error":
        return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">Error</span>;
      default:
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">{status}</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="text-sm text-gray-600 mt-4">Loading versions...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 text-center">
        <p className="text-sm text-gray-600">Failed to load version history</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            {isRenaming ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                <button
                  onClick={renameResume}
                  className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setIsRenaming(false);
                    setNewTitle(data.resume_title);
                  }}
                  className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-gray-900">{data.resume_title}</h2>
                <button
                  onClick={() => setIsRenaming(true)}
                  className="text-gray-400 hover:text-gray-600"
                  title="Rename"
                >
                  ✏️
                </button>
              </div>
            )}
            <p className="text-sm text-gray-600">{data.versions.length} version(s)</p>
          </div>
        </div>
      </div>

      {/* Version List */}
      <div className="divide-y divide-gray-200">
        {data.versions.map((version) => {
          const isCurrent = version.id === data.current_version_id;
          const isActionInProgress = actionLoading === version.id;

          return (
            <div
              key={version.id}
              className={`px-6 py-4 hover:bg-gray-50 ${isCurrent ? "bg-blue-50" : ""}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">
                      📄 Version {version.version_number}
                    </span>
                    {isCurrent && (
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        Current
                      </span>
                    )}
                    {getStatusBadge(version.status)}
                  </div>
                  <p className="text-xs text-gray-600 mt-1">
                    Created: {formatDate(version.created_at)}
                  </p>
                  <p className="text-xs text-gray-600">
                    File: {version.original_filename}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {isActionInProgress ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  ) : (
                    <>
                      {!isCurrent && (
                        <>
                          <button
                            onClick={() => restoreVersion(version.id)}
                            className="px-3 py-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                            title="Restore this version"
                          >
                            Restore
                          </button>
                          <button
                            onClick={() => deleteVersion(version.id)}
                            className="px-3 py-1 text-xs font-medium text-red-600 hover:text-red-700"
                            title="Delete this version"
                          >
                            Delete
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => duplicateVersion(version.id)}
                        className="px-3 py-1 text-xs font-medium text-gray-700 hover:text-gray-900"
                        title="Duplicate as new resume"
                      >
                        Duplicate
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Info Footer */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-600">
          💡 <strong>Restore</strong> creates a new version with old content. <strong>Duplicate</strong> creates a
          new resume.
        </p>
      </div>
    </div>
  );
}
