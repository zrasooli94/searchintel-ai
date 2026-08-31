from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ClientReportPDFService:
    @staticmethod
    def render(report) -> bytes:
        snapshot = report.snapshot
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title=report.title)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=colors.HexColor("#312E81"), alignment=TA_CENTER, spaceAfter=16))
        styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=15, leading=19, textColor=colors.HexColor("#3730A3"), spaceBefore=12, spaceAfter=8))
        styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#64748B")))
        story = [Paragraph("SEARCHINTEL CLIENT REPORT", styles["Small"]), Paragraph(escape(report.title), styles["ReportTitle"]), Paragraph(escape(snapshot["project"]["name"]), styles["Heading2"]), Paragraph(escape(f"Report date: {snapshot['generated_at'][:10]}" + (f" | Period: {report.period_label}" if report.period_label else "")), styles["BodyText"]), Spacer(1, 12)]

        def section(title, text):
            story.extend([Paragraph(escape(title), styles["Section"]), Paragraph(escape(text or "No measured evidence is available for this section."), styles["BodyText"])])

        section("Executive Summary", snapshot["executive_summary"]["note"])
        technical = snapshot["technical_seo"]
        audit = technical.get("audit") or {}
        section("Technical SEO", f"Measurement: {technical.get('measurement_state', 'unavailable').upper()}. Score: {audit.get('score', 'N/A')}. Pages checked: {audit.get('pages_checked', technical.get('successful_pages', 0))}. Findings: {audit.get('issue_count', len(technical.get('issues', [])))}. {technical.get('coverage_reason') or technical.get('measurement_reason') or ''}")
        for mode, label in (("web_search", "Web Search / AI Visibility"), ("memory", "Memory Context"), ("site_rag", "Site RAG / First-Party Evidence")):
            item = snapshot["measurements"].get(mode)
            if not item:
                section(label, "No completed stored measurement was available when this snapshot was created.")
                continue
            metrics = item["metrics"]
            target = metrics.get("target", {})
            if mode == "site_rag":
                text = f"Answerability: {metrics.get('site_answerability_rate_v1', 'N/A')}%. Supported: {metrics.get('site_rag_analyzed_runs', 0) - round((metrics.get('unsupported_answer_rate_v1') or 0) * metrics.get('site_rag_analyzed_runs', 0) / 100)}/{metrics.get('site_rag_analyzed_runs', 0)}. Evidence coverage: {metrics.get('evidence_coverage_rate', 'N/A')}%. Source references: {metrics.get('source_reference_rate', 'N/A')}%."
            elif mode == "web_search":
                text = f"Web visibility: {target.get('web_visibility_score', 'N/A')}. Verified response coverage: {target.get('entity_verified_response_coverage', 'N/A')}%. Retrieved coverage: {target.get('retrieval_associated_response_coverage', 'N/A')}%. Cited coverage: {target.get('cited_response_coverage', 'N/A')}%."
            else:
                text = f"Latent model-knowledge context across {metrics.get('analyzed_prompts', 0)} prompts. Verified response coverage: {target.get('entity_verified_response_coverage', 'N/A')}%."
            section(label, text)
        section("Competitor Position", ", ".join(snapshot["competitor_position"]["configured_competitors"]) or "No configured competitors.")
        story.append(PageBreak())
        story.append(Paragraph("Priorities and Progress", styles["Section"]))
        rows = [["Priority", "Status", "Next action"]] + [[p["title"], p["status"].replace("_", " ").title(), p["recommended_action"]] for p in snapshot["priorities"]]
        table = Table(rows, colWidths=[48 * mm, 28 * mm, 82 * mm], repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#312E81")), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#CBD5E1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTSIZE", (0, 0), (-1, -1), 8), ("LEADING", (0, 0), (-1, -1), 10), ("PADDING", (0, 0), (-1, -1), 5)]))
        story.append(table)
        for item in snapshot["compatible_rechecks"]:
            before = (item["baseline"].get("metrics") or {})
            after = (item["recheck"].get("metrics") or {})
            section("Before -> After Compatible Recheck", f"{item['title']}: {before.get('site_answerability_rate_v1', 'N/A')}% ({before.get('site_rag_analyzed_runs', 0) - item['baseline']['gap_count']}/{before.get('site_rag_analyzed_runs', 0)} supported, {item['baseline']['gap_count']} gaps) -> {after.get('site_answerability_rate_v1', 'N/A')}% ({after.get('site_rag_analyzed_runs', 0) - item['recheck']['gap_count']}/{after.get('site_rag_analyzed_runs', 0)} supported, {item['recheck']['gap_count']} gaps). Outcome: {item['status'].replace('_', ' ').upper()}. {item.get('explanation') or ''}")
        section("Measurement Scope and Provenance", snapshot["scope_and_provenance"]["snapshot_note"])

        def footer(canvas, document):
            canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#64748B")); canvas.drawString(18 * mm, 10 * mm, snapshot["project"]["name"]); canvas.drawRightString(192 * mm, 10 * mm, f"Page {document.page}"); canvas.restoreState()
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return output.getvalue()
