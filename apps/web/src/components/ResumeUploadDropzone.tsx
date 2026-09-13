"use client";

import { DragEvent, useCallback, useEffect, useState } from "react";

import {
  getJobStatus,
  getResume,
  uploadResume,
  type JobStatusResult,
  type ResumeDetailResult,
  type ResumeUploadResult,
} from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

const MAX_BYTES = 10 * 1024 * 1024;
const ACCEPT =
  ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

async function accessToken(): Promise<string> {
  const supabase = createClient();
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  const token = data.session?.access_token;
  if (!token) throw new Error("You must be logged in to upload a resume.");
  return token;
}

export function ResumeUploadDropzone() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [upload, setUpload] = useState<ResumeUploadResult | null>(null);
  const [job, setJob] = useState<JobStatusResult | null>(null);
  const [parsed, setParsed] = useState<ResumeDetailResult | null>(null);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setUpload(null);
    setJob(null);
    setParsed(null);

    if (file.size > MAX_BYTES) {
      setError("File exceeds the 10MB limit.");
      return;
    }

    setUploading(true);
    try {
      const token = await accessToken();
      const response = await uploadResume(token, file);
      setUpload(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  useEffect(() => {
    const jobId = upload?.data.job_id;
    const resumeId = upload?.data.id;
    if (!jobId || !resumeId) return;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const token = await accessToken();
        const status = await getJobStatus(token, jobId);
        if (cancelled) return;
        setJob(status);

        if (status.status === "finished" || status.status === "failed") {
          if (status.needs_ocr || status.error) {
            setError(status.error);
          }
          const detail = await getResume(token, resumeId);
          if (!cancelled) setParsed(detail);
          return;
        }

        timer = setTimeout(() => void poll(), 1500);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to poll parse job");
        }
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [upload]);

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) void handleFile(file);
  }

  const parsing = Boolean(upload && !parsed && !error);

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
          dragging ? "border-zinc-900 bg-zinc-50" : "border-zinc-300 bg-white"
        }`}
      >
        <p className="text-lg font-medium text-zinc-900">Drop your resume here</p>
        <p className="mt-2 text-sm text-zinc-600">PDF or DOCX, up to 10MB</p>
        <label className="mt-6 inline-block cursor-pointer rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800">
          {uploading ? "Uploading..." : "Choose file"}
          <input
            type="file"
            accept={ACCEPT}
            className="hidden"
            disabled={uploading || parsing}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
            }}
          />
        </label>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      {upload && (
        <div className="rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-800">
          <p className="font-medium">Upload accepted</p>
          <p className="mt-1">Resume ID: {upload.data.id}</p>
          <p>Version ID: {upload.data.version.id}</p>
          <p>Job ID: {upload.data.job_id}</p>
          <p>Job status: {job?.status ?? "queued"}</p>
        </div>
      )}

      {parsed && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-900">
          <p className="font-medium">
            {parsed.version.needs_ocr
              ? "OCR required"
              : parsed.version.status === "parsed"
                ? "Parsing complete — here's what we found"
                : `Parse status: ${parsed.version.status}`}
          </p>
          <pre className="mt-3 max-h-[32rem] overflow-auto rounded bg-white p-3 text-xs text-zinc-800">
            {JSON.stringify(parsed, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
