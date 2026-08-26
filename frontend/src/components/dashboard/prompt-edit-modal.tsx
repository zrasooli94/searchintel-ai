"use client";

import {
  Loader2,
  Save,
  X,
  TriangleAlert,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import type {
  ProjectPrompt,
} from "@/lib/types";


const categories = [
  "informational",
  "navigational",
  "commercial",
  "transactional",
  "comparison",
  "recommendation",
  "problem_solution",
  "brand",
];


type Props = {
  projectId: number;
  prompt: ProjectPrompt;
  onClose: () => void;
};


export default function PromptEditModal({
  projectId,
  prompt,
  onClose,
}: Props) {
  const router =
    useRouter();

  const [
    text,
    setText,
  ] = useState(
    prompt.text,
  );

  const [
    category,
    setCategory,
  ] = useState(
    prompt.category,
  );

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  async function save() {
    if (
      text.trim().length < 5
    ) {
      setError(
        "Prompt must contain at least 5 characters."
      );

      return;
    }

    setSaving(true);
    setError(null);

    try {
      const response =
        await fetch(
          `/api/projects/${projectId}/prompts/${prompt.id}`,
          {
            method: "PUT",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                text:
                  text.trim(),

                category,

                intent:
                  prompt.intent,
              }),
          },
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data?.detail
          === "string"
            ? data.detail
            : "Could not update prompt.",
        );
      }

      onClose();

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not update prompt.",
      );

    } finally {
      setSaving(false);
    }
  }


  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-5 backdrop-blur-[2px]"
      onMouseDown={
        (event) => {
          if (
            event.target
            === event.currentTarget
          ) {
            onClose();
          }
        }
      }
    >
      <div className="crystal-panel w-full max-w-2xl overflow-hidden rounded-[24px] bg-white/95 shadow-[0_30px_90px_rgba(15,23,42,0.16)]">
        <div className="flex items-center justify-between border-b border-slate-200/80 px-6 py-5">
          <div>
            <h2 className="font-semibold text-slate-950">
              Edit Prompt
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Prompt #{prompt.id} ·
              editing does not change the
              20-prompt limit.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-900"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div>
            <label className="text-sm text-slate-400">
              Category
            </label>

            <select
              value={category}
              onChange={
                (event) =>
                  setCategory(
                    event.target.value
                  )
              }
              className="crystal-field mt-2 px-4 py-3 text-sm"
            >
              {categories.map(
                (item) => (
                  <option
                    key={item}
                    value={item}
                  >
                    {item}
                  </option>
                ),
              )}
            </select>
          </div>

          <div>
            <label className="text-sm text-slate-400">
              Prompt
            </label>

            <textarea
              value={text}
              onChange={
                (event) =>
                  setText(
                    event.target.value
                  )
              }
              rows={6}
              autoFocus
              className="crystal-field mt-2 resize-y px-4 py-3 text-sm leading-6"
            />
          </div>

          {error && (
            <div className="flex gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-700">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 border-t border-slate-200/80 px-6 py-5">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="crystal-secondary-button px-4 py-2.5 text-sm"
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={save}
            disabled={
              saving
              || text.trim().length < 5
            }
            className="crystal-primary-button px-5 py-2.5 text-sm"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
