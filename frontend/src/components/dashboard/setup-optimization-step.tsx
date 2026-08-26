"use client";

import {
  CheckCircle2,
  FlaskConical,
  Globe2,
  Loader2,
  Play,
  RefreshCw,
  TriangleAlert,
} from "lucide-react";

import {
  useCallback,
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
};


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


function isTerminal(
  status: string,
) {
  return [
    "completed",
    "completed_with_errors",
    "failed",
  ].includes(status);
}


export default function SetupOptimizationStep({
  projectId,
}: Props) {
  const router =
    useRouter();

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    starting,
    setStarting,
  ] = useState(false);

  const [
    baselineJob,
    setBaselineJob,
  ] = useState<
    BenchmarkJob | null
  >(null);

  const [
    baselineExperiment,
    setBaselineExperiment,
  ] = useState<
    SetupExperiment | null
  >(null);

  const [
    optimizationJob,
    setOptimizationJob,
  ] = useState<
    BenchmarkJob | null
  >(null);

  const [
    optimizationExperiment,
    setOptimizationExperiment,
  ] = useState<
    SetupExperiment | null
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


  const stopPolling =
    useCallback(
      () => {
        if (
          timer.current !== null
        ) {
          clearInterval(
            timer.current
          );

          timer.current = null;
        }
      },
      [],
    );


  const readJob =
    useCallback(
      async (
        jobId: number,
      ) => {
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
              "Could not read optimization benchmark.",
            ),
          );
        }

        const latest =
          data as BenchmarkJob;

        setOptimizationJob(
          latest,
        );

        if (
          isTerminal(
            latest.status
          )
        ) {
          stopPolling();
          router.refresh();
        }
      },
      [
        router,
        stopPolling,
      ],
    );


  const startPolling =
    useCallback(
      (
        jobId: number,
      ) => {
        stopPolling();

        timer.current =
          setInterval(
            () => {
              void readJob(
                jobId
              ).catch(
                (pollError) => {
                  stopPolling();

                  setError(
                    pollError
                      instanceof Error
                      ? pollError.message
                      : "Optimization polling failed.",
                  );
                },
              );
            },
            2000,
          );
      },
      [
        readJob,
        stopPolling,
      ],
    );


  const loadState =
    useCallback(
      async () => {
        setLoading(true);
        setError(null);

        try {
          const [
            experimentResponse,
            jobResponse,
          ] =
            await Promise.all([
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
          ) {
            throw new Error(
              getError(
                experimentData,
                "Could not load experiments.",
              ),
            );
          }

          if (!jobResponse.ok) {
            throw new Error(
              getError(
                jobData,
                "Could not load benchmark jobs.",
              ),
            );
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

          const completedWebBaselines =
            jobs.filter(
              (job) => {
                if (
                  job.status
                  !== "completed"
                  || job.benchmark_mode
                  !== "web_search"
                  || job.experiment_id
                  === null
                ) {
                  return false;
                }

                const experiment =
                  experimentById.get(
                    job.experiment_id
                  );

                return (
                  experiment?.phase
                  === "baseline"
                );
              },
            );

          completedWebBaselines.sort(
            (
              left,
              right,
            ) =>
              right.id
              - left.id,
          );

          const baseline =
            completedWebBaselines[0]
            ?? null;

          setBaselineJob(
            baseline
          );

          setBaselineExperiment(
            baseline?.experiment_id
              ? (
                  experimentById.get(
                    baseline.experiment_id
                  )
                  ?? null
                )
              : null
          );

          const optimizationJobs =
            jobs.filter(
              (job) => {
                if (
                  job.experiment_id
                  === null
                ) {
                  return false;
                }

                const experiment =
                  experimentById.get(
                    job.experiment_id
                  );

                return (
                  experiment?.phase
                  === "optimization"
                  && job.benchmark_mode
                  === "web_search"
                );
              },
            );

          optimizationJobs.sort(
            (
              left,
              right,
            ) =>
              right.id
              - left.id,
          );

          const latestOptimization =
            optimizationJobs[0]
            ?? null;

          setOptimizationJob(
            latestOptimization
          );

          setOptimizationExperiment(
            latestOptimization?.experiment_id
              ? (
                  experimentById.get(
                    latestOptimization
                      .experiment_id
                  )
                  ?? null
                )
              : null
          );

          if (
            latestOptimization
            && !isTerminal(
              latestOptimization.status
            )
          ) {
            startPolling(
              latestOptimization.id
            );
          }

        } catch (loadError) {
          setError(
            loadError
              instanceof Error
              ? loadError.message
              : "Could not load optimization state.",
          );

        } finally {
          setLoading(false);
        }
      },
      [
        projectId,
        startPolling,
      ],
    );


  useEffect(
    () => {
      const initialLoad =
        window.setTimeout(
          () => {
            void loadState();
          },
          0,
        );

      return () => {
        window.clearTimeout(
          initialLoad
        );

        stopPolling();
      };
    },
    [
      loadState,
      stopPolling,
    ],
  );


  async function start() {
    if (!baselineJob) {
      setError(
        "A completed Web Search baseline is required."
      );
      return;
    }

    setStarting(true);
    setError(null);

    try {
      const existingVersions =
        [
          optimizationExperiment,
        ]
          .filter(
            (
              experiment
            ): experiment is SetupExperiment =>
              experiment !== null
          )
          .map(
            (experiment) => {
              const match =
                experiment.name.match(
                  /^Web Optimization V(\d+)$/i
                );

              return match
                ? Number(
                    match[1]
                  )
                : 0;
            },
          );

      const nextVersion =
        Math.max(
          0,
          ...existingVersions,
        ) + 1;

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
                  `Web Optimization V${nextVersion}`,
                phase:
                  "optimization",
                description:
                  "Controlled post-change web-search measurement reusing the exact frozen baseline prompt snapshots.",
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
            "Could not create optimization experiment.",
          ),
        );
      }

      const experiment =
        experimentData as SetupExperiment;

      setOptimizationExperiment(
        experiment
      );

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
                model_id:
                  null,
                experiment_id:
                  experiment.id,
                benchmark_mode:
                  baselineJob
                    .benchmark_mode,
                source_benchmark_job_id:
                  baselineJob.id,
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
            "Could not start optimization benchmark.",
          ),
        );
      }

      const created =
        benchmarkData as BenchmarkJob;

      setOptimizationJob(
        created
      );

      startPolling(
        created.id
      );

    } catch (startError) {
      setError(
        startError
          instanceof Error
          ? startError.message
          : "Could not start optimization.",
      );

    } finally {
      setStarting(false);
    }
  }


  const running =
    optimizationJob !== null
    && !isTerminal(
      optimizationJob.status
    );


  return (
    <section className="mt-8 crystal-panel rounded-[22px]">
      <div className="border-b border-slate-200/80 p-6">
        <div className="flex gap-4">
          <div className="crystal-step-badge">
            6
          </div>

          <div>
            <h2 className="font-semibold text-slate-950">
              Web Optimization Experiment
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Reuse the exact frozen Web Search
              baseline prompts after site changes.
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading experiment state...
          </div>
        ) : (
          <>
            <div className="crystal-subcard rounded-[18px] p-5">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                <Globe2 className="h-4 w-4 text-[#5f75ff]" />
                Frozen baseline source
              </div>

              {baselineJob ? (
                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex justify-between gap-4">
                    <span className="text-slate-500">
                      Experiment
                    </span>

                    <span className="text-right text-slate-700">
                      {baselineExperiment?.name
                        ?? `#${baselineJob.experiment_id}`}
                    </span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-slate-500">
                      Benchmark
                    </span>

                    <span className="text-slate-700">
                      #{baselineJob.id}
                    </span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-slate-500">
                      Frozen prompts
                    </span>

                    <span className="text-slate-700">
                      {baselineJob.total_prompts}
                    </span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-slate-500">
                      Model
                    </span>

                    <span className="text-slate-700">
                      {String(
                        baselineJob
                          .config_snapshot
                          .provider_model_id
                        ?? `Model #${baselineJob.model_id}`
                      )}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="mt-4 flex gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-700">
                  <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  No completed Web Search baseline is available yet.
                </div>
              )}
            </div>

            {optimizationJob && (
              <div className="mt-5 rounded-xl border border-slate-200/80 bg-[#fbfcff] p-5">
                <div className="flex items-center justify-between gap-5">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                      <FlaskConical className="h-4 w-4 text-emerald-400" />

                      {optimizationExperiment?.name
                        ?? "Web Optimization"}
                    </div>

                    <div className="mt-1 text-xs text-slate-500">
                      Benchmark #{optimizationJob.id}
                      {" · "}
                      {optimizationJob.status}
                    </div>
                  </div>

                  <div className="text-lg font-semibold text-emerald-700">
                    {Math.round(
                      optimizationJob
                        .progress_percentage
                    )}
                    %
                  </div>
                </div>

                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-emerald-400 transition-all"
                    style={{
                      width:
                        `${optimizationJob.progress_percentage}%`,
                    }}
                  />
                </div>

                <div className="mt-3 flex justify-between text-xs text-slate-500">
                  <span>
                    {optimizationJob.completed_runs}
                    {" / "}
                    {optimizationJob.total_prompts}
                    {" completed"}
                  </span>

                  <span>
                    {optimizationJob.failed_runs}
                    {" failed"}
                  </span>
                </div>

                {optimizationJob.status
                  === "completed"
                  && (
                    <div className="mt-4 flex items-center gap-2 text-sm text-emerald-700">
                      <CheckCircle2 className="h-4 w-4" />
                      Optimization measurement completed.
                    </div>
                  )}

                {optimizationJob.status
                  === "completed_with_errors"
                  && (
                    <div className="mt-4 flex items-center gap-2 text-sm text-amber-700">
                      <TriangleAlert className="h-4 w-4" />
                      Optimization completed with failed runs.
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

            {!running && (
              <div className="mt-5 flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    void loadState();
                  }}
                  disabled={
                    loading
                    || starting
                  }
                  className="flex items-center justify-center gap-2 rounded-xl border border-slate-300 px-4 py-3 text-sm font-medium text-slate-700 disabled:opacity-50"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </button>

                <button
                  type="button"
                  onClick={start}
                  disabled={
                    starting
                    || baselineJob === null
                    || (
                      optimizationJob !== null
                      && optimizationJob.status
                      === "completed"
                    )
                  }
                  className="crystal-primary-button flex-1 px-4 py-3 text-sm"
                >
                  {starting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Run Web Optimization
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
