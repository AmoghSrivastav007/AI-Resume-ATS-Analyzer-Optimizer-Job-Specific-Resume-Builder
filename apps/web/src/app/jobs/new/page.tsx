"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function NewJobPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [rawText, setRawText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  
  const [inputMethod, setInputMethod] = useState<"paste" | "upload">("paste");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("title", title);
      if (company) formData.append("company", company);
      if (sourceUrl) formData.append("source_url", sourceUrl);
      
      if (inputMethod === "paste") {
        if (!rawText.trim()) {
          throw new Error("Please paste the job description text");
        }
        formData.append("raw_text", rawText);
      } else {
        if (!file) {
          throw new Error("Please select a file to upload");
        }
        formData.append("file", file);
      }

      const response = await fetch("/api/job-postings", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create job posting");
      }

      const data = await response.json();
      router.push(`/jobs/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-800 mb-4"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Add Job Posting</h1>
          <p className="text-gray-600 mt-2">
            Paste the job description or upload a file (PDF, DOCX, TXT)
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Note: URL scraping is not supported. Please paste or upload the full job description.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded mb-6">
            <div className="font-semibold">Error</div>
            <div className="text-sm">{error}</div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
          {/* Basic Info */}
          <div className="space-y-4 mb-6">
            <div>
              <label htmlFor="title" className="block text-sm font-semibold text-gray-700 mb-2">
                Job Title *
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                placeholder="e.g., Senior Backend Engineer"
                className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="company" className="block text-sm font-semibold text-gray-700 mb-2">
                Company (optional)
              </label>
              <input
                type="text"
                id="company"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g., TechCorp Inc."
                className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="sourceUrl" className="block text-sm font-semibold text-gray-700 mb-2">
                Source URL (optional)
              </label>
              <input
                type="url"
                id="sourceUrl"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://company.com/careers/job-123"
                className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                For reference only - we won't scrape this URL
              </p>
            </div>
          </div>

          {/* Input Method Toggle */}
          <div className="mb-4">
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => setInputMethod("paste")}
                className={`px-4 py-2 rounded font-semibold ${
                  inputMethod === "paste"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                Paste Text
              </button>
              <button
                type="button"
                onClick={() => setInputMethod("upload")}
                className={`px-4 py-2 rounded font-semibold ${
                  inputMethod === "upload"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                Upload File
              </button>
            </div>
          </div>

          {/* Paste Text Area */}
          {inputMethod === "paste" && (
            <div>
              <label htmlFor="rawText" className="block text-sm font-semibold text-gray-700 mb-2">
                Job Description *
              </label>
              <textarea
                id="rawText"
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                required
                rows={15}
                placeholder="Paste the full job description here..."
                className="w-full px-4 py-3 border border-gray-300 rounded font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-sm text-gray-600 mt-2">
                {rawText.length} characters
              </p>
            </div>
          )}

          {/* File Upload */}
          {inputMethod === "upload" && (
            <div>
              <label htmlFor="file" className="block text-sm font-semibold text-gray-700 mb-2">
                Upload Job Description *
              </label>
              <input
                type="file"
                id="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-sm text-gray-600 mt-2">
                Supported formats: PDF, DOCX, TXT
              </p>
              {file && (
                <div className="mt-2 text-sm text-gray-700">
                  Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>
          )}

          {/* Submit Button */}
          <div className="mt-8 flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? "Extracting..." : "Extract Requirements"}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
