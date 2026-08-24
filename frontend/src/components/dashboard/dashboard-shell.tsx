"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import {
  Bot,
  ChevronRight,
  CircleCheck,
  Database,
  FlaskConical,
  FolderKanban,
  LayoutDashboard,
  ListChecks,
  Radar,
  Search,
  Sparkles,
} from "lucide-react";

import type {
  VisibilitySummary,
} from "@/lib/types";


const navigation = [
  {
    label: "Overview",
    path: "",
    icon: LayoutDashboard,
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
];


type Props = {
  summary: VisibilitySummary;
  title: string;
  children: ReactNode;
};


export default function DashboardShell({
  summary,
  title,
  children,
}: Props) {
  const pathname = usePathname();

  const base =
    `/projects/${summary.project_id}`;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-800 bg-slate-950 lg:block">
        <Link
          href="/"
          className="flex h-20 items-center border-b border-slate-800 px-6"
        >
          <div className="mr-3 rounded-xl bg-cyan-400/10 p-2">
            <Sparkles className="h-5 w-5 text-cyan-400" />
          </div>

          <div>
            <div className="font-semibold text-white">
              SearchIntel
            </div>

            <div className="text-xs text-slate-500">
              Search Intelligence
            </div>
          </div>
        </Link>

        <nav className="space-y-1 p-4">
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
                    "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition",
                    active
                      ? "bg-slate-800 text-white"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4" />

                  {label}

                  {active && (
                    <ChevronRight className="ml-auto h-4 w-4 text-slate-500" />
                  )}
                </Link>
              );
            },
          )}
        </nav>

        <div className="absolute bottom-5 left-4 right-4 space-y-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Current target
            </div>

            <div className="mt-2 font-medium text-white">
              {summary.target.brand}
            </div>

            <div className="mt-1 text-xs text-slate-500">
              Project #{summary.project_id}
            </div>
          </div>

          <Link
            href="/"
            className="flex items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-950 px-3 py-2.5 text-xs font-medium text-slate-400 transition hover:bg-slate-900 hover:text-white"
          >
            <FolderKanban className="h-4 w-4" />
            Switch project
          </Link>
        </div>
      </aside>

      <main className="lg:pl-64">
        <header className="border-b border-slate-800 bg-slate-950/90 px-5 py-5 backdrop-blur lg:px-8">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <div>
              <div className="text-sm text-slate-500">
                Visibility intelligence
              </div>

              <h1 className="mt-1 text-xl font-semibold text-white">
                {title}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300 sm:block">
                {summary.experiment_name}
              </div>

              <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-300">
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
