"use client";

import {
  Bot,
  CheckCircle2,
  Database,
  Globe2,
  Loader2,
  Play,
  TriangleAlert,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import type {
  BenchmarkJob,
  MeasurementEligibility,
  SetupExperiment,
} from "@/lib/types";
import {
  canRunMeasurement,
} from "@/lib/readiness";
import { benchmarkConfirmation } from "@/lib/benchmark-confirmation";


type Props = {
  projectId: number;
  activePromptCount: number;
  eligibility: Record<
    "technical_seo" | "memory" | "web_search" | "site_rag",
    MeasurementEligibility
  >;
  operatorAuthorized: boolean;
  modelLabel: string;
};


type Mode =
  | "web_search"
  | "memory"
  | "site_rag";


function getError(
  payload: unknown,
  fallback: string,
) {
  if (
    typeof payload === "object"
    && payload !== null
    && "detail" in payload
  ) {
    const detail =
      (
        payload as {
          detail?: unknown;
        }
      ).detail;

    if (
      typeof detail === "string"
    ) {
      return detail;
    }
  }

  return fallback;
}


export default function SetupBaselineStep({
  projectId,
  activePromptCount,
  eligibility,
  operatorAuthorized,
  modelLabel,
}: Props) {
  const router =
    useRouter();

  const [
    mode,
    setMode,
  ] = useState<Mode>(
    "web_search",
  );

  const [
    starting,
    setStarting,
  ] = useState(false);

  const [
    loadingExisting,
    setLoadingExisting,
  ] = useState(true);

  const [
    job,
    setJob,
  ] = useState<
    BenchmarkJob | null
  >(null);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [confirming, setConfirming] = useState(false);

  const timer =
    useRef<
      ReturnType<
        typeof setInterval
      >
      | null
    >(null);


  function stopPolling() {
    if (
      timer.current !== null
    ) {
      clearInterval(
        timer.current
      );

      timer.current = null;
    }
  }


  async function readJob(
    jobId: number,
  ) {
    const response =
      await fetch(
        `/api/benchmark-jobs/${jobId}`,
        {
          cache: "no-store",
        },
      );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        getError(
          data,
          "Could not read benchmark status.",
        ),
      );
    }

    const latest =
      data as BenchmarkJob;

    setJob(
      latest,
    );

    if (
      [
        "completed",
        "completed_with_errors",
        "failed",
      ].includes(
        latest.status,
      )
    ) {
      stopPolling();

      router.refresh();
    }
  }


  async function start() {
    if (starting) return;
    setConfirming(false);

    if (!operatorAuthorized) {
      setError("Unlock operator controls before starting a paid benchmark.");
      return;
    }
    if (
      activePromptCount === 0
    ) {
      setError(
        "No active prompts are configured."
      );
      return;
    }

    const selectedEligibility = eligibility[mode];
    if (selectedEligibility.state === "blocked") {
      setError(selectedEligibility.reason);
      return;
    }
    if (!selectedEligibility.execution_available) {
      setError(selectedEligibility.execution_note);
      return;
    }

    setStarting(true);
    setError(null);

    try {
      const experimentName =
        mode === "web_search"
          ? "Web Baseline V1"
          : mode === "site_rag"
            ? "Site RAG Baseline V1"
            : "Memory Baseline V1";

      const experimentResponse =
        await fetch(
          `/api/projects/${projectId}/experiments`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                name:
                  experimentName,
                phase:
                  "baseline",
                description:
                  mode === "web_search"
                    ? "Initial controlled live-web retrieval, source and citation baseline."
                    : mode === "site_rag"
                      ? "Initial controlled first-party website evidence, BM25 retrieval and grounded answerability baseline."
                      : "Initial controlled latent model-memory baseline.",
              }),
          },
        );

      const experimentData =
        await experimentResponse.json();

      if (
        !experimentResponse.ok
      ) {
        throw new Error(
          getError(
            experimentData,
            "Could not create baseline experiment.",
          ),
        );
      }

      const experiment =
        experimentData as SetupExperiment;

      const benchmarkResponse =
        await fetch(
          `/api/projects/${projectId}/benchmark-jobs`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                model_id: null,
                experiment_id:
                  experiment.id,
                benchmark_mode:
                  mode,
              }),
          },
        );

      const benchmarkData =
        await benchmarkResponse.json();

      if (
        !benchmarkResponse.ok
      ) {
        throw new Error(
          getError(
            benchmarkData,
            "Could not start benchmark.",
          ),
        );
      }

      const created =
        benchmarkData as BenchmarkJob;

      setJob(
        created,
      );

      timer.current =
        setInterval(
          () => {
            void readJob(
              created.id
            ).catch(
              (error) => {
                stopPolling();

                setError(
                  error instanceof Error
                    ? error.message
                    : "Benchmark polling failed.",
                );
              },
            );
          },
          2000,
        );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not create baseline.",
      );

    } finally {
      setStarting(false);
    }
  }


  useEffect(
    () => {
      let cancelled = false;

      const initialLoad =
        window.setTimeout(
          () => {
            void (
              async () => {
                setLoadingExisting(true);

                try {
                  const [
                    experimentResponse,
                    jobResponse,
                  ] = await Promise.all([
                    fetch(
                      `/api/projects/${projectId}/experiments`,
                      {
                        cache: "no-store",
                      },
                    ),
                    fetch(
                      `/api/projects/${projectId}/benchmark-jobs`,
                      {
                        cache: "no-store",
                      },
                    ),
                  ]);

                  const experimentData =
                    await experimentResponse.json();

                  const jobData =
                    await jobResponse.json();

                  if (
                    !experimentResponse.ok
                    || !jobResponse.ok
                  ) {
                    return;
                  }

                  const experiments =
                    experimentData as SetupExperiment[];

                  const jobs =
                    jobData as BenchmarkJob[];

                  const experimentById =
                    new Map(
                      experiments.map(
                        (experiment) => [
                          experiment.id,
                          experiment,
                        ],
                      ),
                    );

                  const matchingJobs =
                    jobs
                      .filter(
                        (candidate) => {
                          if (
                            candidate.experiment_id
                            === null
                            || candidate.benchmark_mode
                            !== mode
                          ) {
                            return false;
                          }

                          const experiment =
                            experimentById.get(
                              candidate.experiment_id
                            );

                          return (
                            experiment?.phase
                            === "baseline"
                          );
                        },
                      )
                      .sort(
                        (
                          left,
                          right,
                        ) =>
                          right.id
                          - left.id,
                      );

                  const existing =
                    matchingJobs[0]
                    ?? null;

                  if (cancelled) {
                    return;
                  }

                  setJob(
                    existing
                  );

                } catch (loadError) {
                  if (!cancelled) {
                    setError(
                      loadError
                        instanceof Error
                        ? loadError.message
                        : "Could not restore baseline state.",
                    );
                  }

                } finally {
                  if (!cancelled) {
                    setLoadingExisting(false);
                  }
                }
              }
            )();
          },
          0,
        );

      return () => {
        cancelled = true;

        window.clearTimeout(
          initialLoad
        );

        if (
          timer.current !== null
        ) {
          clearInterval(
            timer.current
          );

          timer.current = null;
        }
      };
    },
    [
      projectId,
      mode,
    ],
  );


  const running =
    job !== null
    && ![
      "completed",
      "completed_with_errors",
      "failed",
    ].includes(
      job.status,
    );

  const selectedEligibility = eligibility[mode];
  const confirmation = benchmarkConfirmation(
    mode,
    modelLabel,
    activePromptCount,
  );
  const runBlocked =
    !canRunMeasurement(selectedEligibility)
    || !operatorAuthorized;


  return (
    <section className="mt-8 crystal-panel rounded-[22px]">
      <div className="border-b border-slate-200/80 p-6">
        <div className="flex gap-4">
          <div className="crystal-step-badge">
            5
          </div>

          <div>
            <h2 className="font-semibold text-slate-950">
              Baseline Experiment
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Run the current controlled
              prompt set against an AI
              measurement mode.
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid gap-4 md:grid-cols-3">
          <button
            type="button"
            disabled={
              starting
              || running
            }
            onClick={() =>
              setMode(
                "web_search"
              )
            }
            className={[
              "rounded-xl border p-5 text-left transition",
              mode === "web_search"
                ? "border-violet-300 bg-violet-50"
                : "border-slate-200/80 bg-[#fbfcff]",
            ].join(" ")}
          >
            <Globe2 className="h-5 w-5 text-[#5f75ff]" />

            <div className="mt-4 font-medium text-slate-950">
              Web Search
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Measures live-web retrieval,
              source exposure, grounding,
              citations and competitor
              visibility.
            </p>

            <div className="mt-3 text-xs font-medium text-violet-600">
              Recommended first baseline
            </div>
          </button>

          <button
            type="button"
            disabled={
              starting
              || running
            }
            onClick={() =>
              setMode(
                "memory"
              )
            }
            className={[
              "rounded-xl border p-5 text-left transition",
              mode === "memory"
                ? "border-violet-500/40 bg-violet-500/10"
                : "border-slate-200/80 bg-[#fbfcff]",
            ].join(" ")}
          >
            <Bot className="h-5 w-5 text-violet-300" />

            <div className="mt-4 font-medium text-slate-950">
              Memory
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Measures latent model
              knowledge without live-web
              retrieval.
            </p>

            <div className="mt-3 text-xs text-slate-400">
              Kept separate from Web Search
            </div>
          </button>

          <button
            type="button"
            disabled={
              starting
              || running
            }
            onClick={() =>
              setMode(
                "site_rag"
              )
            }
            className={[
              "rounded-xl border p-5 text-left transition",
              mode === "site_rag"
                ? "border-indigo-300 bg-indigo-50"
                : "border-slate-200/80 bg-[#fbfcff]",
            ].join(" ")}
          >
            <Database className="h-5 w-5 text-indigo-600" />

            <div className="mt-4 font-medium text-slate-950">
              Site RAG
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Measures grounded answerability
              using only crawled first-party
              website evidence.
            </p>

            <div className="mt-3 text-xs text-indigo-600">
              No live-web retrieval
            </div>
          </button>
        </div>

        <div className="mt-5 rounded-xl border border-slate-200/80 bg-[#fbfcff] p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">
              Active prompts
            </span>

            <span className="font-semibold text-slate-950">
              {activePromptCount}
            </span>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-slate-400">
              Model
            </span>

            <span className="text-sm text-slate-700">
              {job
                && typeof (
                  job.config_snapshot
                    .provider_model_id
                ) === "string"
                ? job.config_snapshot
                    .provider_model_id
                : modelLabel}
            </span>
          </div>
        </div>

        <div className={[
          "mt-5 rounded-xl border p-4 text-sm",
          selectedEligibility.state === "ready"
            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
            : selectedEligibility.state === "blocked"
              ? "border-red-200 bg-red-50 text-red-800"
              : "border-amber-200 bg-amber-50 text-amber-800",
        ].join(" ")}>
          <div className="font-medium uppercase tracking-wide text-xs">
            {selectedEligibility.state.replace("_", " ")}
          </div>
          <p className="mt-1 leading-6">{selectedEligibility.reason}</p>
          <p className="mt-1 text-xs leading-5 opacity-80">
            {!operatorAuthorized
              ? "Unlock operator controls to start paid execution."
              : runBlocked
              ? selectedEligibility.execution_available
                ? selectedEligibility.recommended_action
                : selectedEligibility.execution_note
              : selectedEligibility.recommended_action}
          </p>
        </div>

        {job && (
          <div className="mt-5 rounded-xl border border-slate-200/80 bg-[#fbfcff] p-5">
            <div className="flex items-center justify-between gap-5">
              <div>
                <div className="text-sm font-medium text-slate-950">
                  Benchmark #{job.id}
                </div>

                <div className="mt-1 text-xs text-slate-500">
                  {job.status}
                </div>
              </div>

              <div className="text-lg font-semibold text-violet-600">
                {Math.round(
                  job.progress_percentage
                )}
                %
              </div>
            </div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="crystal-accent h-full rounded-full transition-all"
                style={{
                  width:
                    `${job.progress_percentage}%`,
                }}
              />
            </div>

            <div className="mt-3 flex justify-between text-xs text-slate-500">
              <span>
                {job.completed_runs}
                {" / "}
                {job.total_prompts}
                {" completed"}
              </span>

              <span>
                {job.failed_runs}
                {" failed"}
              </span>
            </div>

            {job.status === "completed" && (
              <div className="mt-4 flex items-center gap-2 text-sm text-emerald-700">
                <CheckCircle2 className="h-4 w-4" />
                Baseline completed.
              </div>
            )}

            {job.status ===
              "completed_with_errors" && (
              <div className="mt-4 flex items-center gap-2 text-sm text-amber-700">
                <TriangleAlert className="h-4 w-4" />
                Completed with failed runs.
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-5 flex gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-700">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {!job && !loadingExisting && (
          <button
            type="button"
            disabled={
              starting
              || activePromptCount === 0
              || runBlocked
            }
            onClick={() => setConfirming(true)}
            className="crystal-primary-button mt-5 w-full px-4 py-3 text-sm"
          >
            {starting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Create & Run{" "}
                {mode === "web_search"
                  ? "Web Baseline"
                  : mode === "site_rag"
                    ? "Site RAG Baseline"
                    : "Memory Baseline"}
              </>
            )}
          </button>
        )}

        {confirming && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="benchmark-confirmation-title">
            <div className="w-full max-w-md rounded-[22px] border border-white/80 bg-white p-6 shadow-2xl">
              <h3 id="benchmark-confirmation-title" className="text-lg font-semibold text-slate-950">
                Confirm paid benchmark
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Review the expected execution before creating the experiment and AI runs.
              </p>
              <dl className="mt-5 space-y-3 rounded-xl bg-slate-50 p-4 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Measurement mode</dt>
                  <dd className="font-medium text-slate-900">{confirmation.measurementMode}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Model</dt>
                  <dd className="text-right font-medium text-slate-900">{confirmation.model}</dd>
                </div>
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Prompts</dt><dd className="font-medium text-slate-900">{confirmation.promptCount}</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Expected AI runs</dt><dd className="font-medium text-slate-900">{confirmation.expectedAiRuns}</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Web Search</dt><dd className="font-medium text-slate-900">{confirmation.webSearchEnabled ? "Enabled" : "Disabled"}</dd></div>
              </dl>
              <div className="mt-6 flex justify-end gap-3">
                <button type="button" onClick={() => setConfirming(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50">Cancel</button>
                <button type="button" disabled={starting} onClick={start} className="crystal-primary-button px-4 py-2.5 text-sm disabled:opacity-50">
                  {starting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Run Benchmark
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
