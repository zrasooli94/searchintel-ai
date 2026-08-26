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
      "border border-blue-200 bg-blue-50 text-blue-700",
    company:
      "border border-violet-200 bg-violet-50 text-violet-700",
    product:
      "border border-emerald-200 bg-emerald-50 text-emerald-700",
    software_project:
      "border border-amber-200 bg-amber-50 text-amber-700",
    organization:
      "border border-indigo-200 bg-indigo-50 text-indigo-700",
    service:
      "border border-rose-200 bg-rose-50 text-rose-700",
  };

  return (
    <span
      className={[
        "rounded-full px-2.5 py-1 text-[11px] font-medium",
        classes[type] ??
          "bg-slate-100 text-slate-700",
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

  const targetEntity =
    entities.entities.find(
      (entity) =>
        entity.project_role === "target",
    ) ?? null;

  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Entities"
    >
      <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
        <section>
          <div>
            <div className="crystal-eyebrow">
              Entity knowledge graph
            </div>

            <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
              Canonical Entity Registry
            </h2>

            <p className="mt-1.5 text-sm text-slate-500">
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
                  className="crystal-card rounded-[20px] p-5"
                >
                  <div className="flex items-center justify-between">
                    <span className="crystal-eyebrow">
                      {label}
                    </span>

                    <div className="crystal-icon h-10 w-10">
                      <Icon className="h-[18px] w-[18px] text-[#5f75ff]" />
                    </div>
                  </div>

                  <div className="crystal-value mt-5 text-3xl font-medium">
                    {value}
                  </div>
                </div>
              ),
            )}
          </div>
        </section>

        {targetEntity && (
          <section className="crystal-panel rounded-[22px] p-6">
            <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr] lg:items-center">
              <div>
                <div className="crystal-eyebrow">
                  Target identity
                </div>

                <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                  {targetEntity.name}
                </h2>

                <p className="mt-2 max-w-xl text-sm leading-7 text-slate-600">
                  Canonical project target used for
                  entity-aware visibility and identity
                  resolution.
                </p>

                <div className="mt-5 flex flex-wrap gap-2">
                  <EntityTypeBadge
                    type={targetEntity.entity_type}
                  />

                  <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700">
                    Target
                  </span>

                  <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">
                    ID #{targetEntity.id}
                  </span>
                </div>
              </div>

              <div className="crystal-subcard rounded-[18px] p-5">
                <div className="crystal-eyebrow">
                  Known aliases
                </div>

                {targetEntity.aliases.length > 0 ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {targetEntity.aliases.map(
                      (alias) => (
                        <span
                          key={alias}
                          className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700"
                        >
                          {alias}
                        </span>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">
                    No canonical aliases registered.
                  </p>
                )}
              </div>
            </div>
          </section>
        )}

        <section className="crystal-panel rounded-[22px] p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-950">
                Typed Relationships
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Products and offerings linked to
                canonical parent entities.
              </p>
            </div>

            <GitBranch className="h-5 w-5 text-slate-400" />
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
                    className="crystal-subcard rounded-[18px] p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium text-slate-950">
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
                            className="rounded-xl border border-slate-200/70 bg-white/75 px-3 py-2.5 transition hover:bg-white"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-sm text-slate-700">
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

                            <div className="mt-1 text-xs text-slate-400">
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

        <section className="crystal-panel rounded-[22px]">
          <div className="p-5 pb-4 lg:p-6 lg:pb-4">
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h2 className="font-semibold text-slate-950">
                  Entity Registry
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Search canonical entities and
                  inspect their metric roll-ups.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

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
                    className="crystal-field w-64 py-2.5 pl-9 pr-3 text-sm"
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
                  className="crystal-field w-auto px-3 py-2.5 text-sm"
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
                <tr className="border-y border-slate-200/70 bg-slate-50/55 text-[11px] uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-6 py-3.5">
                    Entity
                  </th>

                  <th className="px-4 py-3.5">
                    Type
                  </th>

                  <th className="px-4 py-3.5">
                    Project role
                  </th>

                  <th className="px-4 py-3.5">
                    Metric roll-up
                  </th>

                  <th className="px-4 py-3.5">
                    Parent
                  </th>

                  <th className="px-4 py-3.5">
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
                        className="border-b border-slate-200/65 transition hover:bg-slate-50/55 last:border-0"
                      >
                        <td className="px-6 py-3.5">
                          <div className="font-medium text-slate-900">
                            {
                              entity.name
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-400">
                            ID #{entity.id}
                          </div>
                        </td>

                        <td className="px-4 py-3.5">
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

                        <td className="px-4 py-4 text-sm text-slate-700">
                          {entity.rollup_brand ??
                            "Entity-only"}
                        </td>

                        <td className="px-4 py-3.5">
                          {parent ? (
                            <div>
                              <div className="text-sm text-slate-700">
                                {
                                  parent.object_name
                                }
                              </div>

                              <div className="mt-1 text-xs text-slate-400">
                                {pretty(
                                  parent.relationship_type,
                                )}
                              </div>
                            </div>
                          ) : (
                            <span className="text-sm text-slate-400">
                              —
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-3.5">
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
                                    className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-slate-600"
                                  >
                                    {
                                      alias
                                    }
                                  </span>
                                ),
                              )}
                            </div>
                          ) : (
                            <span className="text-sm text-slate-400">
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

        <section className="crystal-panel rounded-[22px]">
          <div className="p-5 pb-4 lg:p-6 lg:pb-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-slate-950">
                  Candidate Review Queue
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  AI classification is advisory.
                  Candidates require curated
                  resolution before becoming
                  canonical entities.
                </p>
              </div>

              <TriangleAlert className="h-5 w-5 text-amber-600" />
            </div>
          </div>

          {entities.candidates.length ===
          0 ? (
            <div className="p-8">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />

              <div className="mt-3 text-sm text-slate-700">
                No unresolved candidates.
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[950px] text-left">
                <thead>
                  <tr className="border-y border-slate-200/70 bg-slate-50/55 text-[11px] uppercase tracking-[0.1em] text-slate-500">
                    <th className="px-6 py-3.5">
                      Candidate
                    </th>

                    <th className="px-4 py-3.5">
                      Suggested type
                    </th>

                    <th className="px-4 py-3.5">
                      Suggested parent
                    </th>

                    <th className="px-4 py-3.5">
                      Relationship
                    </th>

                    <th className="px-4 py-3.5">
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
                        className="border-b border-slate-200/65 transition hover:bg-slate-50/55 last:border-0"
                      >
                        <td className="px-6 py-3.5">
                          <div className="font-medium text-slate-900">
                            {
                              candidate.name
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-400">
                            Rule #
                            {
                              candidate.rule_id
                            }
                          </div>
                        </td>

                        <td className="px-4 py-3.5">
                          {candidate.entity_type ? (
                            <EntityTypeBadge
                              type={
                                candidate.entity_type
                              }
                            />
                          ) : (
                            <span className="text-sm text-slate-400">
                              Unclassified
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-4 text-sm text-slate-700">
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

                        <td className="px-4 py-3.5">
                          <span className="text-sm font-medium text-slate-700">
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
          <div className="crystal-card rounded-[20px] p-5">
            <div className="crystal-icon h-10 w-10">
              <Tags className="h-5 w-5 text-[#5f75ff]" />
            </div>

            <div className="crystal-value mt-4 text-2xl font-medium">
              {entities.stats.aliases}
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Canonical aliases
            </div>
          </div>

          <div className="crystal-card rounded-[20px] p-5">
            <div className="crystal-icon h-10 w-10">
              <GitBranch className="h-5 w-5 text-[#5f75ff]" />
            </div>

            <div className="crystal-value mt-4 text-2xl font-medium">
              {
                entities.stats
                  .relationships
              }
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Typed relationships
            </div>
          </div>

          <div className="crystal-card rounded-[20px] p-5">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />

            <div className="crystal-value mt-4 text-2xl font-medium">
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
