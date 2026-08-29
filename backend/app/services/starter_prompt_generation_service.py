import json
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
    GENERATOR_VERSION = "balanced-v2"
    REQUIRED_INTENTS = {"brand", "informational", "problem_solution", "recommendation", "comparison", "commercial"}
    VALID_CATEGORIES = REQUIRED_INTENTS | {"navigational", "transactional"}
    STOP_WORDS = {
        "about", "with", "from", "your", "this", "that", "have", "more", "page",
        "home", "official", "platform", "solutions", "product", "products", "learn",
        "resources", "documentation", "developers", "company", "using", "build",
    }

    @staticmethod
    def normalize_text(value: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", value.strip().lower()))

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
    def coverage(cls, prompts: list[dict], scope: str) -> tuple[dict, list[str]]:
        topics = Counter(item["topic_cluster"] for item in prompts)
        intents = Counter(item["category"] for item in prompts)
        largest_share = max(topics.values(), default=0) / max(1, len(prompts))
        warnings = []
        if scope == "brand_wide" and largest_share > 0.35:
            warnings.append("One topic cluster exceeds the 35% brand-wide concentration guard.")
        missing = sorted(cls.REQUIRED_INTENTS - set(intents))
        if missing:
            warnings.append("Missing major intent categories: " + ", ".join(missing) + ".")
        status = "focused" if scope == "focused" else ("needs_review" if warnings else "balanced")
        return {
            "topic_distribution": dict(topics),
            "intent_distribution": dict(intents),
            "largest_topic_share": round(largest_share, 4),
            "concentration_status": status,
        }, warnings

    @classmethod
    def _serialize(cls, proposal: PromptSetProposal, context: dict | None = None) -> dict:
        context = context or {}
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
            "topic_clusters": proposal.topic_clusters,
            "coverage_blueprint": proposal.coverage_blueprint,
            "warnings": proposal.warnings, "prompts": proposal.prompts,
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
        excerpts = []
        for page in sorted(pages, key=lambda item: item.word_count or 0, reverse=True)[:12]:
            excerpts.append(f"URL: {page.url}\nTitle: {page.title or ''}\nH1: {page.h1 or ''}\nExcerpt: {(page.content_text or '')[:1200]}")
        scope_instruction = (
            "Cover the brand broadly across distinct first-party product/topic clusters. No cluster may receive more than 35% of prompts."
            if measurement_scope == "brand_wide" else
            f"Concentrate on this approved focus: {focus_label}. Concentration is expected, but remain varied by intent."
        )
        provider_prompt = f"""Design a controlled AI-search prompt-set proposal.
TARGET: {target.name}
SCOPE: {measurement_scope}
APPROVED COMPETITORS: {', '.join(item.name for item in competitors) or '(none)'}
DETERMINISTIC EVIDENCE TERMS: {', '.join(terms)}
{scope_instruction}

Return JSON only with exactly this shape:
{{"topic_clusters":[{{"name":"...","evidence":["exact supplied term or URL"],"allocated_prompts":3}}],"prompts":[{{"text":"...","category":"comparison","topic_cluster":"exact cluster name","rationale":"..."}}]}}

Create exactly {count} realistic questions. Use at least these intents: brand, informational, problem_solution, recommendation, comparison, commercial. At least 70% must be unbranded. Use only approved competitors. Avoid near-duplicates, keyword strings, benchmark language, unsupported claims, and these current prompts: {[item.text for item in existing]}.
Every cluster must be grounded by an exact evidence term or URL below. Cluster allocations must equal prompt assignments.

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
        raw_clusters = payload.get("topic_clusters")
        raw_prompts = payload.get("prompts")
        if not isinstance(raw_clusters, list) or not isinstance(raw_prompts, list):
            raise HTTPException(status_code=502, detail="Generator response omitted the coverage blueprint.")
        evidence_blob = " ".join(terms + [page.url.lower() for page in pages])
        clusters = []
        cluster_names = set()
        for item in raw_clusters:
            name = str(item.get("name", "")).strip()
            evidence = [str(value).strip() for value in item.get("evidence", []) if str(value).strip()]
            if not name or not evidence or not any(value.lower() in evidence_blob for value in evidence):
                continue
            cluster_names.add(name)
            clusters.append({"name": name, "evidence": evidence[:4], "allocated_prompts": 0})
        output: list[dict] = []
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
        blueprint, warnings = cls.coverage(output, measurement_scope)
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
