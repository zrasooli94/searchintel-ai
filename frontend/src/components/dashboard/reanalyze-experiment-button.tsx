"use client";

import {
  CheckCircle2,
  Loader2,
  RefreshCcw,
  TriangleAlert,
} from "lucide-react";

import {
  useRouter,
} from "next/navigation";

import {
  useState,
} from "react";


type Result = {
  analysis_version: string;

  total_responses: number;
  stale_before: number;
  skipped_current: number;

  reanalyzed: number;
  failed: number;

  current_after: number;
  stale_after: number;

  analysis_is_current: boolean;
};


type Props = {
  projectId: number;
  experimentId: number;

  staleResponses: number;
  totalResponses: number;
};


export default function ReanalyzeExperimentButton({
  projectId,
  experimentId,
  staleResponses,
  totalResponses,
}: Props) {
  const router = useRouter();

  const [
    running,
    setRunning,
  ] = useState(false);

  const [
    result,
    setResult,
  ] = useState<Result | null>(
    null,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  async function reanalyze() {
    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(
        `/api/projects/${projectId}/experiments/${experimentId}/reanalyze`,
        {
          method: "POST",
        },
      );

      const payload =
        await response.json();

      if (!response.ok) {
        throw new Error(
          payload.detail ??
          "Re-analysis failed.",
        );
      }

      setResult(
        payload as Result,
      );

      router.refresh();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Re-analysis failed.",
      );
    } finally {
      setRunning(false);
    }
  }

  if (
    result?.analysis_is_current
  ) {
    return (
      <div className="mt-3 inline-flex items-center gap-2 text-xs font-medium text-emerald-700">
        <CheckCircle2 className="h-4 w-4" />

        Analysis current ·{" "}
        {result.current_after}/
        {result.total_responses}
      </div>
    );
  }

  return (
    <div className="mt-3">
      <button
        type="button"
        disabled={
          running
          || totalResponses === 0
        }
        onClick={reanalyze}
        className="crystal-primary-button px-3.5 py-2 text-xs"
      >
        {running ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Re-analyzing...
          </>
        ) : (
          <>
            <RefreshCcw className="h-3.5 w-3.5" />
            Re-analyze stored responses
          </>
        )}
      </button>

      <div className="mt-2 text-[11px] leading-5 text-amber-700/75">
        Stored responses only · no new AI or
        web-search measurement run.
      </div>

      {error && (
        <div className="mt-2 flex items-center gap-2 text-xs text-red-700">
          <TriangleAlert className="h-3.5 w-3.5" />
          {error}
        </div>
      )}

      {!running &&
        staleResponses > 0 && (
          <div className="mt-1 text-[11px] text-slate-500">
            {staleResponses} of{" "}
            {totalResponses} responses need
            the current analyzer.
          </div>
        )}

      {!running &&
        staleResponses === 0 &&
        totalResponses > 0 && (
          <div className="mt-1 text-[11px] text-slate-500">
            Force a derived-data rebuild after
            changing brand, domain, alias, or
            competitor configuration.
          </div>
        )}
    </div>
  );
}
