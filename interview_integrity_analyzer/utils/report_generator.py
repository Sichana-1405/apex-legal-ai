"""
utils/report_generator.py
──────────────────────────
Generates a professional downloadable PDF report for an interview integrity assessment.
Uses fpdf2 (FPDF class) for PDF creation.

Output: bytes object (PDF content) ready for st.download_button().

NOTE: This is a prototype decision-support tool.
      All reports include a mandatory disclaimer that no hiring decision
      should be based solely on this automated assessment.
"""

from __future__ import annotations
import io
from datetime import datetime
from typing import Optional

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Color Palette
# ─────────────────────────────────────────────────────────────────────────────
COLOR = {
    "bg_dark":     (10,  14,  26),
    "bg_card":     (26,  32,  53),
    "bg_section":  (17,  24,  39),
    "accent_blue": (59,  130, 246),
    "text_white":  (241, 245, 249),
    "text_gray":   (148, 163, 184),
    "text_dark":   (30,  41,  59),
    "success":     (16,  185, 129),
    "warning":     (245, 158, 11),
    "danger":      (239, 68,  68),
    "purple":      (139, 92,  246),
    "border":      (45,  55,  72),
}

RISK_COLORS = {
    "LOW":    COLOR["success"],
    "MEDIUM": COLOR["warning"],
    "HIGH":   COLOR["danger"],
}


# ─────────────────────────────────────────────────────────────────────────────
# PDF Report Class
# ─────────────────────────────────────────────────────────────────────────────
class InterviewIntegrityReport(FPDF):
    """Custom FPDF subclass for Interview Integrity Report."""

    def __init__(self, candidate_name: str = "Unknown"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.candidate_name = candidate_name
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 15, 18)

    # ── Header (called automatically on each new page) ────────────────────────
    def header(self):
        # Header bar
        self.set_fill_color(*COLOR["bg_dark"])
        self.rect(0, 0, 210, 22, "F")
        # Logo / Title
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*COLOR["accent_blue"])
        self.set_xy(0, 6)
        self.cell(0, 10, "INTERVIEW INTEGRITY ANALYZER", align="C")
        # Subtitle
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*COLOR["text_gray"])
        self.set_xy(0, 13)
        self.cell(0, 6, "AI-Assisted Interview Risk Assessment Report  •  Decision Support Tool Only", align="C")
        # Separator line
        self.set_draw_color(*COLOR["accent_blue"])
        self.set_line_width(0.4)
        self.line(0, 22, 210, 22)
        self.ln(8)

    # ── Footer ────────────────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*COLOR["border"])
        self.set_line_width(0.2)
        self.line(18, self.get_y(), 192, self.get_y())
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*COLOR["text_gray"])
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(80, 8, f"Generated: {ts}", align="L")
        self.cell(0, 8, f"Page {self.page_no()}  |  CONFIDENTIAL — Recruiter Use Only", align="R")

    # ── Section Heading ───────────────────────────────────────────────────────
    def section_heading(self, title: str, icon: str = "▶"):
        self.ln(4)
        self.set_fill_color(*COLOR["bg_card"])
        self.set_draw_color(*COLOR["accent_blue"])
        self.set_line_width(0.5)
        # Left accent bar
        self.set_fill_color(*COLOR["accent_blue"])
        self.rect(self.get_x(), self.get_y(), 2, 8, "F")
        self.set_x(self.get_x() + 4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*COLOR["accent_blue"])
        self.cell(0, 8, f"  {icon}  {title.upper()}", ln=True)
        self.set_draw_color(*COLOR["border"])
        self.set_line_width(0.2)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(3)

    # ── Label/Value Row ───────────────────────────────────────────────────────
    def kv_row(self, label: str, value: str, value_color: Optional[tuple] = None):
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*COLOR["text_gray"])
        self.cell(52, 6, label + ":", ln=False)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*(value_color or COLOR["text_white"]))
        self.multi_cell(0, 6, value)

    # ── Body Text ─────────────────────────────────────────────────────────────
    def body_text(self, text: str, italic: bool = False):
        style = "I" if italic else ""
        self.set_font("Helvetica", style, 8.5)
        self.set_text_color(*COLOR["text_white"])
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    # ── Risk Score Box ────────────────────────────────────────────────────────
    def risk_score_box(self, score: int, level: str, summary: str):
        color = RISK_COLORS.get(level, COLOR["accent_blue"])
        y_start = self.get_y()

        # Box background
        self.set_fill_color(*COLOR["bg_card"])
        self.set_draw_color(*color)
        self.set_line_width(1)
        self.rect(18, y_start, 174, 38, "FD")

        # Big score number
        self.set_xy(18, y_start + 5)
        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*color)
        self.cell(50, 24, str(score), align="C")

        # /100 suffix
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLOR["text_gray"])
        self.set_xy(68, y_start + 19)
        self.cell(20, 8, "/ 100")

        # Risk level label
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color)
        self.set_xy(95, y_start + 5)
        self.cell(0, 10, f"{level} RISK", align="L")

        # Summary line
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLOR["text_gray"])
        self.set_xy(95, y_start + 17)
        self.multi_cell(88, 5, summary[:160])

        self.set_y(y_start + 42)

    # ── Factor Table ──────────────────────────────────────────────────────────
    def factor_table(self, factors: list):
        if not factors:
            self.body_text("No significant risk factors detected.")
            return

        # Table header
        self.set_fill_color(*COLOR["bg_section"])
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*COLOR["accent_blue"])
        self.cell(80, 6, "Risk Factor", fill=True, border=0)
        self.cell(30, 6, "Category",   fill=True, border=0)
        self.cell(22, 6, "Points",     fill=True, border=0, align="C")
        self.cell(0,  6, "Description", fill=True, border=0, ln=True)
        self.set_line_width(0.2)
        self.set_draw_color(*COLOR["border"])
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(1)

        # Rows
        for i, f in enumerate(factors):
            color = RISK_COLORS.get(
                "HIGH" if f["severity"] == "high" else
                ("MEDIUM" if f["severity"] == "medium" else "LOW"),
                COLOR["text_white"]
            )
            fill  = COLOR["bg_card"] if i % 2 == 0 else COLOR["bg_section"]
            self.set_fill_color(*fill)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*COLOR["text_white"])
            self.cell(80, 6, f["name"][:40],      fill=True, border=0)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*COLOR["text_gray"])
            self.cell(30, 6, f["category"],        fill=True, border=0)
            self.set_text_color(*color)
            self.set_font("Helvetica", "B", 8)
            self.cell(22, 6, f"+{f['score']}",     fill=True, border=0, align="C")
            self.set_text_color(*COLOR["text_white"])
            self.set_font("Helvetica", "", 7.5)
            self.multi_cell(0, 6, f["description"][:80], fill=True, border=0)


# ─────────────────────────────────────────────────────────────────────────────
# Report Builder Function
# ─────────────────────────────────────────────────────────────────────────────
def generate_pdf_report(
    candidate_name:   str,
    resume_text:      str,
    question:         str,
    answer:           str,
    transcript_notes: str,
    behavioral_obs:   dict,
    analysis_result:  dict,
    risk_result:      dict,
) -> bytes:
    """
    Build and return a complete PDF report as bytes.

    Parameters map directly to st.session_state keys collected across the app flow.
    Returns bytes on success, or a minimal error PDF on failure.
    """
    if not FPDF_AVAILABLE:
        return _error_bytes("fpdf2 not installed. Run: pip install fpdf2")

    try:
        pdf = InterviewIntegrityReport(candidate_name=candidate_name)
        pdf.add_page()

        # ── Cover / Summary Card ──────────────────────────────────────────
        _cover_section(pdf, candidate_name, risk_result)

        # ── Candidate & Resume ────────────────────────────────────────────
        pdf.section_heading("Candidate Resume Summary", "📄")
        resume_preview = resume_text[:1800].replace("\r", "")
        if len(resume_text) > 1800:
            resume_preview += "\n\n[... resume truncated for report length ...]"
        pdf.body_text(resume_preview)

        # ── Interview Details ─────────────────────────────────────────────
        pdf.section_heading("Interview Details", "💬")
        pdf.kv_row("Question", question)
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*COLOR["text_gray"])
        pdf.cell(0, 6, "Candidate Answer:", ln=True)
        pdf.body_text(answer[:1200] or "No answer recorded.")
        if transcript_notes:
            pdf.kv_row("Transcript Notes", transcript_notes[:400])

        # ── Behavioral Observations ───────────────────────────────────────
        pdf.section_heading("Behavioral Observations", "👁️")
        obs_labels = {
            "eye_contact":        "Eye Contact",
            "lip_sync":           "Lip Sync",
            "voice_behaviour":    "Voice Behaviour",
            "prompting_detected": "Prompting Detected",
        }
        for key, label in obs_labels.items():
            val = behavioral_obs.get(key, "Not recorded")
            pdf.kv_row(label, val)

        # ── AI Analysis ───────────────────────────────────────────────────
        pdf.section_heading("AI Analysis (Gemini 2.5 Flash)", "🤖")
        api_badge = "✓ Gemini API Used" if analysis_result.get("_api_used") else "⚠ Fallback Mode"
        pdf.kv_row("Analysis Mode", api_badge)
        pdf.kv_row("Skill Match", f"{analysis_result.get('skill_match_percentage', 'N/A')}%")
        pdf.kv_row("Technical Depth", analysis_result.get("technical_depth", "N/A"))
        pdf.kv_row("Confidence Score", f"{analysis_result.get('confidence_score', 'N/A')}%")
        pdf.ln(2)

        missing = analysis_result.get("missing_skills", [])
        if missing:
            pdf.kv_row("Missing Skills", ", ".join(missing[:6]))

        verified   = analysis_result.get("resume_claims_verified", [])
        unverified = analysis_result.get("resume_claims_unverified", [])
        if verified:
            pdf.kv_row("Claims Verified", "; ".join(verified[:4]))
        if unverified:
            pdf.kv_row("Claims Unverified", "; ".join(unverified[:4]), value_color=COLOR["warning"])

        pdf.ln(2)
        observations = analysis_result.get("key_observations", [])
        if observations:
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(*COLOR["text_gray"])
            pdf.cell(0, 6, "Key Observations:", ln=True)
            for obs in observations[:5]:
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(*COLOR["text_white"])
                pdf.cell(6, 5.5, "•")
                pdf.multi_cell(0, 5.5, obs)

        # ── AI Explanation ────────────────────────────────────────────────
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*COLOR["accent_blue"])
        pdf.cell(0, 6, "AI Assessment Explanation:", ln=True)
        pdf.set_fill_color(*COLOR["bg_card"])
        pdf.set_draw_color(*COLOR["purple"])
        pdf.set_line_width(0.5)
        x, y = pdf.get_x(), pdf.get_y()
        explanation = analysis_result.get("ai_explanation", "No explanation available.")
        pdf.multi_cell(0, 6, explanation, border=0)

        # ── Risk Score ────────────────────────────────────────────────────
        pdf.section_heading("Risk Assessment", "⚠️")
        pdf.risk_score_box(
            score   = risk_result.get("risk_score", 0),
            level   = risk_result.get("risk_level", "LOW"),
            summary = risk_result.get("summary_line", ""),
        )

        # ── Factor Breakdown ──────────────────────────────────────────────
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*COLOR["text_gray"])
        pdf.cell(0, 6, "Risk Factor Breakdown:", ln=True)
        pdf.ln(2)
        factors_raw = [
            {
                "name":        f.name if hasattr(f, "name") else f.get("name", ""),
                "category":    f.category if hasattr(f, "category") else f.get("category", ""),
                "score":       f.score if hasattr(f, "score") else f.get("score", 0),
                "description": f.description if hasattr(f, "description") else f.get("description", ""),
                "severity":    f.severity if hasattr(f, "severity") else f.get("severity", "low"),
            }
            for f in risk_result.get("factors", [])
        ]
        pdf.factor_table(factors_raw)

        # ── Recommendation ────────────────────────────────────────────────
        pdf.section_heading("Recommendation", "📋")
        recommendation = risk_result.get("recommendation", "No recommendation generated.")
        pdf.body_text(recommendation)

        # ── Disclaimer ────────────────────────────────────────────────────
        pdf.ln(4)
        pdf.section_heading("Important Disclaimer", "⚖️")
        disclaimer = (
            "This report is generated by an AI-assisted prototype decision-support tool developed for "
            "the TCS Tech Day Hackathon. It is intended to assist recruiters in identifying potential "
            "inconsistencies — it does NOT make hiring decisions, nor does it constitute legal, "
            "professional, or binding HR advice. All conclusions must be reviewed by a qualified human "
            "recruiter. No candidate should be rejected based solely on this automated output. "
            "This tool does not perform real deepfake detection, facial recognition, or voice "
            "biometric analysis."
        )
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*COLOR["text_gray"])
        pdf.multi_cell(0, 5.5, disclaimer)

        # ── Output ────────────────────────────────────────────────────────
        return bytes(pdf.output())

    except Exception as e:
        return _error_bytes(f"Report generation failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _cover_section(pdf: InterviewIntegrityReport, name: str, risk_result: dict):
    """Render the cover summary section."""
    level = risk_result.get("risk_level", "LOW")
    score = risk_result.get("risk_score", 0)
    color = RISK_COLORS.get(level, COLOR["accent_blue"])

    # Title block
    pdf.set_fill_color(*COLOR["bg_card"])
    pdf.rect(18, pdf.get_y(), 174, 50, "F")
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.8)
    pdf.rect(18, pdf.get_y(), 174, 50)

    # Candidate name
    pdf.set_xy(22, pdf.get_y() + 6)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*COLOR["text_white"])
    pdf.cell(0, 10, name, ln=True)

    # Report type
    pdf.set_x(22)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COLOR["text_gray"])
    pdf.cell(0, 7, "Interview Integrity Assessment Report", ln=True)

    # Score summary
    pdf.set_x(22)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*color)
    pdf.cell(0, 7, f"Risk Level: {level}  |  Score: {score}/100", ln=True)

    # Timestamp
    pdf.set_x(22)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR["text_gray"])
    pdf.cell(0, 7, f"Report Date: {datetime.now().strftime('%d %B %Y, %H:%M')}", ln=True)

    pdf.set_y(pdf.get_y() + 8)


def _error_bytes(msg: str) -> bytes:
    """Generate a minimal PDF with an error message."""
    if not FPDF_AVAILABLE:
        return msg.encode()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(239, 68, 68)
    pdf.cell(0, 10, "Report Generation Error", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 8, msg)
    return bytes(pdf.output())
