import {
  ArrowRight,
  Construction,
} from "lucide-react";

import DashboardShell from "@/components/dashboard/dashboard-shell";

import type {
  VisibilitySummary,
} from "@/lib/types";

type Props = {
  summary: VisibilitySummary;
  title: string;
  description: string;
};

export default function SectionPage({
  summary,
  title,
  description,
}: Props) {
  return (
    <DashboardShell
      summary={summary}
      title={title}
    >
      <div className="mx-auto max-w-7xl p-5 lg:p-8">
        <div className="crystal-panel rounded-[22px] p-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400/10">
            <Construction className="h-5 w-5 text-cyan-400" />
          </div>

          <h2 className="mt-6 text-2xl font-semibold text-slate-950">
            {title}
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            {description}
          </p>

          <div className="mt-8 flex items-center gap-2 text-sm font-medium text-cyan-400">
            SearchIntel module
            <ArrowRight className="h-4 w-4" />
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
