const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ResumeUploadResult = {
  data: {
    id: string;
    title: string;
    current_version_id: string | null;
    created_at: string;
    updated_at: string;
    job_id: string | null;
    version: {
      id: string;
      resume_id: string;
      version_number: number;
      status: string;
      storage_path: string;
      original_filename: string;
      mime_type: string;
      file_size_bytes: number;
      needs_ocr?: boolean;
      parse_error?: string | null;
      created_at: string;
      updated_at: string;
    };
  };
};

export type JobStatusResult = {
  id: string;
  status:
    | "queued"
    | "started"
    | "finished"
    | "failed"
    | "deferred"
    | "scheduled"
    | "stopped"
    | "canceled";
  resume_id: string | null;
  version_id: string | null;
  error: string | null;
  needs_ocr: boolean;
  result: Record<string, unknown> | null;
};

export type ResumeDetailResult = {
  id: string;
  title: string;
  current_version_id: string | null;
  created_at: string;
  updated_at: string;
  version: ResumeUploadResult["data"]["version"];
  sections: Array<{
    id: string;
    section_type: string;
    title: string | null;
    sort_order: number;
    blocks: Array<{
      id: string;
      block_type: string;
      content: Record<string, unknown>;
      sort_order: number;
    }>;
  }>;
  facts: Array<{
    id: string;
    fact_type: string;
    is_verified: boolean;
    fact_text: string;
    source_block_id: string | null;
    metadata: Record<string, unknown>;
  }>;
};

async function parseError(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => ({}));
  return typeof body.detail === "string" ? body.detail : fallback;
}

export async function uploadResume(
  accessToken: string,
  file: File,
): Promise<ResumeUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/resumes`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to upload resume"));
  }

  return response.json();
}

export async function getJobStatus(
  accessToken: string,
  jobId: string,
): Promise<JobStatusResult> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to fetch job status"));
  }
  const body = await response.json();
  return body.data ?? body;
}

export async function getResume(
  accessToken: string,
  resumeId: string,
): Promise<ResumeDetailResult> {
  const response = await fetch(`${API_BASE}/api/resumes/${resumeId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to fetch resume"));
  }
  const body = await response.json();
  return body.data ?? body;
}
