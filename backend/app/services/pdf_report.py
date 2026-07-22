"""
PDF Report Generation Service
================================
Generates a PDF evaluation report using ReportLab.
Falls back gracefully if ReportLab is not available.
"""
from typing import Optional
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.models.evaluation import Evaluation

# CARE palette
COLOR_CARE_C = colors.HexColor("#6366F1")
COLOR_CARE_A = colors.HexColor("#10B981")
COLOR_CARE_R = colors.HexColor("#F59E0B")
COLOR_CARE_E = colors.HexColor("#3B82F6")
COLOR_BG = colors.HexColor("#0A0F1E")
COLOR_CARD = colors.HexColor("#1E293B")
COLOR_BORDER = colors.HexColor("#2D3748")
COLOR_TEXT = colors.HexColor("#E2E8F0")
COLOR_MUTED = colors.HexColor("#94A3B8")


def _score_color(score: Optional[float]) -> colors.HexColor:
    if score is None:
        return colors.HexColor("#64748B")
    if score >= 90:
        return colors.HexColor("#10B981")
    if score >= 80:
        return colors.HexColor("#3B82F6")
    if score >= 70:
        return colors.HexColor("#F59E0B")
    return colors.HexColor("#EF4444")


def generate_pdf_report(ev: Evaluation) -> bytes:
    """
    Generate a PDF evaluation report for a single Evaluation record.
    Returns bytes of the PDF.
    """
    if not REPORTLAB_AVAILABLE:
        # Return a minimal placeholder PDF if reportlab is missing
        raise RuntimeError("ReportLab is not installed. Run: pip install reportlab")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "title",
        fontSize=22,
        textColor=colors.white,
        spaceAfter=4,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        backColor=COLOR_BG,
    )
    sub_style = ParagraphStyle(
        "subtitle",
        fontSize=11,
        textColor=COLOR_MUTED,
        spaceAfter=12,
        fontName="Helvetica",
        alignment=TA_CENTER,
    )

    story.append(Paragraph("CARE Evaluation Report", title_style))
    story.append(Paragraph(f"{ev.agent_name} — {ev.agent_type}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=12))

    # ── Score Summary ─────────────────────────────────────────────────────────
    score_color = _score_color(ev.care_score)

    summary_data = [
        ["CARE Score", "Recommendation", "Evaluator", "Date"],
        [
            f"{ev.care_score:.1f}/100" if ev.care_score is not None else "N/A",
            ev.recommendation or "N/A",
            ev.evaluator or "—",
            ev.created_at.strftime("%Y-%m-%d") if ev.created_at else "—",
        ],
    ]
    summary_table = Table(summary_data, colWidths=["25%", "30%", "22%", "23%"])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD),
        ("BACKGROUND", (0, 1), (-1, 1), COLOR_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_MUTED),
        ("TEXTCOLOR", (0, 1), (0, 1), score_color),
        ("TEXTCOLOR", (1, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (0, 1), 16),
        ("FONTSIZE", (1, 1), (-1, 1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [COLOR_CARD, COLOR_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # ── Dimension Scores ──────────────────────────────────────────────────────
    dim_header = ParagraphStyle("dim_h", fontSize=13, textColor=colors.white,
                                 fontName="Helvetica-Bold", spaceAfter=6)
    story.append(Paragraph("Dimension Scores", dim_header))

    dim_data = [["Dimension", "Score", "Weight", "Status"]]
    dims = [
        ("Computational Intelligence", ev.score_c, ev.weight_c, COLOR_CARE_C),
        ("Accuracy", ev.score_a, ev.weight_a, COLOR_CARE_A),
        ("Reliability", ev.score_r, ev.weight_r, COLOR_CARE_R),
        ("Economics", ev.score_e, ev.weight_e, COLOR_CARE_E),
    ]
    dim_style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    for i, (label, score, weight, color) in enumerate(dims, start=1):
        status = "Excellent" if score and score >= 90 else "Good" if score and score >= 80 else "Fair" if score and score >= 70 else "Needs Work"
        dim_data.append([
            label,
            f"{score:.1f}" if score is not None else "—",
            f"{weight * 100:.0f}%",
            status,
        ])
        dim_style_cmds.append(("TEXTCOLOR", (0, i), (0, i), color))
        dim_style_cmds.append(("TEXTCOLOR", (1, i), (1, i), _score_color(score)))
        dim_style_cmds.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
        dim_style_cmds.append(("BACKGROUND", (0, i), (-1, i), COLOR_BG if i % 2 else COLOR_CARD))
        dim_style_cmds.append(("TEXTCOLOR", (2, i), (3, i), COLOR_MUTED))

    dim_table = Table(dim_data, colWidths=["40%", "20%", "20%", "20%"])
    dim_table.setStyle(TableStyle(dim_style_cmds))
    story.append(dim_table)
    story.append(Spacer(1, 16))

    # ── Description ───────────────────────────────────────────────────────────
    if ev.description:
        story.append(Paragraph("Description", dim_header))
        desc_style = ParagraphStyle("desc", fontSize=10, textColor=COLOR_MUTED,
                                     fontName="Helvetica", spaceAfter=12,
                                     leading=14)
        story.append(Paragraph(ev.description, desc_style))

    # ── Strengths & Weaknesses ────────────────────────────────────────────────
    if ev.strengths or ev.weaknesses:
        story.append(Paragraph("Strengths & Weaknesses", dim_header))
        sw_data = [["Strengths ✓", "Weaknesses ✗"]]
        strengths = ev.strengths or []
        weaknesses = ev.weaknesses or []
        max_len = max(len(strengths), len(weaknesses), 1)
        for i in range(max_len):
            sw_data.append([
                strengths[i] if i < len(strengths) else "",
                weaknesses[i] if i < len(weaknesses) else "",
            ])

        sw_table = Table(sw_data, colWidths=["50%", "50%"])
        sw_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#052e16")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#450a0a")),
            ("TEXTCOLOR", (0, 0), (0, 0), COLOR_CARE_A),
            ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#F87171")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (0, -1), COLOR_TEXT),
            ("TEXTCOLOR", (1, 1), (1, -1), COLOR_TEXT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_BG),
        ]))
        story.append(sw_table)
        story.append(Spacer(1, 12))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=16))
    footer_style = ParagraphStyle("footer", fontSize=8, textColor=COLOR_MUTED,
                                   fontName="Helvetica", alignment=TA_CENTER)
    story.append(Paragraph(
        f"Generated by CARE Evaluator · {ev.created_at.strftime('%Y-%m-%d %H:%M UTC') if ev.created_at else 'N/A'}",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
