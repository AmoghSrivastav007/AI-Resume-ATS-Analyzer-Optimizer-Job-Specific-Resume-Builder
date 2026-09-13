"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ResumeUploadDropzone } from "@/components/ResumeUploadDropzone";
import { createClient } from "@/lib/supabase/client";

export default function NewResumePage() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    async function checkSession() {
      try {
        const supabase = createClient();
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          router.replace("/login");
          return;
        }
      } catch {
        router.replace("/login");
        return;
      } finally {
        setCheckingAuth(false);
      }
    }

    void checkSession();
  }, [router]);

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  if (checkingAuth) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-zinc-600">
        Checking session...
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl flex-1 px-4 py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Upload resume</h1>
          <p className="mt-1 text-sm text-zinc-600">
            Upload a PDF or DOCX. Parsing runs in the background; results appear as JSON when complete.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleSignOut()}
          className="text-sm text-zinc-600 underline hover:text-zinc-900"
        >
          Sign out
        </button>
      </div>

      <ResumeUploadDropzone />

      <p className="mt-8 text-center text-sm text-zinc-500">
        <Link href="/" className="underline hover:text-zinc-800">
          Back to home
        </Link>
      </p>
    </div>
  );
}
