"""
Generic, parameterized CV builder — deliberately contains NO hardcoded
personal data, so this file (and this whole repo) is safe to keep public.
All candidate details are passed in as arguments at call time by the
routine's own prompt (which is private to the user's claude.ai account).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem,
)
from reportlab.lib import colors


def _kv_table(rows, key_width=38 * mm):
    data = [[k, ":", v] for k, v in rows]
    t = Table(data, colWidths=[key_width, 3 * mm, None])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def build_cv(
    full_name,
    address,
    phone,
    email,
    profile_summary,
    personal_data,       # dict: e.g. {"Date of Birth": "...", "Identity Number": "...", ...} — ordered
    education,            # list of dicts: {"section": "Tertiary"|"High School", "rows": [(k,v), ...]}
    skills,               # list of str
    work_experience,      # dict: {"rows": [(k,v),...], "duty_sections": [(heading, [bullet, ...]), ...]} or None
    references,           # list of dicts: {"rows": [(k,v), ...]}
    out_path="cv.pdf",
):
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=16, alignment=TA_CENTER, spaceAfter=1 * mm)
    center = ParagraphStyle("center", parent=styles["Normal"], fontSize=9.3, alignment=TA_CENTER, spaceAfter=0.5 * mm)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=10.5, spaceBefore=4 * mm, spaceAfter=2 * mm, textTransform="uppercase")
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.6, leading=13, alignment=TA_JUSTIFY)
    subhead = ParagraphStyle("subhead", parent=styles["Normal"], fontSize=9.6, fontName="Helvetica-Bold", spaceBefore=2.5 * mm, spaceAfter=0.5 * mm)
    bullet_style = ParagraphStyle("bullet", parent=styles["Normal"], fontSize=9.6, leading=12.5)

    story = []
    story.append(Paragraph(full_name.upper(), h1))
    story.append(Paragraph(address, center))
    story.append(Paragraph(f"[Phone No: {phone} / email: {email}]", center))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.black, spaceBefore=2 * mm, spaceAfter=2 * mm))

    story.append(Paragraph("Professional Summary", h2))
    story.append(Paragraph(profile_summary, body))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=2 * mm, spaceAfter=2 * mm))

    story.append(Paragraph("Personal Data", h2))
    story.append(_kv_table(list(personal_data.items())))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=2 * mm, spaceAfter=2 * mm))

    story.append(Paragraph("Education History", h2))
    for ed in education:
        story.append(Paragraph(ed["section"], subhead))
        story.append(_kv_table(ed["rows"]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=2 * mm, spaceAfter=2 * mm))

    story.append(Paragraph("Skills", h2))
    story.append(ListFlowable(
        [ListItem(Paragraph(s, bullet_style)) for s in skills],
        bulletType="bullet", start="•", leftIndent=5 * mm,
    ))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=2 * mm, spaceAfter=2 * mm))

    if work_experience:
        story.append(Paragraph("Work Experience", h2))
        story.append(_kv_table(work_experience["rows"]))
        for heading, bullets in work_experience.get("duty_sections", []):
            story.append(Paragraph(heading, subhead))
            story.append(ListFlowable(
                [ListItem(Paragraph(b, bullet_style)) for b in bullets],
                bulletType="bullet", start="•", leftIndent=5 * mm,
            ))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=2 * mm, spaceAfter=2 * mm))

    story.append(Paragraph("References", h2))
    for ref in references:
        story.append(_kv_table(ref["rows"]))
        story.append(Spacer(1, 2 * mm))

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
    )
    doc.build(story)
    return out_path
