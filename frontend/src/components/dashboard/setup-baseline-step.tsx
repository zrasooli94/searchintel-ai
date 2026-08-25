"use client";

import {
  Bot,
  CheckCircle2,
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
  SetupExperiment,
} from "@/lib/types";


type Props = {
  projectId: number;
  activePromptCount: number;
};


type Mode =
  | "web_search"
  | "memory";


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
    if (
      activePromptCount === 0
    ) {
      setError(
        "No active prompts are configured."
      );
      return;
    }

    setStarting(true);
    setError(null);

    try {
      const experimentName =
        mode === "web_search"
          ? "Web Baseline V1"
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
                model_id: 2,
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


  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 p-6">
        <div className="flex gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400">
            5
          </div>

          <div>
            <h2 className="font-semibold text-white">
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
        <div className="grid gap-4 md:grid-cols-2">
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
                ? "border-cyan-500/40 bg-cyan-500/10"
                : "border-slate-800 bg-slate-950/50",
            ].join(" ")}
          >
            <Globe2 className="h-5 w-5 text-cyan-400" />

            <div className="mt-4 font-medium text-white">
              Web Search
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Measures live-web retrieval,
              source exposure, grounding,
              citations and competitor
              visibility.
            </p>

            <div className="mt-3 text-xs font-medium text-cyan-300">
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
                : "border-slate-800 bg-slate-950/50",
            ].join(" ")}
          >
            <Bot className="h-5 w-5 text-violet-300" />

            <div className="mt-4 font-medium text-white">
              Memory
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Measures latent model
              knowledge without live-web
              retrieval.
            </p>

            <div className="mt-3 text-xs text-slate-600">
              Kept separate from Web Search
            </div>
          </button>
        </div>

        <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/50 p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">
              Active prompts
            </span>

            <span className="font-semibold text-white">
              {activePromptCount}
            </span>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-slate-400">
              Model
            </span>

            <span className="text-sm text-slate-300">
              GPT-5.6 Luna
            </span>
          </div>
        </div>

        {job && (
          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/50 p-5">
            <div className="flex items-center justify-between gap-5">
              <div>
                <div className="text-sm font-medium text-white">
                  Benchmark #{job.id}
                </div>

                <div className="mt-1 text-xs text-slate-500">
                  {job.status}
                </div>
              </div>

              <div className="text-lg font-semibold text-cyan-300">
                {Math.round(
                  job.progress_percentage
                )}
                %
              </div>
            </div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-cyan-400 transition-all"
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
              <div className="mt-4 flex items-center gap-2 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4" />
                Baseline completed.
              </div>
            )}

            {job.status ===
              "completed_with_errors" && (
              <div className="mt-4 flex items-center gap-2 text-sm text-amber-300">
                <TriangleAlert className="h-4 w-4" />
                Completed with failed runs.
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-5 flex gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
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
            }
            onClick={start}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-medium text-slate-950 disabled:opacity-50"
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
                  : "Memory Baseline"}
              </>
            )}
          </button>
        )}
      </div>
    </section>
  );
}
