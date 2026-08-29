import hashlib
import json
import re
from types import SimpleNamespace
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.ai.provider_factory import ProviderFactory
from app.models.competitor_discovery_suggestion import CompetitorDiscoverySuggestion
from app.repositories.ai_engine_repository import AIEngineRepository
from app.repositories.competitor_discovery_repository import CompetitorDiscoveryRepository
from app.repositories.page_repository import PageRepository
from app.repositories.project_brand_repository import ProjectBrandRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.website_repository import WebsiteRepository
from app.services.ai_model_service import AIModelService
from app.services.brand_service import BrandService
from app.services.project_competitor_service import ProjectCompetitorService
from app.services.website_service import WebsiteService


class CompetitorDiscoveryService:
    TYPES = {"direct", "adjacent", "alternative"}
    CONFIDENCES = {"high", "medium", "low"}

    @staticmethod
    def _extract_json(response_text: str) -> dict:
        text = response_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise HTTPException(status_code=502, detail="Competitor discovery returned invalid structured data.")
            try:
                value = json.loads(text[start:end + 1])
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=502, detail="Competitor discovery returned malformed structured data.") from exc
        if not isinstance(value, dict):
            raise HTTPException(status_code=502, detail="Competitor discovery returned an unexpected response.")
        return value

    @staticmethod
    def _domain(website_url: str) -> str | None:
        parsed = urlparse(website_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        domain = parsed.hostname.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if "." not in domain:
            return None
        return domain

    @staticmethod
    def _read(item) -> dict:
        return {
            "id": item.id,
            "project_id": item.project_id,
            "brand_name": item.brand_name,
            "website_url": item.website_url,
            "domain": item.normalized_domain,
            "competitor_type": item.competitor_type,
            "confidence": item.confidence,
            "reason": item.reason,
            "evidence": item.evidence or [],
            "status": item.status,
            "model_name": item.model_name,
            "approved_brand_id": item.approved_brand_id,
        }

    @classmethod
    def list(cls, db: Session, project_id: int) -> list[dict]:
        if ProjectRepository.get_by_id(db, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        return [cls._read(item) for item in CompetitorDiscoveryRepository.list_by_project(db, project_id)]

    @classmethod
    def generate(cls, db: Session, project_id: int, max_candidates: int, model_id: int | None = None) -> dict:
        project = ProjectRepository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        brand_roles = ProjectBrandRepository.list_brand_roles(db, project_id)
        targets = [brand for brand, role in brand_roles if role == "target"]
        if len(targets) != 1:
            raise HTTPException(status_code=400, detail="Confirm one unambiguous target brand before discovery.")
        target = targets[0]
        configured = [brand for brand, role in brand_roles if role == "competitor"]
        websites = WebsiteRepository.list_by_brand(db, target.id)
        website = next((item for item in websites if item.is_primary), websites[0] if websites else None)
        if website is None:
            raise HTTPException(status_code=400, detail="Confirm a primary first-party website before discovery.")
        pages = PageRepository.list_by_website(db, website.id)
        excerpts = []
        for page in sorted(pages, key=lambda item: item.word_count or 0, reverse=True):
            content = (page.content_text or "").strip()
            if content:
                excerpts.append(f"URL: {page.url}\nTitle: {page.title or ''}\nExcerpt: {content[:1800]}")
            if len(excerpts) >= 6:
                break
        if not excerpts:
            raise HTTPException(status_code=400, detail="The stored crawl has no usable first-party evidence for discovery.")
        configured_names = [brand.name for brand in configured]
        fingerprint_source = json.dumps({
            "target": BrandService.normalize_name(target.name),
            "domain": website.domain.lower(),
            "competitors": sorted(BrandService.normalize_name(name) for name in configured_names),
            "pages": [(page.url, page.content_hash) for page in pages],
        }, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_source.encode()).hexdigest()
        prompt = f"""
You are performing controlled competitor discovery for agency onboarding. Use web research and the supplied first-party evidence to identify at most {max_candidates} defensible comparison brands.

TARGET BRAND: {target.name}
OFFICIAL DOMAIN: {website.domain}
ALREADY CONFIGURED COMPETITORS: {', '.join(configured_names) or '(none)'}

FIRST-PARTY EVIDENCE:
{chr(10).join(excerpts)}

Return JSON only:
{{"candidates":[{{"brand_name":"...","website_url":"https://official-domain.example","competitor_type":"direct|adjacent|alternative","confidence":"high|medium|low","reason":"concise market-overlap reason","evidence":[{{"url":"https://public-source.example/page","support":"what this source supports"}}]}}]}}

Rules:
- Prefer fewer strong candidates over weak famous brands.
- Use direct only for meaningful product/category substitution; adjacent and alternative must be explicit.
- Every candidate needs at least one public supporting URL and a specific support statement.
- Do not suggest the target, configured competitors, aliases, or duplicate domains.
- The website_url must be the candidate's plausible official domain.
- Do not claim market leadership, ownership, or relationships without evidence.
- This is onboarding research, not a benchmark or visibility measurement.
""".strip()
        model = AIModelService.resolve_execution_model(db, model_id)
        engine = AIEngineRepository.get_by_id(db, model.engine_id)
        if engine is None:
            raise HTTPException(status_code=500, detail="AI model engine could not be resolved.")
        try:
            result = ProviderFactory.create(engine.slug).execute(
                prompt=prompt,
                model_id=model.provider_model_id,
                mode="web_search",
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail="AI competitor discovery failed without creating suggestions.") from exc
        raw_candidates = cls._extract_json(result.response_text).get("candidates")
        if not isinstance(raw_candidates, list):
            raise HTTPException(status_code=502, detail="Competitor discovery returned no candidate list.")
        blocked_names = {BrandService.normalize_name(target.name), *(BrandService.normalize_name(name) for name in configured_names)}
        blocked_domains = {item.domain.lower() for item in websites}
        for brand in configured:
            blocked_domains.update(item.domain.lower() for item in WebsiteRepository.list_by_brand(db, brand.id))
        output = []
        seen_domains = set()
        try:
            for raw in raw_candidates:
                if not isinstance(raw, dict):
                    continue
                brand_name = re.sub(r"\s+", " ", str(raw.get("brand_name", "")).strip())[:255]
                normalized_name = BrandService.normalize_name(brand_name)
                website_url = str(raw.get("website_url", "")).strip()[:2048]
                domain = cls._domain(website_url)
                competitor_type = str(raw.get("competitor_type", "")).lower()
                confidence = str(raw.get("confidence", "")).lower()
                reason = re.sub(r"\s+", " ", str(raw.get("reason", "")).strip())[:1200]
                identity_match = (
                    ProjectBrandRepository.find_identity_match(
                        db,
                        project_id,
                        normalized_name,
                    )
                    if normalized_name
                    else None
                )
                if not brand_name or normalized_name in blocked_names or identity_match is not None or not domain or domain in blocked_domains or domain in seen_domains:
                    continue
                if competitor_type not in cls.TYPES or confidence not in cls.CONFIDENCES or not reason:
                    continue
                evidence = []
                for evidence_item in raw.get("evidence", [])[:5] if isinstance(raw.get("evidence"), list) else []:
                    if not isinstance(evidence_item, dict):
                        continue
                    url = str(evidence_item.get("url", "")).strip()[:2048]
                    support = re.sub(r"\s+", " ", str(evidence_item.get("support", "")).strip())[:1000]
                    if cls._domain(url) and support:
                        evidence.append({"url": url, "support": support})
                if not evidence:
                    continue
                existing = CompetitorDiscoveryRepository.get_by_domain(db, project_id, domain)
                if existing and (existing.status == "approved" or (existing.status == "ignored" and existing.evidence_fingerprint == fingerprint)):
                    continue
                if existing is None:
                    existing = CompetitorDiscoverySuggestion(project_id=project_id, normalized_domain=domain)
                    db.add(existing)
                existing.brand_name = brand_name
                existing.normalized_name = normalized_name
                existing.website_url = website_url
                existing.competitor_type = competitor_type
                existing.confidence = confidence
                existing.reason = reason
                existing.evidence = evidence
                existing.evidence_fingerprint = fingerprint
                existing.status = "pending"
                existing.model_name = model.name
                existing.approved_brand_id = None
                db.flush()
                output.append(existing)
                seen_domains.add(domain)
                if len(output) >= max_candidates:
                    break
            db.commit()
            for item in output:
                db.refresh(item)
        except Exception:
            db.rollback()
            raise
        return {
            "project_id": project_id,
            "target_brand": target.name,
            "method": "AI + controlled web research",
            "max_candidates": max_candidates,
            "generated_count": len(output),
            "suggestions": [cls._read(item) for item in output],
        }

    @classmethod
    def ignore(cls, db: Session, project_id: int, suggestion_id: int) -> dict:
        suggestion = CompetitorDiscoveryRepository.get(db, project_id, suggestion_id)
        if suggestion is None:
            raise HTTPException(status_code=404, detail="Competitor suggestion not found.")
        if suggestion.status == "approved":
            raise HTTPException(status_code=409, detail="Approved competitors cannot be ignored.")
        suggestion.status = "ignored"
        db.commit()
        db.refresh(suggestion)
        return {"suggestion": cls._read(suggestion), "competitor": None}

    @classmethod
    def approve(cls, db: Session, project_id: int, suggestion_id: int) -> dict:
        suggestion = CompetitorDiscoveryRepository.get(db, project_id, suggestion_id)
        if suggestion is None:
            raise HTTPException(status_code=404, detail="Competitor suggestion not found.")
        if suggestion.status != "pending":
            raise HTTPException(status_code=409, detail="Only pending suggestions can be approved.")
        data = SimpleNamespace(name=suggestion.brand_name, website_url=suggestion.website_url)
        try:
            competitor = ProjectCompetitorService.add(
                db, project_id, data, commit=False
            )
            suggestion.status = "approved"
            suggestion.approved_brand_id = competitor["brand_id"]
            db.commit()
            db.refresh(suggestion)
        except Exception:
            db.rollback()
            raise
        return {"suggestion": cls._read(suggestion), "competitor": competitor}
