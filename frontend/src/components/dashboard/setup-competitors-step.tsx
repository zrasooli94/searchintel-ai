"use client";

import {
  Building2,
  CheckCircle2,
  Globe2,
  Loader2,
  Plus,
  TriangleAlert,
} from "lucide-react";

import {
  FormEvent,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import type {
  ProjectCompetitor,
} from "@/lib/types";


type Props = {
  projectId: number;
  initialCompetitors: ProjectCompetitor[];
};


export default function SetupCompetitorsStep({
  projectId,
  initialCompetitors,
}: Props) {
  const router = useRouter();

  const [
    competitors,
    setCompetitors,
  ] = useState(
    initialCompetitors,
  );

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

    const formElement =
      event.currentTarget;

    setLoading(true);
    setError(null);

    const form =
      new FormData(
        formElement,
      );

    const payload = {
      name:
        String(
          form.get("name") ?? "",
        ),

      website_url:
        String(
          form.get("website_url")
          ?? "",
        ) || null,
    };

    try {
      const response = await fetch(
        `/api/projects/${projectId}/competitors`,
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
        throw new Error(
          typeof data?.detail
          === "string"
            ? data.detail
            : "Could not add competitor.",
        );
      }

      setCompetitors(
        (current) => [
          ...current,
          {
            brand_id:
              data.brand_id,

            name:
              data.name,

            website_id:
              data.website_id,

            domain:
              data.domain,

            base_url:
              data.base_url,
          },
        ].sort(
          (a, b) =>
            a.name.localeCompare(
              b.name,
            ),
        ),
      );

      formElement.reset();

      router.refresh();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not add competitor.",
      );

    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 p-6">
        <div className="flex items-start justify-between gap-5">
          <div className="flex gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400">
              3
            </div>

            <div>
              <h2 className="font-semibold text-white">
                Competitors
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Register brands that should
                participate in visibility
                comparisons.
              </p>
            </div>
          </div>

          <div className="rounded-xl bg-slate-800 px-3 py-2 text-sm font-medium text-slate-300">
            {competitors.length} configured
          </div>
        </div>
      </div>

      <div className="grid gap-6 p-6 lg:grid-cols-[0.9fr_1.1fr]">
        <form
          onSubmit={submit}
          className="rounded-xl border border-slate-800 bg-slate-950/50 p-5"
        >
          <div className="flex items-center gap-2 font-medium text-white">
            <Plus className="h-4 w-4 text-cyan-400" />
            Add Competitor
          </div>

          <div className="mt-5">
            <label className="text-sm text-slate-400">
              Brand name
            </label>

            <input
              required
              minLength={2}
              name="name"
              placeholder="Example competitor"
              className="mt-2 w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-500/50"
            />
          </div>

          <div className="mt-4">
            <label className="text-sm text-slate-400">
              Website
            </label>

            <input
              name="website_url"
              type="url"
              placeholder="https://competitor.com"
              className="mt-2 w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-500/50"
            />

            <p className="mt-2 text-xs leading-5 text-slate-600">
              Recommended for web-search
              source attribution.
            </p>
          </div>

          {error && (
            <div className="mt-4 flex gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            disabled={loading}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" />
                Add Competitor
              </>
            )}
          </button>
        </form>

        <div className="rounded-xl border border-slate-800 bg-slate-950/50">
          <div className="border-b border-slate-800 px-5 py-4">
            <div className="font-medium text-white">
              Configured Competitors
            </div>
          </div>

          {competitors.length === 0 ? (
            <div className="p-8 text-center">
              <Building2 className="mx-auto h-6 w-6 text-slate-600" />

              <div className="mt-3 text-sm text-slate-500">
                No competitors configured.
              </div>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {competitors.map(
                (competitor) => (
                  <div
                    key={
                      competitor.brand_id
                    }
                    className="flex items-center justify-between gap-4 px-5 py-4"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <div className="font-medium text-slate-200">
                          {competitor.name}
                        </div>

                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      </div>

                      <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
                        <Globe2 className="h-3.5 w-3.5" />

                        {competitor.domain ??
                          "No website registered"}
                      </div>
                    </div>

                    <div className="text-xs text-slate-600">
                      Brand #
                      {competitor.brand_id}
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
