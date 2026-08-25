"use client";

import {
  CheckCircle2,
  Globe2,
  Loader2,
  RefreshCw,
  SearchCheck,
  TriangleAlert,
} from "lucide-react";

import {
  useRouter,
} from "next/navigation";

import {
  useState,
} from "react";

import type {
  CrawlResult,
  TechnicalAuditSetupState,
} from "@/lib/types";


type Props = {
  websiteId: number;

  initialPageCount: number;

  initialAudit:
    | TechnicalAuditSetupState
    | null;
};


function errorMessage(
  payload: unknown,
  fallback: string,
): string {
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
      typeof detail
      === "string"
    ) {
      return detail;
    }
  }

  return fallback;
}


export default function SetupTechnicalStep({
  websiteId,
  initialPageCount,
  initialAudit,
}: Props) {
  const router =
    useRouter();

  const [
    pages,
    setPages,
  ] = useState(
    initialPageCount,
  );

  const [
    audit,
    setAudit,
  ] = useState<
    TechnicalAuditSetupState
    | null
  >(
    initialAudit,
  );

  const [
    crawling,
    setCrawling,
  ] = useState(false);

  const [
    auditing,
    setAuditing,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState<
    string | null
  >(null);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  async function runCrawl() {
    setCrawling(true);
    setMessage(null);
    setError(null);

    try {
      const response =
        await fetch(
          `/api/websites/${websiteId}/crawl?max_pages=25`,
          {
            method: "POST",
          },
        );

      const payload =
        await response.json();

      if (!response.ok) {
        throw new Error(
          errorMessage(
            payload,
            "Website crawl failed.",
          ),
        );
      }

      const result =
        payload as CrawlResult;

      setPages(
        result.pages_crawled,
      );

      setMessage(
        `Crawl completed: ${result.pages_crawled} pages crawled, ${result.pages_failed} failed.`,
      );

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Website crawl failed.",
      );

    } finally {
      setCrawling(false);
    }
  }


  async function runAudit() {
    setAuditing(true);
    setMessage(null);
    setError(null);

    try {
      const response =
        await fetch(
          `/api/websites/${websiteId}/technical-audit`,
          {
            method: "POST",
          },
        );

      const payload =
        await response.json();

      if (!response.ok) {
        throw new Error(
          errorMessage(
            payload,
            "Technical audit failed.",
          ),
        );
      }

      const result =
        payload as TechnicalAuditSetupState;

      setAudit(result);

      setMessage(
        `Technical audit completed with score ${result.score}/100.`,
      );

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Technical audit failed.",
      );

    } finally {
      setAuditing(false);
    }
  }


  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400">
            2
          </div>

          <div>
            <h2 className="font-semibold text-white">
              Crawl & Technical Audit
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Discover the website first,
              then evaluate its technical
              SEO baseline.
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 p-6 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-5">
          <div className="flex items-center justify-between">
            <Globe2 className="h-5 w-5 text-cyan-400" />

            {pages > 0 && (
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            )}
          </div>

          <div className="mt-5 text-sm text-slate-500">
            Crawled pages
          </div>

          <div className="mt-1 text-3xl font-semibold text-white">
            {pages}
          </div>

          <button
            type="button"
            disabled={
              crawling
              || auditing
            }
            onClick={runCrawl}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {crawling ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Crawling...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                {pages > 0
                  ? "Re-crawl Website"
                  : "Run Crawl"}
              </>
            )}
          </button>

          <p className="mt-3 text-xs leading-5 text-slate-600">
            Maximum 25 pages for the
            onboarding crawl.
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-5">
          <div className="flex items-center justify-between">
            <SearchCheck className="h-5 w-5 text-cyan-400" />

            {audit && (
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            )}
          </div>

          <div className="mt-5 text-sm text-slate-500">
            Technical Audit V1
          </div>

          {audit ? (
            <>
              <div className="mt-1 text-3xl font-semibold text-white">
                {audit.score}
                <span className="text-lg text-slate-600">
                  /100
                </span>
              </div>

              <div className="mt-2 text-xs text-slate-500">
                {audit.pages_checked} pages checked ·{" "}
                {audit.issue_count} issues
              </div>
            </>
          ) : (
            <>
              <div className="mt-1 text-3xl font-semibold text-slate-600">
                —
              </div>

              <div className="mt-2 text-xs text-slate-600">
                No audit has been run.
              </div>
            </>
          )}

          <button
            type="button"
            disabled={
              pages === 0
              || crawling
              || auditing
            }
            onClick={runAudit}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-500/15 disabled:cursor-not-allowed disabled:border-slate-800 disabled:bg-slate-900 disabled:text-slate-600"
          >
            {auditing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Auditing...
              </>
            ) : (
              <>
                <SearchCheck className="h-4 w-4" />
                {audit
                  ? "Re-run Technical Audit"
                  : "Run Technical Audit"}
              </>
            )}
          </button>

          {pages === 0 && (
            <p className="mt-3 text-xs text-amber-400/80">
              Crawl the website before
              running an audit.
            </p>
          )}
        </div>
      </div>

      {(message || error) && (
        <div className="border-t border-slate-800 px-6 py-4">
          {message && (
            <div className="flex items-center gap-2 text-sm text-emerald-300">
              <CheckCircle2 className="h-4 w-4" />
              {message}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 text-sm text-red-300">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
