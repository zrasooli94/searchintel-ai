"use client";

import {
  CheckCircle2,
  Clock3,
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
  ExperimentSummaryItem,
  ExperimentsSummary,
  SetupExperiment,
} from "@/lib/types";


type Props = {
  projectId: number;
  experiments: ExperimentsSummary;
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


function percent(
  value: number | null,
) {
  if (value === null) {
    return "N/A";
  }

  return `${value.toFixed(2)}%`;
}


function sourceBenchmarkId(
  job: BenchmarkJob | null,
) {
  if (!job) {
    return null;
  }

  const value =
    job.config_snapshot[
      "source_benchmark_job_id"
    ];

  return typeof value === "number"
    ? value
    : null;
}


function providerModel(
  job: BenchmarkJob | null,
) {
  if (!job) {
    return "—";
  }

  const value =
    job.config_snapshot[
      "provider_model_id"
    ];

  return typeof value === "string"
    ? value
    : `Model #${job.model_id}`;
}


function latestCompletedMonitoring(
  experiments: ExperimentsSummary,
): ExperimentSummaryItem | null {
  const matches =
    experiments.experiments
      .filter(
        (experiment) =>
          experiment.phase === "monitoring"
          && experiment.benchmark_mode
            === "web_search"
          && experiment.status
            === "completed",
      )
      .sort(
        (left, right) =>
          right.id - left.id,
      );

  return matches[0] ?? null;
}


function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <div className="text-xs text-slate-500">
        {label}
      </div>

      <div className="mt-2 text-xl font-semibold text-white">
        {value}
      </div>
    </div>
  );
}


export default function RetrievalMonitoringPanel({
  projectId,
  experiments,
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
    monitoringJob,
    setMonitoringJob,
  ] = useState<
    BenchmarkJob | null
  >(null);

  const [
    monitoringExperiment,
    setMonitoringExperiment,
  ] = useState<
    SetupExperiment | null
  >(null);

  const [
    experimentRegistry,
    setExperimentRegistry,
  ] = useState<
    SetupExperiment[]
  >([]);

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

  const latestSummary =
    latestCompletedMonitoring(
      experiments,
    );

  const retrievalDetected =
    (
      latestSummary
        ?.target_source_presence_rate
      ?? 0
    ) > 0;


  const stopPolling =
    useCallback(
      () => {
        if (
          timer.current !== null
        ) {
          clearInterval(
            timer.current,
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
              "Could not read retrieval benchmark.",
            ),
          );
        }

        const latest =
          data as BenchmarkJob;

        setMonitoringJob(
          latest,
        );

        if (
          isTerminal(
            latest.status,
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
                jobId,
              ).catch(
                (pollError) => {
                  stopPolling();

                  setError(
                    pollError
                      instanceof Error
                      ? pollError.message
                      : "Retrieval monitoring polling failed.",
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

          const projectExperiments =
            experimentData as SetupExperiment[];

          const jobs =
            jobData as BenchmarkJob[];

          setExperimentRegistry(
            projectExperiments,
          );

          const experimentById =
            new Map(
              projectExperiments.map(
                (experiment) => [
                  experiment.id,
                  experiment,
                ],
              ),
            );

          const baselines =
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
                    job.experiment_id,
                  );

                return (
                  experiment?.phase
                  === "baseline"
                );
              },
            );

          baselines.sort(
            (
              left,
              right,
            ) =>
              right.id - left.id,
          );

          const monitoringJobs =
            jobs.filter(
              (job) => {
                if (
                  job.experiment_id
                  === null
                  || job.benchmark_mode
                    !== "web_search"
                ) {
                  return false;
                }

                const experiment =
                  experimentById.get(
                    job.experiment_id,
                  );

                return (
                  experiment?.phase
                  === "monitoring"
                );
              },
            );

          monitoringJobs.sort(
            (
              left,
              right,
            ) =>
              right.id - left.id,
          );

          const latest =
            monitoringJobs[0]
            ?? null;

          const optimizationJobs =
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
                    job.experiment_id,
                  );

                return (
                  experiment?.phase
                  === "optimization"
                );
              },
            )
            .sort(
              (
                left,
                right,
              ) =>
                right.id - left.id,
            );

          const monitoringSourceId =
            sourceBenchmarkId(
              latest,
            );

          const optimizationSourceId =
            sourceBenchmarkId(
              optimizationJobs[0]
              ?? null,
            );

          const preferredSourceId =
            monitoringSourceId
            ?? optimizationSourceId;

          const pinnedBaseline =
            (
              preferredSourceId !== null
                ? baselines.find(
                    (job) =>
                      job.id
                      === preferredSourceId,
                  )
                : null
            )
            ?? baselines[0]
            ?? null;

          setBaselineJob(
            pinnedBaseline,
          );

          setBaselineExperiment(
            pinnedBaseline?.experiment_id
              ? (
                  experimentById.get(
                    pinnedBaseline
                      .experiment_id,
                  )
                  ?? null
                )
              : null,
          );

          setMonitoringJob(
            latest,
          );

          setMonitoringExperiment(
            latest?.experiment_id
              ? (
                  experimentById.get(
                    latest.experiment_id,
                  )
                  ?? null
                )
              : null,
          );

          if (
            latest
            && !isTerminal(
              latest.status,
            )
          ) {
            startPolling(
              latest.id,
            );
          }

        } catch (loadError) {
          setError(
            loadError
              instanceof Error
              ? loadError.message
              : "Could not load retrieval monitoring state.",
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
          initialLoad,
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
        "A completed Web Search baseline is required.",
      );

      return;
    }

    setStarting(true);
    setError(null);

    try {
      const existingVersions =
        experimentRegistry
          .filter(
            (experiment) =>
              experiment.phase
              === "monitoring",
          )
          .map(
            (experiment) => {
              const match =
                experiment.name.match(
                  /^Web Retrieval Check V(\d+)$/i,
                );

              return match
                ? Number(
                    match[1],
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
                  `Web Retrieval Check V${nextVersion}`,
                phase:
                  "monitoring",
                description:
                  "Controlled retrieval monitoring using the exact frozen Web Search baseline prompt snapshots and model.",
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
            "Could not create retrieval monitoring experiment.",
          ),
        );
      }

      const experiment =
        experimentData as SetupExperiment;

      setMonitoringExperiment(
        experiment,
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
            "Could not start retrieval monitoring benchmark.",
          ),
        );
      }

      const created =
        benchmarkData as BenchmarkJob;

      setMonitoringJob(
        created,
      );

      startPolling(
        created.id,
      );

    } catch (startError) {
      setError(
        startError
          instanceof Error
          ? startError.message
          : "Could not start retrieval monitoring.",
      );

    } finally {
      setStarting(false);
    }
  }


  const running =
    monitoringJob !== null
    && !isTerminal(
      monitoringJob.status,
    );


  return (
    <section className="rounded-2xl border border-cyan-500/20 bg-slate-900/60">
      <div className="border-b border-slate-800 p-5 lg:p-6">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
          <div>
            <div className="flex items-center gap-2 text-sm text-cyan-300">
              <Globe2 className="h-4 w-4" />
              Retrieval Monitoring
            </div>

            <h2 className="mt-2 text-lg font-semibold text-white">
              Frozen Web Retrieval Check
            </h2>

            <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
              Re-run the original Web Search baseline
              prompts and model to detect registered-domain
              retrieval without treating raw lexical
              mentions as evidence.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              void start();
            }}
            disabled={
              loading
              || starting
              || running
              || baselineJob === null
            }
            className="inline-flex min-w-[190px] items-center justify-center gap-2 rounded-xl border border-cyan-400 bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-800 disabled:text-slate-500 disabled:shadow-none"
          >
            {starting || running ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : latestSummary ? (
              <RefreshCw className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}

            {running
              ? "Retrieval Check Running"
              : latestSummary
                ? "Run Another Check"
                : "Run Retrieval Check"}
          </button>
        </div>
      </div>

      <div className="grid gap-6 p-5 lg:grid-cols-[0.9fr_1.4fr] lg:p-6">
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Frozen reference
          </div>

          {loading ? (
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading benchmark reference...
            </div>
          ) : baselineJob ? (
            <div className="mt-4 space-y-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">
                  Experiment
                </span>

                <span className="text-right text-slate-200">
                  {baselineExperiment?.name ?? "Baseline"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-500">
                  Benchmark
                </span>

                <span className="text-slate-200">
                  #{baselineJob.id}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-500">
                  Prompts
                </span>

                <span className="text-slate-200">
                  {baselineJob.total_prompts}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-500">
                  Model
                </span>

                <span className="text-right text-slate-200">
                  {providerModel(
                    baselineJob,
                  )}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-500">
                  Mode
                </span>

                <span className="text-cyan-300">
                  {baselineJob.benchmark_mode}
                </span>
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-300">
              No completed Web Search baseline is available.
            </div>
          )}

          {monitoringExperiment && monitoringJob && (
            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="flex items-center gap-2">
                {running ? (
                  <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                ) : (
                  <Clock3 className="h-4 w-4 text-slate-500" />
                )}

                <span className="text-sm font-medium text-slate-200">
                  {monitoringExperiment.name}
                </span>
              </div>

              <div className="mt-3 text-xs text-slate-500">
                Benchmark #{monitoringJob.id}
                {" · "}
                {monitoringJob.completed_runs}
                /
                {monitoringJob.total_prompts}
                {" completed · "}
                {monitoringJob.progress_percentage.toFixed(0)}
                %
              </div>
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between gap-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Latest completed check
            </div>

            {latestSummary && (
              <div
                className={[
                  "inline-flex items-center gap-2 rounded-lg px-2.5 py-1 text-xs font-medium",
                  retrievalDetected
                    ? "bg-emerald-500/10 text-emerald-300"
                    : "bg-slate-800 text-slate-400",
                ].join(" ")}
              >
                {retrievalDetected ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : (
                  <TriangleAlert className="h-3.5 w-3.5" />
                )}

                {retrievalDetected
                  ? "Target retrieval detected"
                  : "Target retrieval not detected"}
              </div>
            )}
          </div>

          {latestSummary ? (
            <>
              <div className="mt-4 text-lg font-semibold text-white">
                {latestSummary.name}
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <Metric
                  label="Target Source Presence"
                  value={percent(
                    latestSummary
                      .target_source_presence_rate,
                  )}
                />

                <Metric
                  label="Verified Coverage"
                  value={percent(
                    latestSummary
                      .entity_verified_target_mention_rate,
                  )}
                />

                <Metric
                  label="Retrieved Coverage"
                  value={percent(
                    latestSummary
                      .grounded_target_mention_rate,
                  )}
                />

                <Metric
                  label="Cited Coverage"
                  value={percent(
                    latestSummary
                      .target_cited_response_coverage,
                  )}
                />
              </div>

              <p className="mt-4 text-xs leading-5 text-slate-500">
                Retrieval status is determined by registered
                target source presence. Raw alias mentions do
                not trigger retrieval detection.
              </p>
            </>
          ) : (
            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/50 p-5">
              <div className="text-sm text-slate-300">
                No monitoring checks yet.
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Start a retrieval check after the target
                site has had time to propagate through
                external web-search retrieval systems.
              </p>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="border-t border-red-500/20 bg-red-500/5 px-5 py-4 text-sm text-red-300 lg:px-6">
          {error}
        </div>
      )}
    </section>
  );
}
