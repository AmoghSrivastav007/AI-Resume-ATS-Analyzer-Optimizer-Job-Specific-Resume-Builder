"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

interface JobPosting {
  id: string;
  title: string;
  company: string | null;
  source_url: string | null;
  raw_text: string;
  created_at: string;
}

interface Requirement {
  id: string;
  requirement_type: string;
  requirement_text: string;
  category: string | null;
}

interface JobDetail {
  job_posting: JobPosting;
  requirements: Requirement[];
  extraction_summary: Record<string, number>;
}

const REQUIREMENT_LABELS: Record<string, string> = {
  required_skill: "Required Skills",
  preferred_skill: "Preferred Skills",
  responsibility: "Responsibilities",
  education: "Education",
  experience_years: "Experience",
  certification: "Certifications",
  domain_knowledge: "Domain Knowledge",
  competency_signal: "Competency Signals",
};

const REQUIREMENT_ICONS: Record<string, string> = {
  required_skill: "🔴",
  preferred_skill: "🟡",
  responsibility: "📋",
  education: "🎓",
  experience_years: "📅",
  certification: "🏆",
  domain_knowledge: "🏢",
  competency_signal: "💡",
};

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.id as string;

  const [jobDetail, setJobDetail] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRawText, setShowRawText] = useState(false);

  useEffect(() => {
    async function fetchJobDetail() {
      try {
        const response = await fetch(`/api/job-postings/${jobId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch job posting");
        }

        const data = await response.json();
        setJobDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    if (jobId) {
      fetchJobDetail();
    }
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading job posting...</p>
        </div>
      </div>
    );
  }

  if (error || !jobDetail) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600">{error || "Job posting not found"}</p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const { job_posting, requirements, extraction_summary } = jobDetail;

  // Group requirements by type
  const groupedRequirements: Record<string, Requirement[]> = {};
  requirements.forEach((req) => {
    if (!groupedRequirements[req.requirement_type]) {
      groupedRequirements[req.requirement_type] = [];
    }
    groupedRequirements[req.requirement_type].push(req);
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-800 mb-4"
          >
            ← Back
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{job_posting.title}</h1>
              {job_posting.company && (
                <p className="text-xl text-gray-600 mt-2">{job_posting.company}</p>
              )}
              {job_posting.source_url && (
                <a
                  href={job_posting.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-sm mt-1 inline-block"
                >
                  View Original →
                </a>
              )}
            </div>
            <div className="text-right text-sm text-gray-500">
              Added {new Date(job_posting.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {/* Extraction Summary */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Extraction Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {extraction_summary.total}
              </div>
              <div className="text-sm text-gray-600">Total Requirements</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {extraction_summary.required_skills}
              </div>
              <div className="text-sm text-gray-600">Required Skills</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {extraction_summary.preferred_skills}
              </div>
              <div className="text-sm text-gray-600">Preferred Skills</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {extraction_summary.responsibilities}
              </div>
              <div className="text-sm text-gray-600">Responsibilities</div>
            </div>
          </div>
        </div>

        {/* Extracted Requirements */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Extracted Requirements</h2>
          
          <div className="space-y-6">
            {Object.entries(REQUIREMENT_LABELS).map(([type, label]) => {
              const typeRequirements = groupedRequirements[type] || [];
              if (typeRequirements.length === 0) return null;

              const icon = REQUIREMENT_ICONS[type] || "📌";

              return (
                <div key={type} className="border-b pb-6 last:border-b-0">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span>{icon}</span>
                    <span>{label}</span>
                    <span className="text-sm font-normal text-gray-500">
                      ({typeRequirements.length})
                    </span>
                  </h3>
                  <ul className="space-y-2">
                    {typeRequirements.map((req) => (
                      <li
                        key={req.id}
                        className="flex items-start gap-2 text-gray-700"
                      >
                        <span className="text-blue-600 mt-1">•</span>
                        <span>{req.requirement_text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>

        {/* Raw Text (Collapsible) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <button
            onClick={() => setShowRawText(!showRawText)}
            className="w-full flex justify-between items-center text-left"
          >
            <h2 className="text-xl font-bold text-gray-900">Original Job Description</h2>
            <svg
              className={`w-6 h-6 transition-transform ${
                showRawText ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          
          {showRawText && (
            <div className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                {job_posting.raw_text}
              </pre>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={() => router.push(`/resumes`)}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700"
          >
            Match with Resume →
          </button>
        </div>
      </div>
    </div>
  );
}
