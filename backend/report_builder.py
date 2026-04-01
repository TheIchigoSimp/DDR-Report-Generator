import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib import colors

SEVERITY_COLORS = {
    "Critical": HexColor("#DC2626"),
    "High": HexColor("#EA580C"),
    "Moderate": HexColor("#CA8A04"),
    "Low": HexColor("#16A34A"),
}

def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=HexColor("#1E293B"),
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=HexColor("#64748B"),
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceBefore=20,
        spaceAfter=8,
        textColor=HexColor("#1E40AF"),
        borderWidth=1,
        borderColor=HexColor("#DBEAFE"),
        borderPadding=(0, 0, 4, 0),
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceBefore=12,
        spaceAfter=4,
        textColor=HexColor("#334155"),
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        textColor=HexColor("#374151"),
    ))
    styles.add(ParagraphStyle(
        name="Disclaimer",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        spaceAfter=16,
        textColor=HexColor("#94A3B8"),
    ))
    styles.add(ParagraphStyle(
        name="BulletItem",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=4,
        textColor=HexColor("#374151"),
        bulletIndent=8,
        bulletFontName="Helvetica",
    ))
    return styles

def _add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#94A3B8"))
    canvas.drawCentredString(
        A4[0] / 2, 15 * mm,
        f"DDR Report — Page {doc.page} — Generated {datetime.now().strftime('%d %B %Y')}"
    )
    canvas.restoreState()

def build_pdf_report(ddr_data: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
    )
    styles = _get_styles()
    story = []
    story.append(Spacer(1, 30))
    story.append(Paragraph("Detailed Diagnostic Report", styles["ReportTitle"]))
    story.append(Paragraph("(DDR)", styles["ReportTitle"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}",
        styles["ReportSubtitle"]
    ))
    story.append(HRFlowable(
        width="80%", thickness=1, color=HexColor("#DBEAFE"),
        spaceBefore=10, spaceAfter=10
    ))
    story.append(Paragraph(
        "⚠ This report was generated using AI-powered analysis. "
        "All observations are derived from the provided inspection and thermal reports. "
        "This should be reviewed by a qualified professional before taking action.",
        styles["Disclaimer"]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Property Issue Summary", styles["SectionHeader"]))
    summary = ddr_data.get("property_issue_summary", "Not Available")
    story.append(Paragraph(summary, styles["BodyText2"]))

    story.append(Paragraph("2. Area-wise Observations", styles["SectionHeader"]))
    observations = ddr_data.get("observations", [])
    if not observations:
        story.append(Paragraph("No observations available.", styles["BodyText2"]))
    else:
        for i, obs in enumerate(observations, 1):
            area = obs.get("area", "Unknown Area")
            observation = obs.get("observation", "No details.")
            source = obs.get("source", "N/A").capitalize()
            story.append(Paragraph(f"2.{i} {area}", styles["SubHeader"]))
            story.append(Paragraph(
                f"<b>Source:</b> {source} Report &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<b>Finding:</b> {observation}",
                styles["BodyText2"]
            ))

            matched = obs.get("matched_images", [])
            if matched:
                for img_info in matched[:2]:
                    img_path = img_info.get("path", "")
                    if os.path.exists(img_path):
                        try:
                            img = Image(img_path, width=3.5 * inch, height=2.5 * inch)
                            img.hAlign = "CENTER"
                            story.append(Spacer(1, 6))
                            story.append(img)
                            story.append(Paragraph(
                                f"<i>Image from page {img_info.get('page', '?')}</i>",
                                styles["Disclaimer"]
                            ))
                        except Exception:
                            story.append(Paragraph(
                                "[Image could not be loaded]", styles["Disclaimer"]
                            ))
            else:
                story.append(Spacer(1, 4))
                story.append(Paragraph(
                    "<font color='#94A3B8'>[No matching image available for this observation]</font>",
                    styles["BodyText2"]
                ))

            story.append(Spacer(1, 8))

    story.append(Paragraph("3. Probable Root Cause", styles["SectionHeader"]))
    root_cause = ddr_data.get("probable_root_cause", "Not Available")
    story.append(Paragraph(root_cause, styles["BodyText2"]))

    story.append(Paragraph("4. Severity Assessment", styles["SectionHeader"]))
    severity = ddr_data.get("severity_assessment", {})
    level = severity.get("level", "Not Available")
    reasoning = severity.get("reasoning", "No reasoning provided.")
    badge_color = SEVERITY_COLORS.get(level, HexColor("#6B7280"))

    badge_data = [[Paragraph(
        f"<b>{level.upper()}</b>",
        ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=12,
                       textColor=colors.white, alignment=TA_CENTER)
    )]]

    badge_table = Table(badge_data, colWidths=[120])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Reasoning:</b> {reasoning}", styles["BodyText2"]))

    story.append(Paragraph("5. Recommended Actions", styles["SectionHeader"]))
    actions = ddr_data.get("recommended_actions", [])
    if actions:
        for idx, action in enumerate(actions, 1):
            story.append(Paragraph(f"{idx}. {action}", styles["BulletItem"]))
    else:
        story.append(Paragraph("No recommendations available.", styles["BodyText2"]))

    story.append(Paragraph("6. Additional Notes", styles["SectionHeader"]))
    notes = ddr_data.get("additional_notes", "Not Available")
    story.append(Paragraph(notes, styles["BodyText2"]))

    story.append(Paragraph("7. Missing or Unclear Information", styles["SectionHeader"]))
    missing = ddr_data.get("missing_or_unclear_info", [])
    if missing:
        for item in missing:
            story.append(Paragraph(f"• {item}", styles["BulletItem"]))
    else:
        story.append(Paragraph("No missing information flagged.", styles["BodyText2"]))

    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
    print(f"[report_builder] PDF saved to: {output_path}")

if __name__ == "__main__":
    test_data = {
        "property_issue_summary": "The flat shows signs of moisture ingress on the north wall and bathroom ceiling. Thermal imaging confirms temperature differentials consistent with water damage.",
        "observations": [
            {"area": "Bedroom - North Wall", "observation": "Visible cracks with moisture staining", "image_hint": "crack wall", "source": "both", "matched_images": []},
            {"area": "Bathroom - Ceiling", "observation": "Water stains and discoloration", "image_hint": "water ceiling", "source": "inspection", "matched_images": []},
        ],
        "probable_root_cause": "Likely waterproofing failure at the terrace level, causing water to seep through to lower floors.",
        "severity_assessment": {"level": "High", "reasoning": "Active moisture ingress can lead to structural degradation if not addressed."},
        "recommended_actions": [
            "Inspect terrace waterproofing membrane for breaches",
            "Apply fresh waterproofing treatment on terrace",
            "Repair and repaint affected interior walls after source is fixed"
        ],
        "additional_notes": "The inspection score of 85.71% suggests the property is generally in acceptable condition, but the flagged moisture issue needs prompt attention.",
        "missing_or_unclear_info": [
            "Exact age and condition of the waterproofing membrane",
            "History of previous leakage or repair work"
        ]
    }
    
    build_pdf_report(test_data, "test_ddr_output.pdf")
    print("Done! Check test_ddr_output.pdf")