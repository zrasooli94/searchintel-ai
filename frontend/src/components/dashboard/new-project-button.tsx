"use client";

import {
  Loader2,
  Plus,
  X,
} from "lucide-react";

import {
  FormEvent,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import type {
  ProjectOnboardResponse,
} from "@/lib/types";


export default function NewProjectButton() {
  const router = useRouter();

  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(true);
    setError(null);

    const form =
      new FormData(
        event.currentTarget,
      );

    const payload = {
      project_name:
        String(
          form.get(
            "project_name"
          ) ?? "",
        ),

      project_description:
        String(
          form.get(
            "project_description"
          ) ?? "",
        ) || null,

      target_brand:
        String(
          form.get(
            "target_brand"
          ) ?? "",
        ),

      website_url:
        String(
          form.get(
            "website_url"
          ) ?? "",
        ),
    };

    try {
      const response = await fetch(
        "/api/projects/onboard",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body:
            JSON.stringify(
              payload
            ),
        },
      );

      const data =
        await response.json();

      if (!response.ok) {
        const detail =
          data?.detail;

        if (
          typeof detail
          === "string"
        ) {
          throw new Error(
            detail
          );
        }

        throw new Error(
          "Project onboarding failed."
        );
      }

      const result =
        data as
          ProjectOnboardResponse;

      router.push(
        `/projects/${result.project_id}/setup`
      );

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Project onboarding failed."
      );

    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() =>
          setOpen(true)
        }
        className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-300"
      >
        <Plus className="h-4 w-4" />
        New Project
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-5 backdrop-blur-sm">
          <div className="w-full max-w-xl crystal-panel rounded-[22px] shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200/80 p-6">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">
                  New SearchIntel Project
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Create the target brand
                  and primary website
                  workspace.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  setOpen(false)
                }
                className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-slate-950"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={submit}
              className="space-y-5 p-6"
            >
              <div>
                <label className="text-sm text-slate-700">
                  Project name
                </label>

                <input
                  name="project_name"
                  required
                  minLength={3}
                  placeholder="Acme Search Intelligence"
                  className="mt-2 w-full rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400 focus:border-cyan-500/50"
                />
              </div>

              <div>
                <label className="text-sm text-slate-700">
                  Target brand
                </label>

                <input
                  name="target_brand"
                  required
                  minLength={2}
                  placeholder="Acme"
                  className="mt-2 w-full rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400 focus:border-cyan-500/50"
                />
              </div>

              <div>
                <label className="text-sm text-slate-700">
                  Primary website
                </label>

                <input
                  name="website_url"
                  required
                  type="url"
                  placeholder="https://example.com"
                  className="mt-2 w-full rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400 focus:border-cyan-500/50"
                />
              </div>

              <div>
                <label className="text-sm text-slate-700">
                  Description
                </label>

                <textarea
                  name="project_description"
                  rows={3}
                  placeholder="SEO, GEO and AI visibility project."
                  className="mt-2 w-full resize-none rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400 focus:border-cyan-500/50"
                />
              </div>

              {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() =>
                    setOpen(false)
                  }
                  className="rounded-xl border border-slate-200/80 px-4 py-2.5 text-sm text-slate-700 hover:bg-white"
                >
                  Cancel
                </button>

                <button
                  disabled={loading}
                  className="flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-2.5 text-sm font-medium text-slate-950 disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      Create Project
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
