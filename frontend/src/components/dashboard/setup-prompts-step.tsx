"use client";

import {
  CheckCircle2,
  FileText,
  Loader2,
  Pencil,
  Upload,
  TriangleAlert,
} from "lucide-react";

import {
  FormEvent,
  useState,
} from "react";

import SetupPromptGenerator from "@/components/dashboard/setup-prompt-generator";
import PromptEditModal from "@/components/dashboard/prompt-edit-modal";

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
] as const;


type Category =
  typeof categories[number];


type Props = {
  projectId: number;
  targetBrand: string;
  initialPrompts: ProjectPrompt[];
};


function pretty(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


export default function SetupPromptsStep({
  projectId,
  targetBrand,
  initialPrompts,
}: Props) {
  const router = useRouter();

  const [
    prompts,
    setPrompts,
  ] = useState(
    initialPrompts,
  );

  const [
    editingPrompt,
    setEditingPrompt,
  ] = useState<ProjectPrompt | null>(
    null,
  );


  const [
    text,
    setText,
  ] = useState("");

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

  const [
    success,
    setSuccess,
  ] = useState<string | null>(
    null,
  );


  function isCategory(
    value: string,
  ): value is Category {
    return categories.some(
      (category) =>
        category === value,
    );
  }


  function parseLines(): {
    category: Category;
    text: string;
  }[] {
    const lines = text
      .split("\n")
      .map(
        (line) =>
          line.trim(),
      )
      .filter(Boolean);

    return lines.map(
      (line) => {
        const separator =
          line.indexOf("|");

        if (separator === -1) {
          return {
            category:
              "informational",

            text:
              line,
          };
        }

        const category =
          line
            .slice(
              0,
              separator,
            )
            .trim()
            .toLowerCase()
            .replaceAll(
              " ",
              "_",
            );

        const promptText =
          line
            .slice(
              separator + 1,
            )
            .trim();

        if (
          !isCategory(
            category
          )
        ) {
          throw new Error(
            `Unknown category: ${category}`
          );
        }

        if (
          promptText.length < 5
        ) {
          throw new Error(
            "Every prompt must contain at least 5 characters."
          );
        }

        return {
          category,
          text:
            promptText,
        };
      },
    );
  }


  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const parsed =
        parseLines();

      if (
        parsed.length === 0
      ) {
        throw new Error(
          "Enter at least one prompt."
        );
      }

      const response =
        await fetch(
          `/api/projects/${projectId}/prompts/bulk`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                prompts: parsed,
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
            : "Prompt import failed.",
        );
      }

      setSuccess(
        `${data.created} prompts created, ${data.skipped_duplicates} duplicates skipped.`,
      );

      setText("");

      const refreshed =
        await fetch(
          `/api/projects/${projectId}/prompts`,
        );

      if (refreshed.ok) {
        const result =
          await refreshed.json();

        setPrompts(
          result as ProjectPrompt[],
        );
      }

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Prompt import failed.",
      );

    } finally {
      setLoading(false);
    }
  }


  const categoryCounts =
    prompts.reduce<
      Record<string, number>
    >(
      (
        result,
        prompt,
      ) => {
        result[
          prompt.category
        ] =
          (
            result[
              prompt.category
            ] ?? 0
          ) + 1;

        return result;
      },
      {},
    );


  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 p-6">
        <div className="flex items-start justify-between gap-5">
          <div className="flex gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400">
              4
            </div>

            <div>
              <h2 className="font-semibold text-white">
                Prompt Set
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Define the questions used
                for controlled visibility
                measurement.
              </p>
            </div>
          </div>

          <div className="rounded-xl bg-slate-800 px-3 py-2 text-sm font-medium text-slate-300">
            {prompts.length} prompts
          </div>
        </div>
      </div>

      <div className="p-6 pb-0">
        <SetupPromptGenerator
          projectId={projectId}
        />

      </div>

      <div className="grid gap-6 p-6 xl:grid-cols-[1fr_1fr]">
        <form
          onSubmit={submit}
          className="rounded-xl border border-slate-800 bg-slate-950/50 p-5"
        >
          <div className="flex items-center gap-2 font-medium text-white">
            <Upload className="h-4 w-4 text-cyan-400" />
            Bulk Import
          </div>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            One prompt per line. Add a
            category before the prompt using
            <span className="mx-1 text-cyan-300">
              category | prompt
            </span>
            . Lines without a category become
            informational.
          </p>

          <textarea
            value={text}
            onChange={(
              event,
            ) =>
              setText(
                event.target.value,
              )
            }
            rows={12}
            placeholder={`commercial | best platforms for ...
comparison | ${targetBrand} alternatives
problem_solution | how can businesses ...
brand | what is ${targetBrand}`}
            className="mt-5 w-full resize-y rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 font-mono text-sm leading-6 text-white outline-none placeholder:text-slate-600 focus:border-cyan-500/50"
          />

          <div className="mt-4 flex flex-wrap gap-2">
            {categories.map(
              (category) => (
                <span
                  key={category}
                  className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400"
                >
                  {category}
                </span>
              ),
            )}
          </div>

          {error && (
            <div className="mt-4 flex gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {success && (
            <div className="mt-4 flex gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-300">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              {success}
            </div>
          )}

          <button
            disabled={loading}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Import Prompt Set
              </>
            )}
          </button>
        </form>

        <div className="rounded-xl border border-slate-800 bg-slate-950/50">
          <div className="border-b border-slate-800 px-5 py-4">
            <div className="font-medium text-white">
              Current Prompt Set
            </div>
          </div>

          {prompts.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="mx-auto h-6 w-6 text-slate-600" />

              <div className="mt-3 text-sm text-slate-500">
                No prompts configured yet.
              </div>
            </div>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 border-b border-slate-800 p-4">
                {Object.entries(
                  categoryCounts,
                ).map(
                  ([
                    category,
                    count,
                  ]) => (
                    <span
                      key={
                        category
                      }
                      className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400"
                    >
                      {pretty(
                        category,
                      )}
                      {" "}
                      {count}
                    </span>
                  ),
                )}
              </div>

              <div className="max-h-[520px] divide-y divide-slate-800 overflow-y-auto">
                {prompts.map(
                  (prompt) => (
                    <div
                      key={prompt.id}
                      className="px-5 py-4"
                    >
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />

                        <div className="min-w-0 flex-1">
                          <div className="text-sm leading-6 text-slate-200">
                            {prompt.text}
                          </div>

                          <div className="mt-2 text-xs text-slate-600">
                            {pretty(
                              prompt.category,
                            )}
                            {" · "}
                            Prompt #
                            {prompt.id}
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() =>
                            setEditingPrompt(
                              prompt
                            )
                          }
                          className="shrink-0 rounded-lg border border-slate-800 p-2 text-slate-500 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-cyan-300"
                          title="Edit prompt"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </>
          )}
        </div>
      </div>
      {editingPrompt && (
        <PromptEditModal
          projectId={projectId}
          prompt={editingPrompt}
          onClose={() =>
            setEditingPrompt(
              null
            )
          }
        />
      )}
    </section>
  );
}
