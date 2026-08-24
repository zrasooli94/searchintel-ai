"use client";

import {
  Boxes,
  Building2,
  CheckCircle2,
  GitBranch,
  Package,
  Search,
  Tags,
  TriangleAlert,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import DashboardShell from "@/components/dashboard/dashboard-shell";

import type {
  EntitiesSummary,
  EntityRegistryItem,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  visibilitySummary: VisibilitySummary;
  entities: EntitiesSummary;
};


function pretty(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


function confidence(
  value: number | null,
) {
  if (value === null) {
    return "N/A";
  }

  return `${(
    value * 100
  ).toFixed(0)}%`;
}


function EntityTypeBadge({
  type,
}: {
  type: string;
}) {
  const classes: Record<
    string,
    string
  > = {
    brand:
      "bg-cyan-500/10 text-cyan-300",
    company:
      "bg-violet-500/10 text-violet-300",
    product:
      "bg-emerald-500/10 text-emerald-300",
    software_project:
      "bg-amber-500/10 text-amber-300",
    organization:
      "bg-blue-500/10 text-blue-300",
    service:
      "bg-pink-500/10 text-pink-300",
  };

  return (
    <span
      className={[
        "rounded-lg px-2.5 py-1 text-xs font-medium",
        classes[type] ??
          "bg-slate-800 text-slate-300",
      ].join(" ")}
    >
      {pretty(type)}
    </span>
  );
}


function childNames(
  entity: EntityRegistryItem,
) {
  return entity.child_relationships.map(
    (relationship) => ({
      id:
        relationship.subject_entity_id,

      name:
        relationship.subject_name,

      type:
        relationship.subject_type,

      relationship:
        relationship.relationship_type,
    }),
  );
}


export default function EntitiesDashboard({
  visibilitySummary,
  entities,
}: Props) {
  const [
    query,
    setQuery,
  ] = useState("");

  const [
    type,
    setType,
  ] = useState("all");

  const filtered =
    useMemo(
      () => {
        const normalized =
          query.trim().toLowerCase();

        return entities.entities.filter(
          (entity) => {
            if (
              type !== "all"
              && entity.entity_type
              !== type
            ) {
              return false;
            }

            if (!normalized) {
              return true;
            }

            const haystack = [
              entity.name,
              entity.rollup_brand ?? "",
              ...entity.aliases,
            ]
              .join(" ")
              .toLowerCase();

            return haystack.includes(
              normalized
            );
          },
        );
      },
      [
        entities.entities,
        query,
        type,
      ],
    );

  const hierarchyRoots =
    entities.entities.filter(
      (entity) =>
        entity.child_relationships
          .length > 0,
    );

  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Entities"
    >
      <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
        <section>
          <div>
            <div className="text-sm text-slate-500">
              Entity knowledge graph
            </div>

            <h2 className="mt-1 text-xl font-semibold text-white">
              Canonical Entity Registry
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Exact entities remain separate while
              products can roll up to commercial
              brands for visibility metrics.
            </p>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {[
              {
                label: "Total Entities",
                value:
                  entities.stats
                    .total_entities,
                icon: Boxes,
              },
              {
                label: "Brands + Companies",
                value:
                  entities.stats.brands
                  + entities.stats
                    .companies,
                icon: Building2,
              },
              {
                label: "Products",
                value:
                  entities.stats.products,
                icon: Package,
              },
              {
                label: "Software Projects",
                value:
                  entities.stats
                    .software_projects,
                icon: GitBranch,
              },
              {
                label: "Candidates",
                value:
                  entities.stats.candidates,
                icon: TriangleAlert,
              },
            ].map(
              ({
                label,
                value,
                icon: Icon,
              }) => (
                <div
                  key={label}
                  className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">
                      {label}
                    </span>

                    <div className="rounded-xl bg-slate-800 p-2.5">
                      <Icon className="h-4 w-4 text-cyan-400" />
                    </div>
                  </div>

                  <div className="mt-5 text-3xl font-semibold text-white">
                    {value}
                  </div>
                </div>
              ),
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-white">
                Typed Relationships
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Products and offerings linked to
                canonical parent entities.
              </p>
            </div>

            <GitBranch className="h-5 w-5 text-slate-600" />
          </div>

          {hierarchyRoots.length === 0 ? (
            <div className="mt-6 text-sm text-slate-500">
              No typed relationships.
            </div>
          ) : (
            <div className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {hierarchyRoots.map(
                (root) => (
                  <div
                    key={root.id}
                    className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium text-white">
                          {root.name}
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {root.project_role
                            ? pretty(
                                root.project_role,
                              )
                            : "Entity"}
                        </div>
                      </div>

                      <EntityTypeBadge
                        type={
                          root.entity_type
                        }
                      />
                    </div>

                    <div className="mt-4 space-y-2">
                      {childNames(
                        root,
                      ).map(
                        (child) => (
                          <div
                            key={
                              child.id
                            }
                            className="rounded-lg border border-slate-800 px-3 py-2.5"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-sm text-slate-300">
                                {
                                  child.name
                                }
                              </span>

                              <EntityTypeBadge
                                type={
                                  child.type
                                }
                              />
                            </div>

                            <div className="mt-1 text-xs text-slate-600">
                              {pretty(
                                child.relationship,
                              )}
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 p-5 lg:p-6">
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h2 className="font-semibold text-white">
                  Entity Registry
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Search canonical entities and
                  inspect their metric roll-ups.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" />

                  <input
                    value={query}
                    onChange={(
                      event,
                    ) =>
                      setQuery(
                        event.target.value,
                      )
                    }
                    placeholder="Search entities..."
                    className="w-64 rounded-xl border border-slate-800 bg-slate-950 py-2.5 pl-9 pr-3 text-sm text-slate-200 outline-none placeholder:text-slate-600 focus:border-cyan-500/50"
                  />
                </div>

                <select
                  value={type}
                  onChange={(
                    event,
                  ) =>
                    setType(
                      event.target.value,
                    )
                  }
                  className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2.5 text-sm text-slate-300 outline-none"
                >
                  <option value="all">
                    All types
                  </option>

                  <option value="brand">
                    Brands
                  </option>

                  <option value="company">
                    Companies
                  </option>

                  <option value="product">
                    Products
                  </option>

                  <option value="software_project">
                    Software projects
                  </option>

                  <option value="organization">
                    Organizations
                  </option>

                  <option value="service">
                    Services
                  </option>
                </select>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[1000px] text-left">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-4">
                    Entity
                  </th>

                  <th className="px-4 py-4">
                    Type
                  </th>

                  <th className="px-4 py-4">
                    Project role
                  </th>

                  <th className="px-4 py-4">
                    Metric roll-up
                  </th>

                  <th className="px-4 py-4">
                    Parent
                  </th>

                  <th className="px-4 py-4">
                    Aliases
                  </th>
                </tr>
              </thead>

              <tbody>
                {filtered.map(
                  (entity) => {
                    const parent =
                      entity
                        .parent_relationships[
                        0
                      ];

                    return (
                      <tr
                        key={entity.id}
                        className="border-b border-slate-800/70 last:border-0"
                      >
                        <td className="px-6 py-4">
                          <div className="font-medium text-slate-200">
                            {
                              entity.name
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-600">
                            ID #{entity.id}
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <EntityTypeBadge
                            type={
                              entity.entity_type
                            }
                          />
                        </td>

                        <td className="px-4 py-4 text-sm capitalize text-slate-400">
                          {entity.project_role ??
                            "—"}
                        </td>

                        <td className="px-4 py-4 text-sm text-slate-300">
                          {entity.rollup_brand ??
                            "Entity-only"}
                        </td>

                        <td className="px-4 py-4">
                          {parent ? (
                            <div>
                              <div className="text-sm text-slate-300">
                                {
                                  parent.object_name
                                }
                              </div>

                              <div className="mt-1 text-xs text-slate-600">
                                {pretty(
                                  parent.relationship_type,
                                )}
                              </div>
                            </div>
                          ) : (
                            <span className="text-sm text-slate-600">
                              —
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-4">
                          {entity.aliases.length >
                          0 ? (
                            <div className="flex flex-wrap gap-1.5">
                              {entity.aliases.map(
                                (
                                  alias,
                                ) => (
                                  <span
                                    key={
                                      alias
                                    }
                                    className="rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-300"
                                  >
                                    {
                                      alias
                                    }
                                  </span>
                                ),
                              )}
                            </div>
                          ) : (
                            <span className="text-sm text-slate-600">
                              —
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 p-5 lg:p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-white">
                  Candidate Review Queue
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  AI classification is advisory.
                  Candidates require curated
                  resolution before becoming
                  canonical entities.
                </p>
              </div>

              <TriangleAlert className="h-5 w-5 text-amber-400" />
            </div>
          </div>

          {entities.candidates.length ===
          0 ? (
            <div className="p-8">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />

              <div className="mt-3 text-sm text-slate-300">
                No unresolved candidates.
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[950px] text-left">
                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-6 py-4">
                      Candidate
                    </th>

                    <th className="px-4 py-4">
                      Suggested type
                    </th>

                    <th className="px-4 py-4">
                      Suggested parent
                    </th>

                    <th className="px-4 py-4">
                      Relationship
                    </th>

                    <th className="px-4 py-4">
                      Confidence
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {entities.candidates.map(
                    (candidate) => (
                      <tr
                        key={
                          candidate.rule_id
                        }
                        className="border-b border-slate-800/70 last:border-0"
                      >
                        <td className="px-6 py-4">
                          <div className="font-medium text-slate-200">
                            {
                              candidate.name
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-600">
                            Rule #
                            {
                              candidate.rule_id
                            }
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          {candidate.entity_type ? (
                            <EntityTypeBadge
                              type={
                                candidate.entity_type
                              }
                            />
                          ) : (
                            <span className="text-sm text-slate-600">
                              Unclassified
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-4 text-sm text-slate-300">
                          {
                            candidate
                              .proposed_parent_name ??
                            "—"
                          }
                        </td>

                        <td className="px-4 py-4 text-sm text-slate-400">
                          {candidate
                            .proposed_relationship_type
                            ? pretty(
                                candidate
                                  .proposed_relationship_type,
                              )
                            : "—"}
                        </td>

                        <td className="px-4 py-4">
                          <span className="text-sm font-medium text-slate-300">
                            {confidence(
                              candidate
                                .classification_confidence,
                            )}
                          </span>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <Tags className="h-5 w-5 text-cyan-400" />

            <div className="mt-4 text-2xl font-semibold text-white">
              {entities.stats.aliases}
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Canonical aliases
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <GitBranch className="h-5 w-5 text-cyan-400" />

            <div className="mt-4 text-2xl font-semibold text-white">
              {
                entities.stats
                  .relationships
              }
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Typed relationships
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />

            <div className="mt-4 text-2xl font-semibold text-white">
              {
                entities.stats
                  .resolved_rules
              }
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Resolved knowledge rules
            </div>
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
