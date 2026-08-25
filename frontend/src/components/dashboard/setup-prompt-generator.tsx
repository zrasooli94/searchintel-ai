"use client";

import {
  Bot,
  Check,
  CheckCircle2,
  Loader2,
  Sparkles,
  TriangleAlert,
} from "lucide-react";

import {
  useRouter,
} from "next/navigation";

import {
  useMemo,
  useState,
} from "react";

import type {
  StarterPromptGenerationResult,
  StarterPromptSuggestion,
} from "@/lib/types";


type Props = {
  projectId: number;
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


export default function SetupPromptGenerator({
  projectId,
}: Props) {
  const router =
    useRouter();

  const [
    result,
    setResult,
  ] = useState<
    StarterPromptGenerationResult
    | null
  >(null);

  const [
    selected,
    setSelected,
  ] = useState<
    Set<number>
  >(
    new Set(),
  );

  const [
    generating,
    setGenerating,
  ] = useState(false);

  const [
    importing,
    setImporting,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    success,
    setSuccess,
  ] = useState<
    string | null
  >(null);


  const selectedCount =
    selected.size;


  const categoryCounts =
    useMemo(
      () => {
        const counts:
          Record<string, number> = {};

        for (
          const prompt
          of result?.prompts ?? []
        ) {
          counts[
            prompt.category
          ] =
            (
              counts[
                prompt.category
              ] ?? 0
            ) + 1;
        }

        return counts;
      },
      [result],
    );


  async function generate() {
    setGenerating(true);
    setError(null);
    setSuccess(null);

    try {
      const response =
        await fetch(
          `/api/projects/${projectId}/prompts/starter-generate`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                count: 20,
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
            : "Prompt generation failed.",
        );
      }

      const generated =
        data as StarterPromptGenerationResult;

      setResult(
        generated,
      );

      setSelected(
        new Set(
          generated.prompts.map(
            (
              _prompt,
              index,
            ) => index,
          ),
        ),
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Prompt generation failed.",
      );

    } finally {
      setGenerating(false);
    }
  }


  function toggle(
    index: number,
  ) {
    setSelected(
      (current) => {
        const next =
          new Set(
            current,
          );

        if (
          next.has(index)
        ) {
          next.delete(
            index
          );
        } else {
          next.add(
            index
          );
        }

        return next;
      },
    );
  }


  function selectAll() {
    if (!result) {
      return;
    }

    setSelected(
      new Set(
        result.prompts.map(
          (
            _prompt,
            index,
          ) => index,
        ),
      ),
    );
  }


  function clearAll() {
    setSelected(
      new Set(),
    );
  }


  async function importSelected() {
    if (!result) {
      return;
    }

    const prompts:
      StarterPromptSuggestion[] =
        result.prompts.filter(
          (
            _prompt,
            index,
          ) =>
            selected.has(
              index,
            ),
        );

    if (
      prompts.length === 0
    ) {
      setError(
        "Select at least one prompt."
      );
      return;
    }

    setImporting(true);
    setError(null);
    setSuccess(null);

    try {
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
                prompts:
                  prompts.map(
                    (
                      prompt,
                    ) => ({
                      text:
                        prompt.text,

                      category:
                        prompt.category,
                    }),
                  ),
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
        `${data.created} prompts imported, ${data.skipped_duplicates} duplicates skipped.`,
      );

      if (
        data.created > 0
      ) {
        setSelected(
          new Set(),
        );

        setResult(null);
      }

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Prompt import failed.",
      );

    } finally {
      setImporting(false);
    }
  }


  return (
    <div className="mb-6 rounded-xl border border-cyan-500/20 bg-cyan-500/5">
      <div className="flex flex-col justify-between gap-4 border-b border-cyan-500/10 p-5 md:flex-row md:items-center">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-cyan-400/10 p-2.5">
            <Bot className="h-5 w-5 text-cyan-400" />
          </div>

          <div>
            <div className="font-medium text-white">
              AI Starter Prompt Generator
            </div>

            <p className="mt-1 max-w-2xl text-xs leading-5 text-slate-500">
              Uses the crawled target website,
              configured competitors and current
              prompt set to propose a balanced
              discovery benchmark.
            </p>
          </div>
        </div>

        <button
          type="button"
          disabled={
            generating
            || importing
          }
          onClick={generate}
          className="flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-medium text-slate-950 disabled:opacity-50"
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              {result
                ? "Generate Again"
                : "Generate Starter Set"}
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="m-5 flex gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {success && (
        <div className="m-5 flex gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-300">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          {success}
        </div>
      )}

      {result && (
        <div className="p-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="text-xs text-slate-500">
                Generated
              </div>

              <div className="mt-2 text-xl font-semibold text-white">
                {result.generated_count}
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="text-xs text-slate-500">
                Website pages
              </div>

              <div className="mt-2 text-xl font-semibold text-white">
                {result.website_pages_used}
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="text-xs text-slate-500">
                Competitors
              </div>

              <div className="mt-2 text-xl font-semibold text-white">
                {
                  result.competitors_used
                    .length
                }
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="text-xs text-slate-500">
                Model
              </div>

              <div className="mt-2 truncate text-sm font-medium text-white">
                {result.model_name}
              </div>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
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

          <div className="mt-5 flex items-center justify-between gap-4">
            <div className="text-sm text-slate-400">
              {selectedCount} selected
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={
                  selectAll
                }
                className="rounded-lg border border-slate-800 px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-900"
              >
                Select all
              </button>

              <button
                type="button"
                onClick={
                  clearAll
                }
                className="rounded-lg border border-slate-800 px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-900"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="mt-4 max-h-[650px] space-y-2 overflow-y-auto pr-1">
            {result.prompts.map(
              (
                prompt,
                index,
              ) => {
                const active =
                  selected.has(
                    index,
                  );

                return (
                  <button
                    type="button"
                    key={`${prompt.text}-${index}`}
                    onClick={() =>
                      toggle(
                        index
                      )
                    }
                    className={[
                      "w-full rounded-xl border p-4 text-left transition",
                      active
                        ? "border-cyan-500/30 bg-cyan-500/5"
                        : "border-slate-800 bg-slate-950/50 opacity-60",
                    ].join(" ")}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={[
                          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border",
                          active
                            ? "border-cyan-400 bg-cyan-400 text-slate-950"
                            : "border-slate-700",
                        ].join(" ")}
                      >
                        {active && (
                          <Check className="h-3.5 w-3.5" />
                        )}
                      </div>

                      <div className="min-w-0">
                        <div className="text-sm leading-6 text-slate-200">
                          {prompt.text}
                        </div>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <span className="rounded-md bg-slate-800 px-2 py-1 text-xs text-cyan-300">
                            {pretty(
                              prompt.category,
                            )}
                          </span>

                          {prompt.rationale && (
                            <span className="text-xs leading-5 text-slate-600">
                              {
                                prompt.rationale
                              }
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              },
            )}
          </div>

          <button
            type="button"
            disabled={
              importing
            }
            onClick={
              importSelected
            }
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            {importing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4" />
                Import Selected (
                {selectedCount}
                )
              </>
            )}
          </button>

          <p className="mt-3 text-center text-xs text-slate-600">
            Suggestions are not stored until
            you explicitly import them.
          </p>
        </div>
      )}
    </div>
  );
}
