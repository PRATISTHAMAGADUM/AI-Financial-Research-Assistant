import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List
from fpdf import FPDF

class FinancialPDFReport(FPDF):
    def header(self):
        # Header banner
        self.set_fill_color(15, 23, 42)  # Dark navy #0F172A
        self.rect(0, 0, 210, 25, "F")
        
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 8)
        self.cell(120, 8, "AI FINANCIAL RESEARCH REPORT")

        self.set_font("Helvetica", "I", 9)
        self.set_text_color(148, 163, 184)
        self.set_xy(135, 8)
        self.cell(65, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"AI Financial Research Assistant | Confidential Research Document | Page {self.page_no()}/{{nb}}", align="C")

def sanitize_text(text: str) -> str:
    """Sanitize unicode characters for Latin-1 encoding in FPDF standard fonts."""
    if not text:
        return ""
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
        "…": "...", "™": "TM", "®": "(R)", "©": "(C)", "•": "-",
        "⚠️": "[WARNING]", "✅": "[OK]", "❌": "[FAIL]", "💡": "[INFO]"
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.encode("latin-1", "replace").decode("latin-1")

def generate_pdf_report(report_data: Dict[str, Any]) -> str:
    """
    Generates a professional financial research report PDF.
    Returns the file path to the generated PDF.
    """
    pdf = FinancialPDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=18)

    query = sanitize_text(report_data.get("query", "N/A"))
    answer = sanitize_text(report_data.get("answer", ""))
    grounding_score = report_data.get("grounding_score", 1.0)
    grounding_pct = report_data.get("grounding_percentage", round(grounding_score * 100, 1))
    warning_msg = sanitize_text(report_data.get("warning_message", ""))
    claims = report_data.get("claims", [])
    sources = report_data.get("sources", [])
    search_mode = sanitize_text(report_data.get("search_mode", "Research Mode"))

    # Section 1: Executive Overview Box
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(190, 6, f"Research Prompt: {query}")
    pdf.ln(2)

    # Grounding Score Card Container
    pdf.set_fill_color(241, 245, 249) # Light slate
    start_y = pdf.get_y()
    pdf.rect(10, start_y, 190, 24, "F")

    # Score color selection
    if grounding_pct >= 85:
        score_color = (22, 163, 74) # Green
        status_txt = "HIGHLY GROUNDED (VERIFIED)"
    elif grounding_pct >= 70:
        score_color = (217, 119, 6) # Amber
        status_txt = "MODERATELY GROUNDED"
    else:
        score_color = (220, 38, 38) # Red
        status_txt = "LOW GROUNDING - UNVERIFIED"

    pdf.set_xy(14, start_y + 3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(50, 5, "GROUNDING CONFIDENCE:")

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*score_color)
    pdf.cell(30, 5, f"{grounding_pct}%")

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*score_color)
    pdf.cell(95, 5, status_txt, align="R")

    pdf.set_xy(14, start_y + 12)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(180, 5, f"Execution Mode: {search_mode} | Claims Audited: {len(claims)} | Sources: {len(sources)}")

    pdf.set_y(start_y + 28)

    # Warning Box if present
    if warning_msg:
        pdf.set_fill_color(254, 242, 242)
        pdf.set_draw_color(248, 113, 113)
        pdf.rect(10, pdf.get_y(), 190, 12, "FD")
        pdf.set_xy(14, pdf.get_y() + 3)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(185, 28, 28)
        pdf.multi_cell(180, 4, warning_msg)
        pdf.ln(6)

    # Section 2: AI Financial Analysis Answer
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(190, 6, "AI FINANCIAL SYNTHESIS & EXECUTIVE ANALYSIS")
    pdf.ln(6)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    
    # Process line-by-line answer formatting
    for line in answer.split("\n"):
        line_clean = sanitize_text(line.strip())
        if not line_clean:
            pdf.ln(2)
            continue
        pdf.set_x(10)
        if line_clean.startswith("**") or line_clean.startswith("###"):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(190, 5, line_clean.replace("**", "").replace("###", "").strip())
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
        else:
            pdf.multi_cell(190, 5, line_clean)

    pdf.ln(6)

    # Section 3: Grounding Verification Claim Breakdown
    if claims:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(190, 6, "CLAIM-LEVEL GROUNDING VERIFICATION AUDIT")
        pdf.ln(6)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        for i, c in enumerate(claims, 1):
            claim_text = sanitize_text(c.get("claim", ""))
            supported = c.get("supported", False)
            snippet = sanitize_text(c.get("evidence_snippet", ""))

            pdf.set_x(10)
            pdf.set_font("Helvetica", "B", 8)
            if supported:
                pdf.set_text_color(22, 163, 74)
                status_label = "[VERIFIED]"
            else:
                pdf.set_text_color(220, 38, 38)
                status_label = "[UNSUPPORTED / UNVERIFIED]"

            pdf.multi_cell(190, 5, f"Claim {i} {status_label}: {claim_text}")

            if snippet and supported:
                pdf.set_x(10)
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(100, 116, 139)
                pdf.multi_cell(190, 4, f"Evidence: {snippet[:150]}...")
            pdf.ln(2)

        pdf.ln(4)

    # Section 4: Cited Primary Sources
    if sources:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(190, 6, "PRIMARY RETRIEVED SOURCES & CITATIONS")
        pdf.ln(6)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        for i, src in enumerate(sources, 1):
            title = sanitize_text(src.get("title", "Source"))
            source_name = sanitize_text(src.get("source_name", "Public Database"))
            url = sanitize_text(src.get("source_url", ""))
            snippet = sanitize_text(src.get("snippet", ""))

            pdf.set_x(10)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 58, 138)
            pdf.multi_cell(190, 5, f"[{i}] {title} - {source_name}")

            if url:
                pdf.set_x(10)
                pdf.set_font("Helvetica", "U", 8)
                pdf.set_text_color(37, 99, 235)
                pdf.multi_cell(190, 4, f"URL: {url}")

            if snippet:
                pdf.set_x(10)
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(71, 85, 105)
                pdf.multi_cell(190, 4, f"Snippet: {snippet[:180]}...")

            pdf.ln(3)

    # Save output PDF to temporary file
    temp_dir = tempfile.gettempdir()
    file_name = f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(temp_dir, file_name)
    pdf.output(file_path)
    return file_path
