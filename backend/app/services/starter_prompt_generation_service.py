import json
import math
import re
from collections import Counter
from difflib import SequenceMatcher
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.ai.provider_factory import ProviderFactory
from app.models.prompt_set_proposal import PromptSetProposal
from app.repositories.ai_engine_repository import AIEngineRepository
from app.repositories.page_repository import PageRepository
from app.repositories.project_brand_repository import ProjectBrandRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.prompt_repository import PromptRepository
from app.repositories.website_repository import WebsiteRepository
from app.services.ai_model_service import AIModelService


class StarterPromptGenerationService:
    GENERATOR_VERSION = "semantic-classification-v6"
    REPAIR_GENERATOR_VERSION = "coverage-repair-v1"
    MAX_TOPIC_SHARE = 0.35
    MAX_FAMILY_SHARE = 0.40
    MAX_SUPER_THEME_SHARE = 0.45
    REQUIRED_INTENTS = {"brand", "informational", "problem_solution", "recommendation", "comparison", "commercial"}
    VALID_CATEGORIES = REQUIRED_INTENTS | {"navigational", "transactional"}
    STOP_WORDS = {
        "about", "with", "from", "your", "this", "that", "have", "more", "page",
        "home", "official", "platform", "solutions", "product", "products", "learn",
        "resources", "documentation", "developers", "company", "using", "build",
    }
    AI_AGENT_THEME_TERMS = {
        "ai", "agent", "agents", "agentic", "llm", "llms", "model", "models",
        "generative", "inference",
    }
    SEMANTIC_DOMAINS = {
        "ai_agent": {
            "name": "AI / Agent Ecosystem",
            "phrases": {
                "agent": 3, "agents": 3, "agentic": 3, "ai application": 3, "ai-generated": 3,
                "ai generated": 3, "aigenerated": 3, "ai gateway": 4, "ai sdk": 4, "ai model": 3,
                "model provider": 3, "llm": 3, "generative ai": 3,
            },
        },
        "payments": {
            "name": "Payments Ecosystem",
            "phrases": {
                "payment processing": 4, "payment gateway": 4, "checkout": 3,
                "payment fraud": 4, "billing": 2, "invoicing": 3, "merchant": 2,
            },
        },
        "marketing_crm": {
            "name": "Marketing / CRM Ecosystem",
            "phrases": {
                "crm": 4, "lead nurturing": 4, "marketing automation": 4,
                "sales pipeline": 3, "customer relationship": 3, "campaign automation": 3,
            },
        },
    }

    @staticmethod
    def normalize_text(value: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", value.strip().lower()))

    @classmethod
    def semantic_theme_signature(cls, value: str) -> str:
        terms = set(cls.normalize_text(value).split())
        if terms & cls.AI_AGENT_THEME_TERMS:
            return "ai_agent_ecosystem"
        return " ".join(sorted(terms))

    @classmethod
    def grouped_theme_names(cls, topic_clusters: list[dict]) -> dict[str, str]:
        raw_names = {
            item.get("super_theme") or item.get("topic_family") or item["name"]
            for item in topic_clusters
        }
        return {
            name: " / ".join(sorted(
                candidate for candidate in raw_names
                if cls.semantic_theme_signature(candidate) == cls.semantic_theme_signature(name)
            ))
            for name in raw_names
        }

    @classmethod
    def semantic_prompt_classification(cls, prompt: dict, cluster: dict) -> dict:
        normalized = cls.normalize_text(prompt.get("text", ""))
        provider_theme = cluster.get("super_theme") or cluster.get("topic_family") or cluster.get("name", "")
        provider_signature = cls.semantic_theme_signature(provider_theme)
        scores = {}
        tokens = set(normalized.split())
        for key, domain in cls.SEMANTIC_DOMAINS.items():
            score = sum(
                weight for phrase, weight in domain["phrases"].items()
                if (phrase in normalized if " " in phrase or phrase == "aigenerated" else phrase in tokens)
            )
            if key == "ai_agent" and provider_signature == "ai_agent_ecosystem":
                score += 3
            scores[key] = score
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        primary_key, primary_score = ranked[0]
        secondary = [
            cls.SEMANTIC_DOMAINS[key]["name"] for key, score in ranked[1:]
            if score >= 3 and primary_score - score <= 1
        ]
        if primary_score < 3:
            return {
                "effective_micro_cluster": cluster.get("name") or prompt.get("topic_cluster"),
                "effective_topic_family": cluster.get("topic_family") or cluster.get("name") or prompt.get("topic_cluster"),
                "effective_super_theme": provider_theme,
                "secondary_themes": [],
                "confidence": "metadata_supported",
                "reclassified": False,
            }
        if primary_key == "ai_agent":
            if any(value in normalized for value in ("gateway", "sdk", "model provider", "ai model")):
                micro = "AI model access"
            elif any(value in normalized for value in ("sandbox", "generated code", "ai generated")):
                micro = "Secure AI execution"
            elif any(value in normalized for value in ("connect", "integration", "external service")):
                micro = "AI application integration"
            else:
                micro = "Agent development and orchestration"
            family = "AI and agent infrastructure"
        elif primary_key == "payments":
            micro = "Payment risk and checkout" if any(value in normalized for value in ("fraud", "checkout")) else "Payment operations"
            family = "Payments"
        else:
            micro = "Marketing automation" if "automation" in normalized else "CRM operations"
            family = "Marketing and CRM"
        effective_theme = cls.SEMANTIC_DOMAINS[primary_key]["name"]
        return {
            "effective_micro_cluster": micro,
            "effective_topic_family": family,
            "effective_super_theme": effective_theme,
            "secondary_themes": secondary,
            "confidence": "high" if primary_score >= 4 else "medium",
            "reclassified": cls.semantic_theme_signature(effective_theme) != provider_signature,
        }

    @classmethod
    def is_near_duplicate(cls, value: str, existing: list[str]) -> bool:
        normalized = cls.normalize_text(value)
        words = set(normalized.split())
        for candidate in existing:
            other = cls.normalize_text(candidate)
            other_words = set(other.split())
            overlap = len(words & other_words) / max(1, len(words | other_words))
            if normalized == other or SequenceMatcher(None, normalized, other).ratio() >= 0.88 or overlap >= 0.8:
                return True
        return False

    @staticmethod
    def extract_json(response_text: str) -> dict:
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text.strip(), flags=re.I)
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise HTTPException(status_code=502, detail="AI prompt generator did not return valid JSON.")
            try:
                value = json.loads(text[start:end + 1])
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=502, detail="AI prompt generator returned malformed JSON.") from exc
        if not isinstance(value, dict):
            raise HTTPException(status_code=502, detail="Unexpected generator response format.")
        return value

    @classmethod
    def evidence_terms(cls, pages: list) -> list[str]:
        counts: Counter[str] = Counter()
        for page in pages:
            parsed = urlparse(page.url)
            values = [page.title or "", page.h1 or "", parsed.path.replace("-", " ").replace("/", " ")]
            page_terms = set()
            for value in values:
                for token in re.findall(r"[A-Za-z][A-Za-z0-9+.-]{2,}", value.lower()):
                    token = token.strip(".-")
                    if token not in cls.STOP_WORDS and not token.isdigit():
                        page_terms.add(token)
            counts.update(page_terms)
        return [term for term, _count in counts.most_common(30)]

    @classmethod
    def evidence_tiers(cls, pages: list) -> dict[str, list]:
        def depth(page) -> int:
            return len([part for part in urlparse(page.url).path.split("/") if part])

        homepage = [page for page in pages if depth(page) == 0]
        top_level = [page for page in pages if depth(page) == 1]
        broader = [page for page in pages if page not in homepage and page not in top_level]
        return {
            "homepage": homepage,
            "top_level": sorted(top_level, key=lambda item: item.url),
            "broader_corpus": sorted(broader, key=lambda item: item.url),
        }

    @classmethod
    def crawl_sample_bias_signal(cls, pages: list) -> dict:
        tiers = cls.evidence_tiers(pages)

        def page_terms(page) -> set[str]:
            parsed = urlparse(page.url)
            values = [page.title or "", page.h1 or "", parsed.path.replace("-", " ").replace("/", " ")]
            return {
                token.strip(".-")
                for value in values
                for token in re.findall(r"[A-Za-z][A-Za-z0-9+.-]{2,}", value.lower())
                if token.strip(".-") not in cls.STOP_WORDS and not token.strip(".-").isdigit()
            }

        strong_terms = set().union(*(page_terms(page) for tier in ("homepage", "top_level")
                                     for page in tiers[tier]))
        deep_pages = tiers["broader_corpus"]
        counts = Counter(term for page in deep_pages for term in page_terms(page))
        candidates = [
            (term, count) for term, count in counts.most_common()
            if term not in strong_terms and count / max(1, len(deep_pages)) >= 0.4
        ]
        if len(deep_pages) < 5 or not candidates:
            return {"detected": False, "reason": None, "evidence": []}
        term, count = candidates[0]
        return {
            "detected": True,
            "reason": (
                f"The bounded crawl repeatedly emphasizes '{term}' on {count} of {len(deep_pages)} "
                "deeper pages without matching emphasis in stored homepage/top-level evidence."
            ),
            "evidence": [page.url for page in deep_pages if term in page_terms(page)][:4],
        }

    @classmethod
    def coverage(
        cls,
        prompts: list[dict],
        scope: str,
        topic_clusters: list[dict] | None = None,
        core_category: dict | None = None,
        crawl_sample_bias: dict | None = None,
    ) -> tuple[dict, list[str]]:
        provider_topics = Counter(item["topic_cluster"] for item in prompts)
        intents = Counter(item["category"] for item in prompts)
        family_by_cluster = {
            item["name"]: item.get("topic_family") or item["name"]
            for item in (topic_clusters or [])
        }
        provider_families = Counter(
            family_by_cluster.get(item["topic_cluster"], item["topic_cluster"])
            for item in prompts
        )
        raw_theme_by_cluster = {
            item["name"]: item.get("super_theme") or item.get("topic_family") or item["name"]
            for item in (topic_clusters or [])
        }
        grouped_theme_names = cls.grouped_theme_names(topic_clusters or [])
        theme_by_cluster = {
            cluster: grouped_theme_names[theme]
            for cluster, theme in raw_theme_by_cluster.items()
        }
        provider_super_themes = Counter(
            theme_by_cluster.get(item["topic_cluster"], item["topic_cluster"])
            for item in prompts
        )
        cluster_meta = {item["name"]: item for item in (topic_clusters or [])}
        effective_classifications = []
        for index, prompt in enumerate(prompts):
            metadata = cluster_meta.get(prompt["topic_cluster"], {
                "name": prompt["topic_cluster"],
                "topic_family": family_by_cluster.get(prompt["topic_cluster"], prompt["topic_cluster"]),
                "super_theme": theme_by_cluster.get(prompt["topic_cluster"], prompt["topic_cluster"]),
            })
            classification = cls.semantic_prompt_classification(prompt, metadata)
            effective_classifications.append({
                "prompt_index": index,
                "provider_topic_cluster": prompt["topic_cluster"],
                "provider_topic_family": metadata.get("topic_family") or metadata["name"],
                "provider_super_theme": grouped_theme_names.get(
                    metadata.get("super_theme") or metadata.get("topic_family") or metadata["name"],
                    metadata.get("super_theme") or metadata.get("topic_family") or metadata["name"],
                ),
                **classification,
            })
        topics = Counter(item["effective_micro_cluster"] for item in effective_classifications)
        families = Counter(item["effective_topic_family"] for item in effective_classifications)
        super_themes = Counter(item["effective_super_theme"] for item in effective_classifications)
        largest_share = max(topics.values(), default=0) / max(1, len(prompts))
        largest_family_share = max(families.values(), default=0) / max(1, len(prompts))
        largest_super_theme_share = max(super_themes.values(), default=0) / max(1, len(prompts))
        target_terms = set((core_category or {}).get("target_terms", []))
        normalized_target_terms = {
            cls.normalize_text(value) for value in target_terms if value
        }
        unbranded = [
            item for item in prompts
            if not any(term and term in cls.normalize_text(item["text"])
                       for term in normalized_target_terms)
        ]
        core_family = (core_category or {}).get("topic_family")
        raw_core_super_theme = (core_category or {}).get("super_theme") or core_family
        core_super_theme = grouped_theme_names.get(raw_core_super_theme, raw_core_super_theme)
        represented_families = set(provider_families)
        represented_super_themes = set(provider_super_themes)
        major_families = {
            item.get("topic_family")
            for item in (topic_clusters or [])
            if item.get("is_major_family") and item.get("topic_family")
        }
        major_super_themes = {
            grouped_theme_names.get(
                item.get("super_theme") or item.get("topic_family"),
                item.get("super_theme") or item.get("topic_family"),
            )
            for item in (topic_clusters or [])
            if (item.get("is_major_super_theme", item.get("is_major_family"))
                and (item.get("super_theme") or item.get("topic_family")))
        }
        checklist = {
            "core_category": bool(
                core_category and core_family in represented_families
                and core_super_theme in represented_super_themes
            ),
            "major_super_themes": bool(major_super_themes) and major_super_themes <= represented_super_themes,
            "major_product_families": bool(major_families) and major_families <= represented_families,
            "general_brand_discovery": intents.get("brand", 0) > 0,
            "unbranded_recommendation": any(
                item["category"] == "recommendation" for item in unbranded
            ),
            "alternatives_comparison": intents.get("comparison", 0) > 0,
            "commercial_evaluation": intents.get("commercial", 0) > 0,
        }
        warnings = []
        if scope == "brand_wide" and largest_share > cls.MAX_TOPIC_SHARE:
            warnings.append("One topic cluster exceeds the 35% brand-wide concentration guard.")
        if scope == "brand_wide" and largest_family_share > cls.MAX_FAMILY_SHARE:
            dominant_family, dominant_count = families.most_common(1)[0]
            warnings.append(
                f"{dominant_family} represents {dominant_count / len(prompts):.0%} of this "
                "brand-wide proposal, above SearchIntel's 40% topic-family guard."
            )
        if scope == "brand_wide" and largest_super_theme_share > cls.MAX_SUPER_THEME_SHARE:
            dominant_theme, dominant_count = super_themes.most_common(1)[0]
            justified = any(
                cls.semantic_theme_signature(item.get("super_theme") or "")
                == cls.semantic_theme_signature(dominant_theme)
                and item.get("dominance_justified")
                for item in (topic_clusters or [])
            ) and (core_category or {}).get("market_structure") == "single_theme"
            if not justified:
                warnings.append(
                    f"{dominant_theme} represents {dominant_count / len(prompts):.0%} of this "
                    "brand-wide proposal, above SearchIntel's 45% super-theme guard."
                )
        missing = sorted(cls.REQUIRED_INTENTS - set(intents))
        if missing:
            warnings.append("Missing major intent categories: " + ", ".join(missing) + ".")
        if scope == "brand_wide":
            missing_checks = [name.replace("_", " ") for name, passed in checklist.items() if not passed]
            if missing_checks:
                warnings.append("Brand-wide coverage needs review: " + ", ".join(missing_checks) + ".")
        status = "focused" if scope == "focused" else ("needs_review" if warnings else "balanced")
        core_category = dict(core_category or {}) or None
        if core_category:
            strategic = core_category.get("strategic_emphasis") or {
                "name": core_category.get("name"), "evidence": core_category.get("evidence", []),
            }
            durable = core_category.get("core_brand_market")
            if not durable:
                emphasis_signature = cls.semantic_theme_signature(
                    core_category.get("super_theme") or core_category.get("topic_family") or ""
                )
                candidate_family = next((
                    name for name, _count in provider_families.most_common()
                    if cls.semantic_theme_signature(name) != emphasis_signature
                ), core_category.get("name"))
                candidate_evidence = [
                    value for item in (topic_clusters or [])
                    if item.get("topic_family") == candidate_family
                    for value in item.get("evidence", [])
                ][:4]
                durable = {"name": candidate_family, "evidence": candidate_evidence}
            core_category["core_brand_market"] = durable
            core_category["strategic_emphasis"] = strategic
        return {
            "topic_distribution": dict(topics),
            "topic_family_distribution": dict(families),
            "super_theme_distribution": dict(super_themes),
            "provider_topic_distribution": dict(provider_topics),
            "provider_topic_family_distribution": dict(provider_families),
            "provider_super_theme_distribution": dict(provider_super_themes),
            "effective_classifications": effective_classifications,
            "intent_distribution": dict(intents),
            "largest_topic_share": round(largest_share, 4),
            "largest_topic_family_share": round(largest_family_share, 4),
            "largest_super_theme_share": round(largest_super_theme_share, 4),
            "concentration_status": status,
            "core_category": core_category,
            "crawl_sample_bias": crawl_sample_bias or {"detected": False, "reason": None, "evidence": []},
            "brand_wide_checklist": checklist,
        }, warnings

    @classmethod
    def build_repair_brief(
        cls,
        prompts: list[dict],
        topic_clusters: list[dict],
        blueprint: dict,
        warnings: list[str],
    ) -> dict | None:
        if blueprint.get("concentration_status") != "needs_review":
            return None
        distributions = blueprint.get("super_theme_distribution", {})
        dominant_theme, dominant_count = max(distributions.items(), key=lambda item: item[1], default=(None, 0))
        missing_intents = sorted(cls.REQUIRED_INTENTS - set(blueprint.get("intent_distribution", {})))
        missing_checks = sorted(
            name for name, passed in blueprint.get("brand_wide_checklist", {}).items() if not passed
        )
        over_limit = bool(dominant_theme and blueprint.get("largest_super_theme_share", 0) > cls.MAX_SUPER_THEME_SHARE)
        if not over_limit and not missing_intents and not missing_checks:
            return None

        cluster_meta = {item["name"]: item for item in topic_clusters}
        dominant_indices = {
            item["prompt_index"] for item in blueprint.get("effective_classifications", [])
            if item["effective_super_theme"] == dominant_theme
        }
        allowed_count = math.floor(len(prompts) * cls.MAX_SUPER_THEME_SHARE)
        replacement_count = max(0, dominant_count - allowed_count) if over_limit else 0
        dominant_family_count = max(blueprint.get("topic_family_distribution", {}).values(), default=0)
        dominant_topic_count = max(blueprint.get("topic_distribution", {}).values(), default=0)
        replacement_count = max(
            replacement_count,
            max(0, dominant_family_count - math.floor(len(prompts) * cls.MAX_FAMILY_SHARE)),
            max(0, dominant_topic_count - math.floor(len(prompts) * cls.MAX_TOPIC_SHARE)),
        )
        replacement_count = min(len(prompts), max(replacement_count, len(missing_intents), len(missing_checks)))

        combo_counts = Counter((item["topic_cluster"], item["category"]) for item in prompts)
        cluster_counts = Counter(item["topic_cluster"] for item in prompts)
        core = blueprint.get("core_category") or {}
        core_family = core.get("topic_family")
        preserve_intents = {"brand", "recommendation", "comparison", "commercial"}

        candidates = []
        for index, item in enumerate(prompts):
            meta = cluster_meta.get(item["topic_cluster"], {})
            in_dominant = index in dominant_indices
            replace_score = 0
            replace_score += 100 if in_dominant else 0
            replace_score += 20 if combo_counts[(item["topic_cluster"], item["category"])] > 1 else 0
            replace_score += 10 if cluster_counts[item["topic_cluster"]] > 1 else 0
            replace_score -= 40 if meta.get("topic_family") == core_family else 0
            replace_score -= 25 if item["category"] in preserve_intents else 0
            candidates.append((replace_score, index, item))
        selected = sorted(candidates, key=lambda entry: (-entry[0], -entry[1]))[:replacement_count]
        replace_indices = {index for _score, index, _item in selected}
        retained = [item for index, item in enumerate(prompts) if index not in replace_indices]
        replaced = [item for index, item in enumerate(prompts) if index in replace_indices]
        underrepresented = [
            {"name": name, "count": count, "share": round(count / max(1, len(prompts)), 4)}
            for name, count in sorted(distributions.items(), key=lambda item: (item[1], item[0]))
            if name != dominant_theme
        ]
        return {
            "reason": "; ".join(warnings),
            "overrepresented_themes": ([{
                "name": dominant_theme,
                "count": dominant_count,
                "share": round(dominant_count / max(1, len(prompts)), 4),
                "limit": cls.MAX_SUPER_THEME_SHARE,
            }] if over_limit else []),
            "underrepresented_themes": underrepresented,
            "missing_intents": missing_intents,
            "missing_checklist_items": missing_checks,
            "retained_prompts": retained,
            "replacement_candidates": replaced,
            "retained_count": len(retained),
            "replacement_count": len(replaced),
        }

    @classmethod
    def _serialize(cls, proposal: PromptSetProposal, context: dict | None = None) -> dict:
        context = context or {}
        clusters = [
            {
                **item,
                "topic_family": item.get("topic_family") or item["name"],
                "super_theme": item.get("super_theme") or item.get("topic_family") or item["name"],
                "is_major_family": bool(item.get("is_major_family", True)),
                "is_major_super_theme": bool(item.get("is_major_super_theme", True)),
                "dominance_justified": bool(item.get("dominance_justified", False)),
            }
            for item in proposal.topic_clusters
        ]
        blueprint = dict(proposal.coverage_blueprint)
        if "topic_family_distribution" not in blueprint:
            blueprint["topic_family_distribution"] = dict(blueprint.get("topic_distribution", {}))
        blueprint.setdefault("largest_topic_family_share", blueprint.get("largest_topic_share", 0))
        blueprint.setdefault("super_theme_distribution", dict(blueprint.get("topic_family_distribution", {})))
        blueprint.setdefault("largest_super_theme_share", blueprint.get("largest_topic_family_share", 0))
        blueprint.setdefault("core_category", None)
        blueprint.setdefault("brand_wide_checklist", {})
        blueprint.setdefault("crawl_sample_bias", {"detected": False, "reason": None, "evidence": []})
        warnings = list(proposal.warnings)
        if proposal.generator_version in {
            cls.GENERATOR_VERSION, "automatic-rebalance-v5", "market-anchor-v4",
        }:
            automatic_rebalance = blueprint.get("automatic_rebalance")
            semantic_reevaluation = blueprint.get("semantic_reevaluation")
            blueprint, computed_warnings = cls.coverage(
                proposal.prompts,
                proposal.measurement_scope,
                clusters,
                blueprint.get("core_category"),
                blueprint.get("crawl_sample_bias"),
            )
            if automatic_rebalance:
                blueprint["automatic_rebalance"] = automatic_rebalance
            if semantic_reevaluation:
                blueprint["semantic_reevaluation"] = semantic_reevaluation
            warnings = list(dict.fromkeys([*warnings, *computed_warnings]))
        return {
            "id": proposal.id, "project_id": proposal.project_id, "status": proposal.status,
            "generator_version": proposal.generator_version,
            "measurement_scope": proposal.measurement_scope, "focus_label": proposal.focus_label,
            "model_id": context.get("model_id"), "model_name": proposal.model_name,
            "provider_model_id": context.get("provider_model_id"),
            "target_brand": context.get("target_brand", ""),
            "website_pages_used": proposal.source_page_count,
            "competitors_used": context.get("competitors_used", []),
            "existing_prompts_considered": context.get("existing_prompts_considered", 0),
            "requested_count": len(proposal.prompts), "generated_count": len(proposal.prompts),
            "topic_clusters": clusters,
            "coverage_blueprint": blueprint,
            "warnings": warnings, "prompts": proposal.prompts,
            "created_at": proposal.created_at,
        }

    @classmethod
    def latest(cls, db: Session, project_id: int) -> dict | None:
        project = ProjectRepository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        proposal = db.scalar(select(PromptSetProposal).where(
            PromptSetProposal.project_id == project_id
        ).order_by(PromptSetProposal.created_at.desc(), PromptSetProposal.id.desc()))
        return cls._serialize(proposal) if proposal else None

    @classmethod
    def reevaluate_and_repair(
        cls, db: Session, project_id: int, proposal_id: int, model_id: int | None = None,
    ) -> dict:
        project = ProjectRepository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        proposal = db.scalar(select(PromptSetProposal).where(
            PromptSetProposal.id == proposal_id,
            PromptSetProposal.project_id == project_id,
        ))
        if proposal is None or proposal.status != "proposed":
            raise HTTPException(status_code=404, detail="Inactive prompt proposal not found.")
        original_blueprint = dict(proposal.coverage_blueprint)
        core = original_blueprint.get("core_category")
        bias = original_blueprint.get("crawl_sample_bias")
        blueprint, warnings = cls.coverage(
            proposal.prompts, proposal.measurement_scope, proposal.topic_clusters, core, bias
        )
        reclassified = [item for item in blueprint["effective_classifications"] if item["reclassified"]]
        semantic_provenance = {
            "provider_super_theme_distribution": original_blueprint.get(
                "provider_super_theme_distribution", original_blueprint.get("super_theme_distribution", {})
            ),
            "effective_super_theme_distribution": blueprint["super_theme_distribution"],
            "reclassified_prompt_indices": [item["prompt_index"] for item in reclassified],
        }
        brief = (
            cls.build_repair_brief(proposal.prompts, proposal.topic_clusters, blueprint, warnings)
            if proposal.measurement_scope == "brand_wide" else None
        )
        initial_validation = {
            "coverage_status": blueprint["concentration_status"],
            "largest_topic_share": blueprint["largest_topic_share"],
            "largest_topic_family_share": blueprint["largest_topic_family_share"],
            "largest_super_theme_share": blueprint["largest_super_theme_share"],
            "warnings": list(warnings),
        }
        rebalance = {
            "triggered": bool(brief), "status": "not_needed" if not brief else "failed",
            "generator_version": cls.REPAIR_GENERATOR_VERSION,
            "initial_validation": initial_validation,
            "reason": brief["reason"] if brief else None,
            "overrepresented_themes": brief["overrepresented_themes"] if brief else [],
            "underrepresented_themes": brief["underrepresented_themes"] if brief else [],
            "retained_count": brief["retained_count"] if brief else len(proposal.prompts),
            "replaced_count": 0, "final_validation": initial_validation,
        }
        if brief:
            roles = ProjectBrandRepository.list_brand_roles(db, project_id)
            targets = [brand for brand, role in roles if role == "target"]
            if len(targets) != 1:
                raise HTTPException(status_code=400, detail="Project must have one target brand.")
            target = targets[0]
            competitors = [brand for brand, role in roles if role == "competitor"]
            websites = WebsiteRepository.list_by_brand(db, target.id)
            website = next((item for item in websites if item.is_primary), websites[0] if websites else None)
            if website is None:
                raise HTTPException(status_code=400, detail="A target-brand website is required for semantic repair.")
            pages = [page for page in PageRepository.list_by_website(db, website.id) if (page.content_text or "").strip()]
            if not pages:
                raise HTTPException(status_code=400, detail="Usable first-party crawl evidence is required for semantic repair.")
            terms = cls.evidence_terms(pages)
            deterministic_bias = cls.crawl_sample_bias_signal(pages)
            excerpts = [
                f"URL: {page.url}\nTitle: {page.title or ''}\nH1: {page.h1 or ''}\nExcerpt: {(page.content_text or '')[:1000]}"
                for page in pages[:20]
            ]
            model = AIModelService.resolve_execution_model(db, model_id)
            engine = AIEngineRepository.get_by_id(db, model.engine_id)
            if engine is None:
                raise HTTPException(status_code=500, detail="AI model engine could not be resolved.")
            repair_prompt = f"""Repair this existing inactive brand-wide prompt proposal from its semantic coverage brief.
TARGET: {target.name}
APPROVED COMPETITORS: {', '.join(item.name for item in competitors) or '(none)'}
CORE MARKET CONTEXT: {json.dumps(blueprint.get('core_category'))}
SEMANTIC REPAIR BRIEF: {json.dumps(brief)}

Preserve every retained prompt verbatim. Replace only the listed candidates with genuinely broader evidence-backed prompt texts. Do not repair by relabelling prompts. Keep exactly {len(proposal.prompts)} prompts and all required intents. Do not rename or split semantic themes to evade existing guards.

Return JSON only with exactly this shape:
{{"core_category":{{"name":"...","topic_family":"exact family name","super_theme":"exact super-theme name","market_structure":"multi_theme","evidence":["exact supplied term or URL"],"weighting_note":"...","core_brand_market":{{"name":"...","evidence":["exact supplied term or URL"]}},"strategic_emphasis":{{"name":"...","evidence":["exact supplied term or URL"]}}}},"crawl_sample_bias":{{"detected":false,"reason":"...","evidence":["exact supplied term or URL"]}},"super_themes":[{{"name":"...","evidence":["exact supplied term or URL"],"is_major":true,"dominance_justified":false}}],"topic_families":[{{"name":"...","super_theme":"exact super-theme name","evidence":["exact supplied term or URL"],"is_major":true}}],"topic_clusters":[{{"name":"...","topic_family":"exact family name","evidence":["exact supplied term or URL"],"allocated_prompts":3}}],"prompts":[{{"text":"...","category":"comparison","topic_cluster":"exact cluster name","rationale":"..."}}]}}

Every item must use evidence terms or URLs from the supplied evidence.

FIRST-PARTY EVIDENCE:
{chr(10).join(excerpts)}"""
            try:
                result = ProviderFactory.create(engine.slug).execute(
                    prompt=repair_prompt, model_id=model.provider_model_id, mode="memory"
                )
                payload = cls.extract_json(result.response_text)
                repaired_core, repaired_bias, repaired_clusters, repaired_prompts = cls._validate_provider_payload(
                    payload, pages, terms, target.name, len(proposal.prompts), deterministic_bias
                )
                retained_texts = {item["text"] for item in brief["retained_prompts"]}
                if not retained_texts <= {item["text"] for item in repaired_prompts}:
                    raise ValueError("required retained prompts were changed")
                final_blueprint, final_warnings = cls.coverage(
                    repaired_prompts, proposal.measurement_scope, repaired_clusters,
                    repaired_core, repaired_bias,
                )
                proposal.prompts = repaired_prompts
                proposal.topic_clusters = repaired_clusters
                blueprint, warnings = final_blueprint, final_warnings
                rebalance.update({
                    "status": "completed", "retained_count": len(retained_texts),
                    "replaced_count": len(repaired_prompts) - len(retained_texts),
                    "final_validation": {
                        "coverage_status": blueprint["concentration_status"],
                        "largest_topic_share": blueprint["largest_topic_share"],
                        "largest_topic_family_share": blueprint["largest_topic_family_share"],
                        "largest_super_theme_share": blueprint["largest_super_theme_share"],
                        "warnings": list(warnings),
                    },
                })
            except Exception:
                warnings = list(dict.fromkeys([
                    *warnings,
                    "Semantic rebalancing could not produce a valid repair; review the existing proposal.",
                ]))
        blueprint["semantic_reevaluation"] = semantic_provenance
        blueprint["automatic_rebalance"] = rebalance
        proposal.generator_version = cls.GENERATOR_VERSION
        proposal.coverage_blueprint = blueprint
        proposal.warnings = warnings
        db.commit()
        db.refresh(proposal)
        return cls._serialize(proposal)

    @classmethod
    def _validate_provider_payload(
        cls, payload: dict, pages: list, terms: list[str], target_name: str,
        count: int, deterministic_bias: dict,
    ) -> tuple[dict, dict, list[dict], list[dict]]:
        raw_core_category = payload.get("core_category")
        raw_bias = payload.get("crawl_sample_bias")
        raw_super_themes = payload.get("super_themes")
        raw_families = payload.get("topic_families")
        raw_clusters = payload.get("topic_clusters")
        raw_prompts = payload.get("prompts")
        if (not isinstance(raw_core_category, dict) or not isinstance(raw_bias, dict)
                or not isinstance(raw_super_themes, list) or not isinstance(raw_families, list)
                or not isinstance(raw_clusters, list) or not isinstance(raw_prompts, list)):
            raise HTTPException(status_code=502, detail="Generator response omitted the coverage blueprint.")
        evidence_blob = " ".join(terms + [page.url.lower() for page in pages])

        def grounded(values: list) -> bool:
            return bool(values) and any(str(value).strip().lower() in evidence_blob for value in values)

        super_theme_names = set()
        super_themes = []
        for item in raw_super_themes:
            name = str(item.get("name", "")).strip()
            evidence = [str(value).strip() for value in item.get("evidence", []) if str(value).strip()]
            if not name or not grounded(evidence):
                continue
            super_theme_names.add(name)
            super_themes.append({
                "name": name, "evidence": evidence[:4], "is_major": bool(item.get("is_major")),
                "dominance_justified": bool(item.get("dominance_justified")),
            })
        family_names = set()
        families = []
        for item in raw_families:
            name = str(item.get("name", "")).strip()
            super_theme = str(item.get("super_theme", "")).strip()
            evidence = [str(value).strip() for value in item.get("evidence", []) if str(value).strip()]
            if not name or super_theme not in super_theme_names or not grounded(evidence):
                continue
            family_names.add(name)
            families.append({"name": name, "super_theme": super_theme,
                             "evidence": evidence[:4], "is_major": bool(item.get("is_major"))})
        core_name = str(raw_core_category.get("name", "")).strip()
        core_family = str(raw_core_category.get("topic_family", "")).strip()
        core_super_theme = str(raw_core_category.get("super_theme", "")).strip()
        core_evidence = [str(value).strip() for value in raw_core_category.get("evidence", []) if str(value).strip()]
        if (not core_name or core_family not in family_names or core_super_theme not in super_theme_names
                or not grounded(core_evidence)):
            raise HTTPException(status_code=502, detail="Generator returned an ungrounded core market category.")
        core_category = {
            "name": core_name, "topic_family": core_family, "super_theme": core_super_theme,
            "evidence": core_evidence[:4],
            "market_structure": "single_theme" if raw_core_category.get("market_structure") == "single_theme" else "multi_theme",
            "weighting_note": str(raw_core_category.get("weighting_note", "")).strip() or None,
            "target_terms": [target_name],
        }
        raw_brand_market = raw_core_category.get("core_brand_market")
        if isinstance(raw_brand_market, dict):
            market_evidence = [str(value).strip() for value in raw_brand_market.get("evidence", []) if str(value).strip()]
            if str(raw_brand_market.get("name", "")).strip() and grounded(market_evidence):
                core_category["core_brand_market"] = {
                    "name": str(raw_brand_market["name"]).strip(), "evidence": market_evidence[:4],
                }
        raw_emphasis = raw_core_category.get("strategic_emphasis")
        if isinstance(raw_emphasis, dict):
            emphasis_evidence = [str(value).strip() for value in raw_emphasis.get("evidence", []) if str(value).strip()]
            if str(raw_emphasis.get("name", "")).strip() and grounded(emphasis_evidence):
                core_category["strategic_emphasis"] = {
                    "name": str(raw_emphasis["name"]).strip(), "evidence": emphasis_evidence[:4],
                }
        bias_evidence = [str(value).strip() for value in raw_bias.get("evidence", []) if str(value).strip()]
        bias_detected = deterministic_bias["detected"] or (bool(raw_bias.get("detected")) and grounded(bias_evidence))
        crawl_sample_bias = {
            "detected": bias_detected,
            "reason": deterministic_bias["reason"] if deterministic_bias["detected"] else str(raw_bias.get("reason", "")).strip() or None,
            "evidence": deterministic_bias["evidence"] if deterministic_bias["detected"] else bias_evidence[:4] if bias_detected else [],
        }
        clusters = []
        cluster_names = set()
        for item in raw_clusters:
            name = str(item.get("name", "")).strip()
            family = str(item.get("topic_family", "")).strip()
            evidence = [str(value).strip() for value in item.get("evidence", []) if str(value).strip()]
            if not name or family not in family_names or not grounded(evidence):
                continue
            cluster_names.add(name)
            family_meta = next(meta for meta in families if meta["name"] == family)
            theme_meta = next(meta for meta in super_themes if meta["name"] == family_meta["super_theme"])
            clusters.append({
                "name": name, "topic_family": family, "super_theme": family_meta["super_theme"],
                "evidence": evidence[:4], "is_major_family": family_meta["is_major"],
                "is_major_super_theme": theme_meta["is_major"],
                "dominance_justified": theme_meta["dominance_justified"], "allocated_prompts": 0,
            })
        output = []
        for item in raw_prompts:
            text = str(item.get("text", "")).strip()
            category = str(item.get("category", "")).strip().lower()
            topic = str(item.get("topic_cluster", "")).strip()
            if len(text) < 5 or category not in cls.VALID_CATEGORIES or topic not in cluster_names:
                continue
            if cls.is_near_duplicate(text, [entry["text"] for entry in output]):
                continue
            output.append({"text": text, "category": category, "topic_cluster": topic,
                           "rationale": str(item.get("rationale", "")).strip() or None})
            if len(output) == count:
                break
        if len(output) < max(8, count - 2):
            raise HTTPException(status_code=502, detail="Generator returned too few valid, grounded, unique prompts.")
        counts = Counter(item["topic_cluster"] for item in output)
        clusters = [{**item, "allocated_prompts": counts[item["name"]]} for item in clusters if counts[item["name"]]]
        return core_category, crawl_sample_bias, clusters, output

    @classmethod
    def generate(cls, db: Session, project_id: int, count: int, model_id: int | None = None,
                 measurement_scope: str = "brand_wide", focus_label: str | None = None) -> dict:
        project = ProjectRepository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        roles = ProjectBrandRepository.list_brand_roles(db, project_id)
        targets = [brand for brand, role in roles if role == "target"]
        if len(targets) != 1:
            raise HTTPException(status_code=400, detail="Project must have one target brand.")
        target = targets[0]
        competitors = [brand for brand, role in roles if role == "competitor"]
        websites = WebsiteRepository.list_by_brand(db, target.id)
        website = next((item for item in websites if item.is_primary), websites[0] if websites else None)
        if not website:
            raise HTTPException(status_code=400, detail="Target brand has no website.")
        pages = [page for page in PageRepository.list_by_website(db, website.id) if (page.content_text or "").strip()]
        if not pages:
            raise HTTPException(status_code=400, detail="Crawl the target website before generating prompts.")
        terms = cls.evidence_terms(pages)
        if len(terms) < 3:
            raise HTTPException(status_code=400, detail="Crawled pages contain too little topic evidence.")
        existing = PromptRepository.list_by_project(db, project_id)
        tiers = cls.evidence_tiers(pages)
        deterministic_bias = cls.crawl_sample_bias_signal(pages)
        excerpts = []
        tier_limits = {"homepage": 2, "top_level": 10, "broader_corpus": 8}
        for tier_name, tier_pages in tiers.items():
            excerpts.append(f"\n{tier_name.upper()} EVIDENCE (priority tier):")
            selected = sorted(
                tier_pages,
                key=lambda item: item.word_count or 0,
                reverse=True,
            )[:tier_limits[tier_name]]
            for page in selected:
                excerpts.append(
                    f"URL: {page.url}\nTitle: {page.title or ''}\nH1: {page.h1 or ''}"
                    f"\nExcerpt: {(page.content_text or '')[:1000]}"
                )
        scope_instruction = (
            "Anchor the proposal in the brand's broad primary market using homepage and top-level evidence before "
            "broader crawl frequency. Group related micro-clusters into topic families and related families into "
            "market-level super-themes. No cluster may exceed 35%, no family 40%, and no super-theme 45% unless "
            "the evidence establishes a genuinely single-theme company. Include company identity and realistic "
            "unbranded core-category discovery, recommendation, comparison, and commercial-evaluation questions."
            if measurement_scope == "brand_wide" else
            f"Concentrate on this approved focus: {focus_label}. Concentration is expected, but remain varied by intent."
        )
        provider_prompt = f"""Design a controlled AI-search prompt-set proposal.
TARGET: {target.name}
SCOPE: {measurement_scope}
APPROVED COMPETITORS: {', '.join(item.name for item in competitors) or '(none)'}
DETERMINISTIC EVIDENCE TERMS: {', '.join(terms)}
DETERMINISTIC CRAWL-SAMPLE BIAS SIGNAL: {json.dumps(deterministic_bias)}
{scope_instruction}

Return JSON only with exactly this shape:
{{"core_category":{{"name":"...","topic_family":"exact family name","super_theme":"exact super-theme name","market_structure":"multi_theme","evidence":["exact supplied term or URL"],"weighting_note":"..."}},"crawl_sample_bias":{{"detected":false,"reason":"...","evidence":["exact supplied term or URL"]}},"super_themes":[{{"name":"...","evidence":["exact supplied term or URL"],"is_major":true,"dominance_justified":false}}],"topic_families":[{{"name":"...","super_theme":"exact super-theme name","evidence":["exact supplied term or URL"],"is_major":true}}],"topic_clusters":[{{"name":"...","topic_family":"exact family name","evidence":["exact supplied term or URL"],"allocated_prompts":3}}],"prompts":[{{"text":"...","category":"comparison","topic_cluster":"exact cluster name","rationale":"..."}}]}}

Create exactly {count} realistic questions. Include at least one of every intent: brand, informational, problem_solution, recommendation, comparison, commercial. Commercial means a defensible buying, cost, operational-tradeoff, or vendor-evaluation question—not artificial sales language. At least 70% must be unbranded. Use only approved competitors. Avoid near-duplicates, keyword strings, benchmark language, unsupported claims, and these current prompts: {[item.text for item in existing]}.
Every anchor, theme, family, and cluster must be grounded by an exact evidence term or URL below. Related families must share a super-theme instead of being renamed to evade the super-theme guard. Homepage and top-level evidence outweigh repeated deep-page topics. Cluster allocations must equal prompt assignments.

FIRST-PARTY EVIDENCE:
{chr(10).join(excerpts)}"""
        model = AIModelService.resolve_execution_model(db, model_id)
        engine = AIEngineRepository.get_by_id(db, model.engine_id)
        if engine is None:
            raise HTTPException(status_code=500, detail="AI model engine could not be resolved.")
        try:
            result = ProviderFactory.create(engine.slug).execute(
                prompt=provider_prompt, model_id=model.provider_model_id, mode="memory"
            )
            payload = cls.extract_json(result.response_text)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"AI starter prompt generation failed: {exc}") from exc
        core_category, crawl_sample_bias, clusters, output = cls._validate_provider_payload(
            payload, pages, terms, target.name, count, deterministic_bias
        )
        blueprint, warnings = cls.coverage(
            output, measurement_scope, clusters, core_category, crawl_sample_bias
        )
        initial_validation = {
            "coverage_status": blueprint["concentration_status"],
            "largest_topic_share": blueprint["largest_topic_share"],
            "largest_topic_family_share": blueprint["largest_topic_family_share"],
            "largest_super_theme_share": blueprint["largest_super_theme_share"],
            "warnings": list(warnings),
        }
        repair_brief = (
            cls.build_repair_brief(output, clusters, blueprint, warnings)
            if measurement_scope == "brand_wide" else None
        )
        repair_provenance = {
            "triggered": False,
            "status": "not_needed",
            "generator_version": cls.REPAIR_GENERATOR_VERSION,
            "initial_validation": initial_validation,
            "reason": None,
            "overrepresented_themes": [],
            "underrepresented_themes": [],
            "retained_count": len(output),
            "replaced_count": 0,
            "final_validation": initial_validation,
        }
        if repair_brief:
            repair_prompt = f"""Repair an existing brand-wide AI-search prompt proposal using this structured brief.
TARGET: {target.name}
APPROVED COMPETITORS: {', '.join(item.name for item in competitors) or '(none)'}
CORE MARKET: {json.dumps(core_category)}
REPAIR BRIEF: {json.dumps(repair_brief)}

Preserve every retained prompt verbatim. Replace only the listed replacement candidates. Fill the documented evidence-backed deficits naturally. Keep exactly {count} prompts and all required intents. Keep the existing semantic theme meanings; do not rename or split related themes to evade the 35%, 40%, or 45% guards. Aim below, not exactly at, the 45% super-theme maximum. Use approved competitors only.

Return the same JSON shape as the initial generator:
{{"core_category":{{"name":"...","topic_family":"exact family name","super_theme":"exact super-theme name","market_structure":"multi_theme","evidence":["exact supplied term or URL"],"weighting_note":"..."}},"crawl_sample_bias":{{"detected":false,"reason":"...","evidence":["exact supplied term or URL"]}},"super_themes":[{{"name":"...","evidence":["exact supplied term or URL"],"is_major":true,"dominance_justified":false}}],"topic_families":[{{"name":"...","super_theme":"exact super-theme name","evidence":["exact supplied term or URL"],"is_major":true}}],"topic_clusters":[{{"name":"...","topic_family":"exact family name","evidence":["exact supplied term or URL"],"allocated_prompts":3}}],"prompts":[{{"text":"...","category":"comparison","topic_cluster":"exact cluster name","rationale":"..."}}]}}

FIRST-PARTY EVIDENCE:
{chr(10).join(excerpts)}"""
            repair_provenance = {
                **repair_provenance,
                "triggered": True,
                "status": "failed",
                "reason": repair_brief["reason"],
                "overrepresented_themes": repair_brief["overrepresented_themes"],
                "underrepresented_themes": repair_brief["underrepresented_themes"],
                "retained_count": repair_brief["retained_count"],
                "replaced_count": 0,
            }
            try:
                repair_result = ProviderFactory.create(engine.slug).execute(
                    prompt=repair_prompt, model_id=model.provider_model_id, mode="memory"
                )
                repaired_payload = cls.extract_json(repair_result.response_text)
                repaired_core, repaired_bias, repaired_clusters, repaired_output = cls._validate_provider_payload(
                    repaired_payload, pages, terms, target.name, count, deterministic_bias
                )
                retained_texts = {item["text"] for item in repair_brief["retained_prompts"]}
                repaired_texts = {item["text"] for item in repaired_output}
                if not retained_texts <= repaired_texts:
                    raise ValueError("required retained prompts were changed")
                core_category, crawl_sample_bias, clusters, output = (
                    repaired_core, repaired_bias, repaired_clusters, repaired_output
                )
                blueprint, warnings = cls.coverage(
                    output, measurement_scope, clusters, core_category, crawl_sample_bias
                )
                repair_provenance = {
                    **repair_provenance,
                    "status": "completed",
                    "retained_count": len(retained_texts),
                    "replaced_count": len(output) - len(retained_texts),
                    "final_validation": {
                        "coverage_status": blueprint["concentration_status"],
                        "largest_topic_share": blueprint["largest_topic_share"],
                        "largest_topic_family_share": blueprint["largest_topic_family_share"],
                        "largest_super_theme_share": blueprint["largest_super_theme_share"],
                        "warnings": list(warnings),
                    },
                }
            except Exception:
                warnings = list(dict.fromkeys([
                    *warnings,
                    "Automatic rebalancing could not produce a valid repair; review the initial proposal.",
                ]))
        blueprint["automatic_rebalance"] = repair_provenance
        project.measurement_scope = measurement_scope
        project.measurement_focus = focus_label.strip() if focus_label else None
        proposal = PromptSetProposal(
            project_id=project_id, generator_version=cls.GENERATOR_VERSION,
            measurement_scope=measurement_scope, focus_label=project.measurement_focus,
            source_website_id=website.id, source_page_count=len(pages), model_name=model.name,
            topic_clusters=clusters, coverage_blueprint=blueprint, prompts=output, warnings=warnings,
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return cls._serialize(proposal, {
            "model_id": model.id, "provider_model_id": model.provider_model_id,
            "target_brand": target.name, "competitors_used": [item.name for item in competitors],
            "existing_prompts_considered": len(existing),
        })
