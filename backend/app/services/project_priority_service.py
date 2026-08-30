import hashlib
import json
import re
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark_job import BenchmarkJob
from app.models.geo_prompt_opportunity import GeoPromptOpportunity
from app.models.project_priority import ProjectPriority
from app.models.site_rag_gap import SiteRAGGap
from app.repositories.project_priority_repository import ProjectPriorityRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.site_rag_gap_analysis_repository import SiteRAGGapAnalysisRepository
from app.services.project_readiness_service import ProjectReadinessService
from app.services.technical_seo_summary_service import TechnicalSEOSummaryService


class ProjectPriorityService:
    """Deterministically reconcile stored evidence into an agency work queue."""

    VALID_STATUSES = {
        "open", "in_progress", "implemented", "ready_to_recheck",
        "rechecked_improved", "rechecked_unchanged", "rechecked_worsened",
    }
    STOP_WORDS = {
        "a", "an", "and", "are", "best", "for", "how", "in", "is", "of",
        "on", "or", "the", "to", "what", "which", "with", "vs", "versus",
    }

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        normalized = set()
        for token in re.findall(r"[a-z0-9]+", value.lower()):
            if len(token) <= 2 or token in cls.STOP_WORDS:
                continue
            if token.endswith("ing") and len(token) > 6:
                token = token[:-3]
            elif token.endswith("s") and len(token) > 4:
                token = token[:-1]
            normalized.add(token)
        return normalized

    @classmethod
    def _topic_key(cls, prompts: list[str], fallback: str) -> str:
        tokens: dict[str, int] = {}
        for prompt in prompts:
            for token in cls._tokens(prompt):
                tokens[token] = tokens.get(token, 0) + 1
        ranked = sorted(tokens, key=lambda token: (-tokens[token], token))[:4]
        return "-".join(ranked) or fallback

    @staticmethod
    def _band(score: int, monitor: bool = False) -> str:
        if monitor:
            return "monitor"
        if score >= 75:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    @classmethod
    def _finalize(cls, item: dict) -> dict:
        modes = sorted(set(item["source_modes"]))
        severity = item.pop("severity")
        confidence_points = 15 if item["confidence"] == "high" else 10 if item["confidence"] == "medium" else 5
        corroboration = 15 if len(modes) > 1 else 0
        blocking = 15 if "readiness" in modes else 0
        score = 0 if item.get("monitor") else min(100, severity + confidence_points + corroboration + blocking)
        item["priority_score"] = score
        item["priority"] = cls._band(score, item.pop("monitor", False))
        item["source_modes"] = modes
        item["score_components"] = {
            "evidence_severity": severity,
            "evidence_confidence": confidence_points,
            "cross_mode_corroboration": corroboration,
            "prerequisite_importance": blocking,
            "effort_excluded_from_score": True,
        }
        item["why_ranked"] = (
            f"{severity} severity points + {confidence_points} confidence points"
            + (f" + {corroboration} cross-mode corroboration points" if corroboration else "")
            + (f" + {blocking} prerequisite points" if blocking else "")
            + ". Effort is shown separately and does not change importance."
        )
        item["observed_evidence"] = list(dict.fromkeys(item["observed_evidence"]))
        item["affected_prompts"] = list(dict.fromkeys(item["affected_prompts"]))
        item["affected_pages"] = list(dict.fromkeys(item["affected_pages"]))
        item["affected_entities"] = list(dict.fromkeys(item["affected_entities"]))
        payload = {key: item[key] for key in sorted(item) if key != "evidence_fingerprint"}
        item["evidence_fingerprint"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        return item

    @classmethod
    def _technical_candidates(cls, db: Session, project_id: int) -> list[dict]:
        try:
            summary = TechnicalSEOSummaryService.build(db, project_id)
        except HTTPException as error:
            if error.status_code == 404:
                return []
            raise
        grouped: dict[str, list] = {}
        for recommendation in summary["recommendations"]:
            family = recommendation["issue_code"].lower()
            grouped.setdefault(family, []).append(recommendation)
        pages_by_id = {page["id"]: page["url"] for page in summary["pages"]}
        candidates = []
        for family, recommendations in grouped.items():
            top = max(recommendations, key=lambda item: item["priority_score"])
            pages = sorted({pages_by_id.get(item["page_id"], "") for item in recommendations} - {""})
            severity = 60 if top["priority"] == "high" else 45 if top["priority"] == "medium" else 25
            candidates.append({
                "stable_key": f"technical:{family}", "title": top["title"], "severity": severity,
                "impact": top["priority"], "effort": "medium", "confidence": "high",
                "observed_evidence": [f"{len(recommendations)} stored finding(s) in the latest bounded technical audit."],
                "interpretation": "The repeated page-level findings represent one technical work package, not separate strategic tasks.",
                "recommended_action": top["recommendation"], "affected_prompts": [],
                "affected_pages": pages, "affected_entities": [], "source_modes": ["technical_seo"],
                "provenance": {"technical_audit_id": summary["audit"]["id"] if summary["audit"] else None, "issue_code": top["issue_code"]},
            })
        return candidates

    @classmethod
    def _web_candidates(cls, db: Session, project_id: int) -> list[dict]:
        experiment_id = db.scalar(
            select(GeoPromptOpportunity.experiment_id)
            .join(BenchmarkJob, BenchmarkJob.experiment_id == GeoPromptOpportunity.experiment_id)
            .where(GeoPromptOpportunity.project_id == project_id, BenchmarkJob.benchmark_mode == "web_search")
            .order_by(GeoPromptOpportunity.experiment_id.desc()).limit(1)
        )
        if experiment_id is None:
            return []
        rows = list(db.scalars(select(GeoPromptOpportunity).where(
            GeoPromptOpportunity.experiment_id == experiment_id
        ).order_by(GeoPromptOpportunity.opportunity_score.desc())).all())
        candidates = []
        for row in rows:
            if row.gap_type not in {"target_absent", "competitor_dominance", "unmeasured_web_search"}:
                continue
            monitor = row.gap_type == "unmeasured_web_search"
            title = (
                f"Recheck Web Search measurement for: {row.prompt_text}"
                if monitor else f"Improve Web Search evidence for: {row.prompt_text}"
            )
            candidates.append({
                "stable_key": f"evidence:{cls._topic_key([row.prompt_text], str(row.prompt_id))}",
                "title": title, "severity": 0 if monitor else max(35, min(70, round(row.opportunity_score * .7))),
                "impact": "low" if monitor else row.priority, "effort": "medium", "confidence": "low" if monitor else "high",
                "monitor": monitor,
                "observed_evidence": [
                    "No live-web source measurement was returned; this is unmeasured, not a visibility failure."
                    if monitor else f"Target grounded presence was {row.target_mention_rate}% across {row.run_count} measured run(s)."
                ],
                "interpretation": (
                    "A compatible Web Search recheck is needed before drawing an SEO conclusion."
                    if monitor else "Stored Web Search evidence shows an actionable target-absence or competitor-dominance opportunity."
                ),
                "recommended_action": row.recommendation,
                "affected_prompts": [row.prompt_text], "affected_pages": [],
                "affected_entities": [row.top_competitor_name] if row.top_competitor_name else [],
                "source_modes": ["web_search"],
                "provenance": {"web_experiment_id": experiment_id, "opportunity_ids": [row.id], "gap_types": [row.gap_type]},
            })
        return candidates

    @classmethod
    def _site_rag_candidates(cls, db: Session, project_id: int) -> list[dict]:
        analysis = SiteRAGGapAnalysisRepository.latest_completed_by_project(db, project_id)
        if analysis is None or analysis.gap_count == 0:
            return []
        gaps = list(db.scalars(select(SiteRAGGap).where(
            SiteRAGGap.experiment_id == analysis.experiment_id
        ).order_by(SiteRAGGap.gap_score.desc())).all())
        grouped: dict[str, list] = {}
        for gap in gaps:
            grouped.setdefault(gap.gap_type, []).append(gap)
        candidates = []
        for gap_type, rows in grouped.items():
            prompts = [row.prompt_text for row in rows]
            top = max(rows, key=lambda row: row.gap_score)
            candidates.append({
                "stable_key": f"evidence:{cls._topic_key(prompts, gap_type)}",
                "title": {
                    "competitive_evidence_gap": "Create a factual comparison and evaluation resource",
                    "insufficient_product_evidence": "Strengthen first-party product evidence",
                    "insufficient_use_case_evidence": "Expand first-party use-case evidence",
                    "insufficient_proof_evidence": "Add verifiable proof evidence",
                }.get(gap_type, "Strengthen first-party evidence"),
                "severity": max(45, min(70, round(top.gap_score * .7))),
                "impact": top.priority, "effort": "medium", "confidence": "high",
                "observed_evidence": [f"{len(rows)} persisted Site RAG evidence gap(s) share the {gap_type} classification."],
                "interpretation": "The current first-party crawl corpus cannot fully support these answers.",
                "recommended_action": top.recommendation, "affected_prompts": prompts,
                "affected_pages": [], "affected_entities": [], "source_modes": ["site_rag"],
                "provenance": {"site_rag_experiment_id": analysis.experiment_id, "site_rag_gap_ids": [row.id for row in rows], "gap_types": [gap_type]},
            })
        return candidates

    @classmethod
    def _readiness_candidates(cls, db: Session, project_id: int) -> list[dict]:
        readiness = ProjectReadinessService.build(db, project_id)
        candidates = []
        for mode, measurement in readiness["measurements"].items():
            if measurement["state"] not in {"blocked", "needs_review", "limited"}:
                continue
            candidates.append({
                "stable_key": f"readiness:{mode}", "title": f"Resolve {mode.replace('_', ' ').title()} readiness",
                "severity": 55 if measurement["state"] == "blocked" else 35,
                "impact": "high" if measurement["state"] == "blocked" else "medium", "effort": "low", "confidence": "high",
                "observed_evidence": list(measurement["evidence"]), "interpretation": measurement["reason"],
                "recommended_action": measurement["recommended_action"], "affected_prompts": [], "affected_pages": [],
                "affected_entities": [], "source_modes": ["readiness", mode],
                "provenance": {"readiness_state": measurement["state"], "measurement_mode": mode},
            })
        return candidates

    @classmethod
    def _merge(cls, candidates: list[dict]) -> list[dict]:
        merged: list[dict] = []
        for candidate in candidates:
            target = None
            candidate_tokens = set().union(*(cls._tokens(value) for value in candidate["affected_prompts"]))
            if candidate_tokens and "technical_seo" not in candidate["source_modes"] and "readiness" not in candidate["source_modes"]:
                for existing in merged:
                    existing_tokens = set().union(*(cls._tokens(value) for value in existing["affected_prompts"]))
                    overlap = len(candidate_tokens & existing_tokens) / max(1, min(len(candidate_tokens), len(existing_tokens)))
                    if existing_tokens and overlap >= .4 and not set(candidate["source_modes"]).issubset(existing["source_modes"]):
                        target = existing
                        break
            if target is None:
                merged.append(candidate)
                continue
            target["title"] = candidate["title"] if "site_rag" in candidate["source_modes"] else target["title"]
            target["severity"] = max(target["severity"], candidate["severity"])
            for key in ("observed_evidence", "affected_prompts", "affected_pages", "affected_entities", "source_modes"):
                target[key].extend(candidate[key])
            target["recommended_action"] = target["recommended_action"] + " " + candidate["recommended_action"]
            target["interpretation"] = "Independent Web Search and Site RAG evidence point to the same underlying content/evidence problem."
            target["provenance"].update(candidate["provenance"])
        return merged

    @classmethod
    def build_candidates(cls, db: Session, project_id: int) -> list[dict]:
        if ProjectRepository.get_by_id(db, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        raw = cls._technical_candidates(db, project_id) + cls._web_candidates(db, project_id) + cls._site_rag_candidates(db, project_id) + cls._readiness_candidates(db, project_id)
        return [cls._finalize(item) for item in cls._merge(raw)]

    @classmethod
    def refresh(cls, db: Session, project_id: int) -> dict:
        candidates = cls.build_candidates(db, project_id)
        existing = ProjectPriorityRepository.by_key(db, project_id)
        seen = set()
        now = datetime.now(timezone.utc)
        for candidate in candidates:
            key = candidate["stable_key"]
            seen.add(key)
            record = existing.get(key)
            if record is None:
                record = ProjectPriority(project_id=project_id, stable_key=key, status="open")
                db.add(record)
            for field in (
                "title", "priority", "priority_score", "impact", "effort", "confidence",
                "observed_evidence", "interpretation", "recommended_action", "affected_prompts",
                "affected_pages", "affected_entities", "source_modes", "score_components", "evidence_fingerprint",
            ):
                setattr(record, field, candidate[field])
            record.provenance = {**candidate["provenance"], "why_ranked": candidate["why_ranked"]}
            record.is_resolved = False
            record.resolved_at = None
        for key, record in existing.items():
            if key not in seen and not record.is_resolved:
                record.is_resolved = True
                record.resolved_at = now
        db.commit()
        return cls.summary(db, project_id)

    @classmethod
    def backfill_missing(cls, db: Session) -> list[int]:
        refreshed = []
        for project in ProjectRepository.list_all(db):
            if ProjectPriorityRepository.list_by_project(db, project.id):
                continue
            if cls.build_candidates(db, project.id):
                cls.refresh(db, project.id)
                refreshed.append(project.id)
        return refreshed

    @classmethod
    def summary(cls, db: Session, project_id: int) -> dict:
        if ProjectRepository.get_by_id(db, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        priorities = ProjectPriorityRepository.list_by_project(db, project_id)
        active = [item for item in priorities if not item.is_resolved]
        return {
            "project_id": project_id,
            "open_priorities": sum(item.status == "open" for item in active),
            "high_priority": sum(item.priority == "high" for item in active),
            "in_progress": sum(item.status == "in_progress" for item in active),
            "ready_to_recheck": sum(item.status == "ready_to_recheck" for item in active),
            "priorities": priorities,
            "provenance_note": "Priorities are persisted by an explicit deterministic refresh from stored SearchIntel evidence. Loading this page is read-only and never calls AI, web search, or a crawler.",
        }

    @classmethod
    def update_status(cls, db: Session, project_id: int, priority_id: int, status: str) -> ProjectPriority:
        if status not in cls.VALID_STATUSES:
            raise HTTPException(status_code=422, detail="Invalid priority status.")
        record = ProjectPriorityRepository.get(db, project_id, priority_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Priority not found.")
        record.status = status
        db.commit()
        db.refresh(record)
        return record
