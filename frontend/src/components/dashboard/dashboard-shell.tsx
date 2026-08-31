"use client";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";
import type {
  ReactNode,
} from "react";

import {
  Bot,
  CircleCheck,
  Database,
  FlaskConical,
  FolderKanban,
  LayoutDashboard,
  ListChecks,
  ListTodo,
  FileText,
  Radar,
  Search,
} from "lucide-react";

export type DashboardShellSummary = {
  project_id: number;
  target: {
    brand: string;
  };
  experiment_name: string;
  experiment_status: string;
};


const navigation = [
  {
    label: "Overview",
    path: "",
    icon: LayoutDashboard,
  },
  {
    label: "Priority Center",
    path: "/priorities",
    icon: ListTodo,
  },
  {
    label: "Technical SEO",
    path: "/technical-seo",
    icon: Search,
  },
  {
    label: "AI Visibility",
    path: "/ai-visibility",
    icon: Bot,
  },
  {
    label: "Prompt Gaps",
    path: "/prompt-gaps",
    icon: Radar,
  },
  {
    label: "Experiments",
    path: "/experiments",
    icon: FlaskConical,
  },
  {
    label: "Entities",
    path: "/entities",
    icon: Database,
  },
  {
    label: "Action Plan",
    path: "/action-plan",
    icon: ListChecks,
  },
  {
    label: "Client Reports",
    path: "/client-reports",
    icon: FileText,
  },
];


type Props = {
  summary: DashboardShellSummary;
  title: string;
  children: ReactNode;
};


export default function DashboardShell({
  summary,
  title,
  children,
}: Props) {
  const pathname =
    usePathname();

  const base =
    `/projects/${summary.project_id}`;

  return (
    <div className="min-h-screen text-slate-900">
      <aside className="fixed inset-y-0 left-0 z-50 hidden w-[230px] border-r border-slate-200/70 bg-white/80 px-5 py-7 backdrop-blur-2xl xl:flex xl:flex-col">
        <Link
          href="/"
          className="flex items-center gap-3 px-2"
        >
          <div className="grid h-9 w-9 grid-cols-3 gap-[3px]">
            {Array.from({
              length: 9,
            }).map(
              (_, index) => (
                <span
                  key={index}
                  className={[
                    "rounded-full",
                    index % 2 === 0
                      ? "bg-[#7357ff]"
                      : "bg-[#42a5ff]",
                  ].join(" ")}
                />
              ),
            )}
          </div>

          <div>
            <div className="text-[15px] font-semibold tracking-[-0.03em] text-slate-950">
              SearchIntel
            </div>

            <div className="mt-0.5 text-[10px] text-slate-400">
              Search Intelligence
            </div>
          </div>
        </Link>

        <nav className="mt-12 space-y-1.5">
          {navigation.map(
            ({
              label,
              path,
              icon: Icon,
            }) => {
              const href =
                `${base}${path}`;

              const active =
                path === ""
                  ? pathname === base
                  : pathname.startsWith(
                      href,
                    );

              return (
                <Link
                  key={href}
                  href={href}
                  className={[
                    "group flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm transition-all duration-300",
                    active
                      ? "bg-gradient-to-r from-[#eef4ff] to-[#f5f1ff] text-[#4d49d8]"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                  ].join(" ")}
                >
                  <Icon
                    className={[
                      "h-[17px] w-[17px]",
                      active
                        ? "text-[#5f63ff]"
                        : "text-slate-500 group-hover:text-slate-800",
                    ].join(" ")}
                    strokeWidth={1.7}
                  />

                  {label}
                </Link>
              );
            },
          )}
        </nav>

        <div className="mt-auto space-y-3">
          <div className="rounded-2xl border border-slate-200/80 bg-white/85 p-4 shadow-[0_10px_35px_rgba(79,90,130,0.05)]">
            <div className="text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-400">
              Current target
            </div>

            <div className="mt-3 font-medium text-slate-900">
              {summary.target.brand}
            </div>

            <div className="mt-1 text-xs text-slate-400">
              Project #{summary.project_id}
            </div>
          </div>

          <Link
            href="/"
            className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white/80 px-3 py-2.5 text-xs font-medium text-slate-600 shadow-sm transition hover:border-violet-300 hover:text-violet-700"
          >
            <FolderKanban className="h-4 w-4" />
            Switch project
          </Link>
        </div>
      </aside>

      <main className="xl:pl-[230px]">
        <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/72 px-5 py-5 backdrop-blur-2xl lg:px-8">
          <div className="mx-auto flex max-w-[1450px] items-center justify-between">
            <div>
              <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-400">
                Visibility intelligence
              </div>

              <h1 className="mt-1.5 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                {title}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden rounded-full border border-slate-200 bg-white px-4 py-2 text-xs text-slate-600 shadow-sm sm:block">
                {summary.experiment_name}
              </div>

              <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3.5 py-2 text-xs font-medium text-emerald-700">
                <CircleCheck className="h-4 w-4" />

                {summary.experiment_status}
              </div>
            </div>
          </div>
        </header>

        {children}
      </main>
    </div>
  );
}
