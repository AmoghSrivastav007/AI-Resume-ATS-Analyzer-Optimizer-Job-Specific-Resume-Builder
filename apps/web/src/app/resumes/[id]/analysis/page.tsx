"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

/**
 * Tabbed Analysis Screen (Step 8)
 * 
 * Features:
 * - Resume preview with issue highlighting
 * - Tabbed analysis panel (Overview, ATS, Keywords, Skills, etc.)
 * - Real-time re-analysis (debounced for LLM-dependent scores)
 * - Click issue → highlight block in preview
 */

type TabType =
  | "overview"
  | "ats"
  | "keywords"
  | "skills"
  | "experience"
  | "formatting"
  | "grammar"
  | "jd_match"
  | "recommendations";

interface Issue {
  id: string;
  issue_type: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  affected_block_id: string | null;
}

interface Block {
  id: string;
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

interface AnalysisData {
  id: string;
  overall_score: number;
  summary: {
    general_quality_score?: any;
    ats_score?: any;
    jd_match_score?: any;
  };
  score_breakdown?: any;
}

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const resumeId = params.id as string;

  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [highlightedBlockId, setHighlightedBlockId] = useState<string | null>(null);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [analysisId, setAnalysisId] = useState<string | null>(null);

  // Helper to get auth headers
  const getAuthHeaders = () => {
    const token = localStorage.getItem('supabase.auth.token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    };
  };

  useEffect(() => {
    loadResumeData();
  }, [resumeId]);

  const loadResumeData = async () => {
    setIsLoading(true);
    try {
      // Load resume sections for preview
      const resumeResponse = await fetch(`/api/resumes/${resumeId}`, {
        headers: getAuthHeaders(),
      });
      
      if (!resumeResponse.ok) {
        throw new Error(`Failed to load resume: ${resumeResponse.statusText}`);
      }
      
      const resumeResult = await resumeResponse.json();
      const resumeData = resumeResult.data;
      
      // Transform sections for preview
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
      
      // Load or create analysis
      const versionId = resumeData.current_version_id || resumeData.version.id;
      await loadOrCreateAnalysis(versionId);
    } catch (error) {
      console.error('Error loading resume:', error);
      alert('Failed to load resume. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadOrCreateAnalysis = async (versionId: string) => {
    try {
      // Try to run a new ATS analysis
      const analysisResponse = await fetch(`/api/analyses`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          analysis_type: 'ats',
          resume_version_id: versionId,
        }),
      });
      
      if (!analysisResponse.ok) {
        throw new Error('Failed to run analysis');
      }
      
      const newAnalysis = await analysisResponse.json();
      setAnalysisId(newAnalysis.id);
      
      // Fetch detailed results
      const detailsResponse = await fetch(`/api/analyses/${newAnalysis.id}`, {
        headers: getAuthHeaders(),
      });
      
      if (!detailsResponse.ok) {
        throw new Error('Failed to get analysis details');
      }
      
      const details = await detailsResponse.json();
      setAnalysisData(details.analysis);
      setIssues(details.issues || []);
    } catch (error) {
      console.error('Error loading analysis:', error);
      // Set empty state if analysis fails
      setAnalysisData({
        id: '',
        overall_score: 0,
        summary: {},
      });
      setIssues([]);
    }
  };

  const loadAnalysisData = async () => {
    // This function is now integrated into loadResumeData
    // Kept for backwards compatibility but not used
  };

  const loadIssues = async () => {
    // This function is now integrated into loadOrCreateAnalysis
    // Kept for backwards compatibility but not used
  };

  const reanalyze = async () => {
    setIsReanalyzing(true);
    try {
      const resumeResponse = await fetch(`/api/resumes/${resumeId}`, {
        headers: getAuthHeaders(),
      });
      
      if (!resumeResponse.ok) {
        throw new Error('Failed to load resume');
      }
      
      const resumeData = await resumeResponse.json();
      const versionId = resumeData.data.current_version_id || resumeData.data.version.id;
      
      // Run new analysis
      const analysisResponse = await fetch(`/api/analyses`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          analysis_type: 'ats',
          resume_version_id: versionId,
        }),
      });
      
      if (!analysisResponse.ok) {
        const error = await analysisResponse.json();
        throw new Error(error.detail || 'Failed to run analysis');
      }
      
      const newAnalysis = await analysisResponse.json();
      setAnalysisId(newAnalysis.id);
      
      // Fetch detailed results
      const detailsResponse = await fetch(`/api/analyses/${newAnalysis.id}`, {
        headers: getAuthHeaders(),
      });
      
      if (!detailsResponse.ok) {
        throw new Error('Failed to get analysis details');
      }
      
      const details = await detailsResponse.json();
      setAnalysisData(details.analysis);
      setIssues(details.issues || []);
      
      alert('✅ Analysis complete!');
    } catch (error) {
      console.error('Error reanalyzing:', error);
      alert(error instanceof Error ? error.message : 'Failed to reanalyze resume');
    } finally {
      setIsReanalyzing(false);
    }
  };

  const highlightIssue = (blockId: string | null) => {
    setHighlightedBlockId(blockId);
    if (blockId) {
      // Scroll to block in preview
      const element = document.getElementById(blockId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Score</h3>
              <div className="flex items-center gap-4">
                <div className="relative w-32 h-32">
                  <svg className="w-32 h-32 transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="#e5e7eb"
                      strokeWidth="12"
                      fill="none"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke={analysisData && analysisData.overall_score >= 70 ? "#10b981" : "#ef4444"}
                      strokeWidth="12"
                      fill="none"
                      strokeDasharray={`${((analysisData?.overall_score || 0) / 100) * 351.86} 351.86`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-bold text-gray-900">
                      {analysisData?.overall_score || 0}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-gray-900">
                    {analysisData && analysisData.overall_score >= 80
                      ? "Excellent"
                      : analysisData && analysisData.overall_score >= 70
                      ? "Good"
                      : analysisData && analysisData.overall_score >= 60
                      ? "Fair"
                      : "Needs Improvement"}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Your resume is {analysisData && analysisData.overall_score >= 70 ? "well-optimized" : "in need of improvements"}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Content Quality</p>
                  <p className="text-2xl font-bold text-gray-900">85</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">ATS Score</p>
                  <p className="text-2xl font-bold text-gray-900">72</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Keyword Match</p>
                  <p className="text-2xl font-bold text-gray-900">75</p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Issues</h3>
              <div className="space-y-2">
                {issues.slice(0, 5).map((issue) => (
                  <div
                    key={issue.id}
                    onClick={() => highlightIssue(issue.affected_block_id)}
                    className={`p-3 rounded border cursor-pointer hover:shadow-sm transition-shadow ${getSeverityColor(
                      issue.severity
                    )}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{issue.title}</p>
                        <p className="text-sm mt-1">{issue.description}</p>
                      </div>
                      <span className="text-xs font-medium uppercase">{issue.severity}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case "ats":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">ATS Compatibility</h3>
            <p className="text-sm text-gray-600">
              Your resume's compatibility with Applicant Tracking Systems
            </p>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-3xl font-bold text-gray-900">72/100</p>
              <p className="text-sm text-gray-600 mt-1">Good compatibility</p>
            </div>
            {/* TODO: Add detailed ATS analysis */}
          </div>
        );

      case "keywords":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Keyword Analysis</h3>
            <p className="text-sm text-gray-600">Keywords found in your resume</p>
            {/* TODO: Add keyword analysis */}
          </div>
        );

      case "skills":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Skills Assessment</h3>
            <p className="text-sm text-gray-600">Analysis of skills in your resume</p>
            {/* TODO: Add skills analysis */}
          </div>
        );

      case "experience":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Experience Evaluation</h3>
            <p className="text-sm text-gray-600">Assessment of your work experience</p>
            {/* TODO: Add experience analysis */}
          </div>
        );

      case "formatting":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Formatting Issues</h3>
            <div className="space-y-2">
              {issues.filter((i) => i.issue_type === "formatting").map((issue) => (
                <div
                  key={issue.id}
                  onClick={() => highlightIssue(issue.affected_block_id)}
                  className={`p-3 rounded border cursor-pointer hover:shadow-sm ${getSeverityColor(
                    issue.severity
                  )}`}
                >
                  <p className="font-medium">{issue.title}</p>
                  <p className="text-sm mt-1">{issue.description}</p>
                </div>
              ))}
            </div>
          </div>
        );

      case "grammar":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Content Quality</h3>
            <div className="space-y-2">
              {issues.filter((i) => i.issue_type === "content").map((issue) => (
                <div
                  key={issue.id}
                  onClick={() => highlightIssue(issue.affected_block_id)}
                  className={`p-3 rounded border cursor-pointer hover:shadow-sm ${getSeverityColor(
                    issue.severity
                  )}`}
                >
                  <p className="font-medium">{issue.title}</p>
                  <p className="text-sm mt-1">{issue.description}</p>
                </div>
              ))}
            </div>
          </div>
        );

      case "jd_match":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Job Description Match</h3>
            <p className="text-sm text-gray-600">
              Upload a job description to see how well your resume matches
            </p>
            {/* TODO: Add JD match analysis */}
          </div>
        );

      case "recommendations":
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
            <p className="text-sm text-gray-600">Suggestions to improve your resume</p>
            <div className="space-y-2">
              {issues.map((issue) => (
                <div
                  key={issue.id}
                  onClick={() => highlightIssue(issue.affected_block_id)}
                  className={`p-3 rounded border cursor-pointer hover:shadow-sm ${getSeverityColor(
                    issue.severity
                  )}`}
                >
                  <p className="font-medium">{issue.title}</p>
                  <p className="text-sm mt-1">{issue.description}</p>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const tabs: { key: TabType; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "ats", label: "ATS" },
    { key: "keywords", label: "Keywords" },
    { key: "skills", label: "Skills" },
    { key: "experience", label: "Experience" },
    { key: "formatting", label: "Formatting" },
    { key: "grammar", label: "Grammar" },
    { key: "jd_match", label: "JD Match" },
    { key: "recommendations", label: "Recommendations" },
  ];

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
            <h1 className="text-2xl font-bold text-gray-900">Resume Analysis</h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(`/resumes/${resumeId}/editor`)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Edit Resume
            </button>
            <button
              onClick={reanalyze}
              disabled={isReanalyzing || isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isReanalyzing ? "Re-analyzing..." : "Re-analyze"}
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-[calc(100vh-73px)]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading analysis...</p>
          </div>
        </div>
      ) : (
        <div className="flex h-[calc(100vh-73px)]">
          {/* Left: Resume Preview */}
          <div className="w-1/2 bg-white border-r border-gray-200 overflow-y-auto p-8">
            <div className="max-w-2xl mx-auto">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Resume Preview</h2>
              <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
                {sections.length > 0 ? (
                  <div className="space-y-6">
                    {sections.map((section) => (
                      <div key={section.id}>
                        <h4 className="text-lg font-semibold mb-2">
                          {section.title || section.section_type}
                        </h4>
                        <div className="space-y-2">
                          {section.blocks.map((block) => (
                            <div
                              key={block.id}
                              id={block.id}
                              className={`transition-colors ${
                                highlightedBlockId === block.id
                                  ? "bg-yellow-100 p-2 rounded"
                                  : ""
                              }`}
                            >
                              <p className="text-gray-700">{block.content.text}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No resume content available
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: Analysis Panel */}
          <div className="w-1/2 bg-white overflow-hidden flex flex-col">
          {/* Tabs */}
          <div className="border-b border-gray-200 overflow-x-auto">
            <div className="flex">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                    activeTab === tab.key
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-6">{renderTabContent()}</div>
        </div>
      </div>
      )}
    </div>
  );
}
