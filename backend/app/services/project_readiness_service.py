from collections import Counter
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.benchmark_job import BenchmarkJob
from app.models.brand import Brand
from app.models.brand_mention import BrandMention
from app.models.web_search_source import WebSearchSource
from app.models.prompt_set_proposal import PromptSetProposal
from app.repositories.page_repository import PageRepository
from app.repositories.project_brand_repository import ProjectBrandRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.prompt_repository import PromptRepository
from app.repositories.technical_audit_repository import TechnicalAuditRepository
from app.repositories.website_repository import WebsiteRepository
from app.services.ai_model_service import AIModelService
from app.services.starter_prompt_generation_service import StarterPromptGenerationService
from app.repositories.competitor_discovery_repository import CompetitorDiscoveryRepository


class ProjectReadinessService:
    MIN_USABLE_PAGES = 3
    MIN_USABLE_WORDS = 500

    @staticmethod
    def _domain(value: str | None) -> str:
        if not value:
            return ""
        host = urlparse(
            value if "://" in value else f"https://{value}"
        ).hostname or ""
        return host.lower().removeprefix("www.")

    @staticmethod
    def _issue(
        code: str,
        message: str,
        action: str | None = None,
        evidence: list[str] | None = None,
    ) -> dict:
        return {
            "code": code,
            "message": message,
            "evidence": evidence or [],
            "recommended_action": action,
        }

    @classmethod
    def _historical_modes(
        cls,
        db: Session,
        project_id: int,
    ) -> set[str]:
        statement = select(
            BenchmarkJob.benchmark_mode
        ).where(
            BenchmarkJob.project_id == project_id,
            BenchmarkJob.status.in_([
                "completed",
                "completed_with_errors",
            ]),
        ).distinct()
        return set(db.scalars(statement).all())

    @classmethod
    def _first_party_suggestions(
        cls,
        db: Session,
        project_id: int,
        target_brand_id: int | None,
        configured_domains: set[str],
        pages: list,
    ) -> list[dict]:
        if target_brand_id is None:
            return []

        evidence_by_domain: dict[str, list[str]] = {}

        source_statement = (
            select(
                WebSearchSource.domain,
                func.count(WebSearchSource.id),
            )
            .join(
                AIResponse,
                AIResponse.id == WebSearchSource.response_id,
            )
            .join(AIRun, AIRun.id == AIResponse.run_id)
            .where(
                AIRun.project_id == project_id,
                WebSearchSource.brand_id == target_brand_id,
                WebSearchSource.domain.is_not(None),
            )
            .group_by(WebSearchSource.domain)
        )
        for raw_domain, count in db.execute(source_statement).all():
            domain = cls._domain(raw_domain)
            if domain and domain not in configured_domains and count >= 2:
                evidence_by_domain.setdefault(domain, []).append(
                    f"{count} stored Web Search sources were already resolved to the target brand."
                )

        canonical_counts: Counter[str] = Counter()
        for page in pages:
            domain = cls._domain(page.canonical_url)
            if domain and domain not in configured_domains:
                canonical_counts[domain] += 1
        for domain, count in canonical_counts.items():
            evidence_by_domain.setdefault(domain, []).append(
                f"{count} crawled first-party page(s) declare a canonical URL on this domain."
            )

        return [
            {
                "key": f"first-party:{domain}",
                "kind": "first_party_domain",
                "value": domain,
                "reason": "Stored first-party evidence points to an unconfigured domain. Confirm ownership before using it for attribution.",
                "evidence": evidence,
                "approval_required": True,
            }
            for domain, evidence in sorted(evidence_by_domain.items())
        ]

    @classmethod
    def _competitor_suggestions(
        cls,
        db: Session,
        project_id: int,
        configured_brand_ids: set[int],
    ) -> list[dict]:
        statement = (
            select(
                Brand.id,
                Brand.name,
                func.count(BrandMention.id),
            )
            .join(
                BrandMention,
                BrandMention.brand_id == Brand.id,
            )
            .join(
                AIResponse,
                AIResponse.id == BrandMention.response_id,
            )
            .join(AIRun, AIRun.id == AIResponse.run_id)
            .where(
                AIRun.project_id == project_id,
                BrandMention.is_target.is_(False),
                BrandMention.resolution_status == "resolved",
                BrandMention.brand_id.is_not(None),
            )
            .group_by(Brand.id, Brand.name)
            .having(func.count(BrandMention.id) >= 2)
            .order_by(func.count(BrandMention.id).desc())
            .limit(5)
        )
        return [
            {
                "key": f"competitor:{brand_id}",
                "kind": "competitor",
                "value": name,
                "reason": "This resolved brand repeatedly appeared in stored project benchmark responses.",
                "evidence": [f"{count} resolved non-target appearances."],
                "approval_required": True,
            }
            for brand_id, name, count in db.execute(statement).all()
            if brand_id not in configured_brand_ids
        ]

    @classmethod
    def build(
        cls,
        db: Session,
        project_id: int,
    ) -> dict:
        project = ProjectRepository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        brand_roles = ProjectBrandRepository.list_brand_roles(
            db, project_id
        )
        targets = [brand for brand, role in brand_roles if role == "target"]
        competitors = [brand for brand, role in brand_roles if role == "competitor"]
        target = targets[0] if len(targets) == 1 else None
        websites = WebsiteRepository.list_by_brand(
            db, target.id
        ) if target else []
        primaries = [website for website in websites if website.is_primary]
        primary = primaries[0] if len(primaries) == 1 else None
        pages = PageRepository.list_by_website(
            db, primary.id
        ) if primary else []
        prompts = PromptRepository.list_by_project(db, project_id)
        active_prompts = [prompt for prompt in prompts if prompt.is_active]
        latest_proposal = db.scalar(
            select(PromptSetProposal)
            .where(PromptSetProposal.project_id == project_id)
            .order_by(PromptSetProposal.created_at.desc(), PromptSetProposal.id.desc())
        )
        latest_coverage = latest_proposal.coverage_blueprint if latest_proposal else {}
        latest_coverage_warnings = list(latest_proposal.warnings) if latest_proposal else []
        if (latest_proposal and getattr(latest_proposal, "generator_version", None) in {
                StarterPromptGenerationService.GENERATOR_VERSION,
                "automatic-rebalance-v5", "market-anchor-v4",
        }):
            latest_coverage, computed_warnings = StarterPromptGenerationService.coverage(
                latest_proposal.prompts,
                latest_proposal.measurement_scope,
                latest_proposal.topic_clusters,
                latest_coverage.get("core_category"),
                latest_coverage.get("crawl_sample_bias"),
            )
            latest_coverage_warnings = list(dict.fromkeys([
                *latest_coverage_warnings, *computed_warnings,
            ]))
        proposed_prompt_count = (
            len(latest_proposal.prompts)
            if latest_proposal and latest_proposal.status == "proposed"
            else 0
        )
        normalized_prompts = [prompt.text.strip().lower() for prompt in active_prompts if prompt.text.strip()]
        duplicate_count = len(normalized_prompts) - len(set(normalized_prompts))
        categories = sorted({
            prompt.category.strip().lower()
            for prompt in active_prompts
            if prompt.category and prompt.category.strip()
        })
        usable_pages = [
            page for page in pages
            if page.status_code is not None
            and 200 <= page.status_code < 300
            and page.content_text
            and page.word_count >= 100
        ]
        usable_words = sum(page.word_count for page in usable_pages)
        configured_domains = {
            cls._domain(website.domain) for website in websites
        }
        historical_modes = cls._historical_modes(db, project_id)
        has_technical_history = bool(
            primary and TechnicalAuditRepository.get_latest(db, primary.id)
        )
        ai_available = settings.openai_api_key is not None
        try:
            execution_model = (
                AIModelService.resolve_execution_model(
                    db,
                    None,
                ).provider_model_id
            )
        except HTTPException:
            execution_model = None

        issues: list[dict] = []
        warnings: list[dict] = []
        if len(targets) == 0:
            issues.append(cls._issue(
                "missing_target_brand",
                "No target brand is configured.",
                "Choose the client brand before measurement.",
            ))
        elif len(targets) > 1:
            issues.append(cls._issue(
                "ambiguous_target_brand",
                "More than one target brand is configured.",
                "Review the brand roles and keep one target brand.",
                [f"{len(targets)} target brands are linked."],
            ))
        elif not target.name.strip():
            issues.append(cls._issue(
                "empty_target_brand",
                "The target brand name is empty.",
                "Provide an unambiguous target brand name.",
            ))

        if target and len(primaries) == 0:
            issues.append(cls._issue(
                "missing_primary_website",
                "No primary first-party website is configured.",
                "Add the client’s primary website and confirm ownership.",
            ))
        elif len(primaries) > 1:
            issues.append(cls._issue(
                "multiple_primary_websites",
                "Multiple websites are marked primary.",
                "Choose one primary website; retain other owned domains as secondary.",
                [f"{len(primaries)} primary websites are configured."],
            ))

        if not active_prompts:
            issues.append(cls._issue(
                "no_active_prompts",
                "No active measurement prompts are configured.",
                "Add a small representative prompt set.",
            ))
            if proposed_prompt_count:
                warnings.append(cls._issue(
                    "prompt_proposal_awaiting_approval",
                    "A starter prompt proposal is awaiting approval; it is not an active measurement set.",
                    "Review and explicitly apply the proposal before measurement.",
                    [f"{proposed_prompt_count} proposed prompt(s)."],
                ))
        if duplicate_count:
            warnings.append(cls._issue(
                "duplicate_prompts",
                "Active prompts contain duplicates.",
                "Review and deactivate duplicate prompts.",
                [f"{duplicate_count} duplicate prompt(s)."],
            ))
        if not competitors:
            warnings.append(cls._issue(
                "no_competitors",
                "No comparison brands are configured.",
                "Add relevant competitors or explicitly continue without competitive comparison.",
            ))
        if active_prompts and len(categories) < 2:
            warnings.append(cls._issue(
                "limited_prompt_diversity",
                "The active prompt set covers fewer than two categories.",
                "Review whether another decision-stage category would improve coverage.",
                categories,
            ))
        if latest_proposal and latest_proposal.status == "proposed":
            for message in latest_coverage_warnings:
                warnings.append(cls._issue(
                    "prompt_coverage_needs_review", message,
                    "Review topic and intent coverage before applying the proposal.",
                ))
            bias = latest_coverage.get("crawl_sample_bias", {})
            if bias.get("detected"):
                warnings.append(cls._issue(
                    "prompt_crawl_sample_bias",
                    bias.get("reason") or "The bounded crawl overrepresents one product area.",
                    "Review the core-market anchor and super-theme coverage before applying the proposal.",
                    bias.get("evidence", []),
                ))

        suggestions = cls._first_party_suggestions(
            db, project_id, target.id if target else None,
            configured_domains, pages,
        )
        suggestions.extend(cls._competitor_suggestions(
            db, project_id, {brand.id for brand, _role in brand_roles}
        ))
        desired_categories = [
            ("brand", "Brand recognition and identity"),
            ("problem_solution", "Problem or use-case discovery"),
            ("recommendation", "Recommendation-stage visibility"),
            ("comparison", "Comparison-stage visibility"),
            ("commercial", "Buying and commercial evaluation"),
        ]
        normalized_categories = {category.replace(" ", "_") for category in categories}
        for category, label in desired_categories:
            if category not in normalized_categories:
                suggestions.append({
                    "key": f"prompt-category:{category}",
                    "kind": "prompt_category",
                    "value": category,
                    "reason": f"Consider whether {label.lower()} is relevant to this client.",
                    "evidence": ["This category is not present in the active prompt set."],
                    "approval_required": True,
                })

        identity_blocked = len(targets) != 1 or not target or not target.name.strip()
        prompt_blocked = not active_prompts
        website_blocked = primary is None
        shared_warnings = [warning for warning in warnings]
        execution_note = (
            "The backend has an AI execution key configured."
            if ai_available else
            "Configuration may be ready, but the backend has no OpenAI execution key."
        )

        def measurement(
            mode: str,
            state: str,
            reason: str,
            evidence: list[str],
            blockers: list[dict],
            mode_warnings: list[dict],
            action: str,
            execution_available: bool,
            historical: bool,
        ) -> dict:
            return {
                "mode": mode,
                "state": state,
                "reason": reason,
                "evidence": evidence,
                "blocking_issues": blockers,
                "warnings": mode_warnings,
                "recommended_action": action,
                "execution_available": execution_available,
                "execution_note": execution_note if mode != "technical_seo" else "Crawls and technical audits do not require an AI key.",
                "has_historical_results": historical,
            }

        identity_issues = [item for item in issues if item["code"] in {"missing_target_brand", "ambiguous_target_brand", "empty_target_brand"}]
        prompt_issues = [item for item in issues if item["code"] == "no_active_prompts"]
        website_issues = [item for item in issues if item["code"] in {"missing_primary_website", "multiple_primary_websites"}]

        if website_blocked:
            technical = measurement("technical_seo", "blocked", "A primary first-party website is required.", [], website_issues or identity_issues, [], "Confirm a primary first-party website.", True, has_technical_history)
        else:
            crawl = primary.last_crawl_summary or {}
            blocked_count = int(crawl.get("pages_blocked_by_robots", 0) or 0)
            if blocked_count and not pages:
                technical = measurement("technical_seo", "limited", "The website’s robots policy blocked SearchIntelBot from the bounded crawl.", [f"{blocked_count} URL(s) blocked in the last explicit crawl."], [], [cls._issue("robots_limited", "SearchIntel could not read enough pages for a complete bounded audit.", "Review robots policy or document the crawl limitation.")], "Treat the technical result as limited; this does not imply that search engines cannot crawl the site.", True, has_technical_history)
            elif not pages:
                technical = measurement("technical_seo", "needs_review", "No bounded crawl corpus is stored yet.", [], [], [], "Run a bounded crawl to establish technical eligibility.", True, has_technical_history)
            else:
                coverage_warnings = (
                    [cls._issue(
                        "limited_technical_sample",
                        "The current bounded crawl contains only one stored page.",
                        "Treat audit findings as sample-specific and review crawl discovery before drawing broader conclusions.",
                    )]
                    if len(pages) == 1
                    else []
                )
                technical = measurement("technical_seo", "ready", "Stored pages are available for a bounded technical audit.", [f"{len(pages)} stored page(s).", f"{len(usable_pages)} content-usable page(s)."], [], coverage_warnings, "Run or refresh the technical audit when needed.", True, has_technical_history)

        ai_blockers = identity_issues + prompt_issues
        if ai_blockers:
            memory = measurement("memory", "blocked", "Target identity and active prompts are required.", [], ai_blockers, shared_warnings, "Resolve the blocking configuration issues.", ai_available, "memory" in historical_modes)
        else:
            memory_state = "needs_review" if warnings else "ready"
            memory = measurement("memory", memory_state, "Target identity and active prompts support latent model-knowledge measurement.", [f"{len(active_prompts)} active prompt(s)."], [], shared_warnings, "Review warnings, then run a controlled Memory baseline." if warnings else "Run a controlled Memory baseline when needed.", ai_available, "memory" in historical_modes)

        web_blockers = ai_blockers + website_issues
        domain_suggestions = [item for item in suggestions if item["kind"] == "first_party_domain"]
        web_warnings = shared_warnings + ([cls._issue("possible_missing_first_party_domains", "Stored evidence suggests additional first-party domains may need review.", "Approve only domains the client owns.", [item["value"] for item in domain_suggestions])] if domain_suggestions else [])
        if web_blockers:
            web = measurement("web_search", "blocked", "Target identity, a primary website, and active prompts are required for attributable Web Search measurement.", [], web_blockers, web_warnings, "Resolve the blocking configuration issues.", ai_available, "web_search" in historical_modes)
        else:
            web_state = "needs_review" if web_warnings else "ready"
            web = measurement("web_search", web_state, "The project can measure controlled API web-search retrieval and citation evidence.", [f"Primary domain: {primary.domain}.", f"{len(active_prompts)} active prompt(s)."], [], web_warnings, "Review identity suggestions before the next run." if web_warnings else "Run a controlled Web Search baseline when needed.", ai_available, "web_search" in historical_modes)

        site_blockers = ai_blockers + website_issues
        if site_blockers:
            site_rag = measurement("site_rag", "blocked", "Target identity, a primary website, active prompts, and a usable first-party corpus are required.", [], site_blockers, [], "Resolve the blocking configuration issues and crawl the confirmed first-party site.", ai_available, "site_rag" in historical_modes)
        elif len(usable_pages) < cls.MIN_USABLE_PAGES or usable_words < cls.MIN_USABLE_WORDS:
            corpus_issue = cls._issue("insufficient_site_rag_corpus", "No sufficiently broad first-party content corpus is stored.", "Run a bounded crawl or add another confirmed crawlable first-party website.", [f"{len(usable_pages)} usable page(s).", f"{usable_words} usable words."])
            site_rag = measurement("site_rag", "blocked", "The stored crawl does not contain enough meaningful first-party evidence.", corpus_issue["evidence"], [corpus_issue], [], "Build a usable first-party corpus before running Site RAG.", ai_available, "site_rag" in historical_modes)
        else:
            site_rag = measurement("site_rag", "ready", "The stored first-party corpus is sufficient for bounded answerability measurement.", [f"{len(usable_pages)} usable page(s).", f"{usable_words} usable words."], [], [], "Run a controlled Site RAG baseline when needed.", ai_available, "site_rag" in historical_modes)

        measurements = {
            "technical_seo": technical,
            "memory": memory,
            "web_search": web,
            "site_rag": site_rag,
        }
        states = {item["state"] for item in measurements.values()}
        overall = "blocked" if states == {"blocked"} else (
            "needs_review" if "needs_review" in states or "blocked" in states or "limited" in states else "ready"
        )

        return {
            "project_id": project.id,
            "project_name": project.name,
            "overall_state": overall,
            "configuration": {
                "measurement_scope": getattr(project, "measurement_scope", None) or "brand_wide",
                "measurement_focus": getattr(project, "measurement_focus", None),
                "target_brand_id": target.id if target else None,
                "target_brand": target.name if target else None,
                "target_brand_count": len(targets),
                "primary_website_id": primary.id if primary else None,
                "primary_domain": primary.domain if primary else None,
                "first_party_domains": sorted(configured_domains),
                "competitor_count": len(competitors),
                "pending_competitor_suggestion_count": (
                    CompetitorDiscoveryRepository.pending_count(db, project_id)
                ),
                "active_prompt_count": len(active_prompts),
                "proposed_prompt_count": proposed_prompt_count,
                "prompt_coverage_state": (
                    "blocked" if not active_prompts and not proposed_prompt_count else
                    "needs_review" if proposed_prompt_count or (
                        latest_proposal and latest_coverage_warnings
                    ) else "ready"
                ),
                "proposed_prompt_coverage_status": (
                    latest_coverage.get("concentration_status")
                    if latest_proposal and latest_proposal.status == "proposed" else None
                ),
                "proposed_largest_topic_family_share": (
                    latest_coverage.get("largest_topic_family_share")
                    if latest_proposal and latest_proposal.status == "proposed" else None
                ),
                "proposed_largest_super_theme_share": (
                    latest_coverage.get("largest_super_theme_share")
                    if latest_proposal and latest_proposal.status == "proposed" else None
                ),
                "proposed_crawl_sample_bias": (
                    bool(latest_coverage.get("crawl_sample_bias", {}).get("detected"))
                    if latest_proposal and latest_proposal.status == "proposed" else None
                ),
                "prompt_categories": categories,
                "usable_page_count": len(usable_pages),
                "usable_word_count": usable_words,
                "execution_model": execution_model,
            },
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "measurements": measurements,
            "provenance_note": "This read-only preflight uses stored SearchIntel configuration and evidence. It does not crawl, search the web, call an AI model, or change project ownership decisions.",
        }
