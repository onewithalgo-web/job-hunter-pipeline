#!/usr/bin/env python3
"""Fill the REAL official Z83 blank PDF via a precise text/checkbox overlay:
small square checkboxes (X = selected, empty = not) after every option,
individual digit boxes for ID/Passport numbers, and Surname/Full names
stacked as two rows to the right of the shared label.

This module is deliberately generic — it contains NO hardcoded personal
data. All candidate-specific values (name, ID number, DOB, references,
education, etc.) are passed in via the `profile` dict argument to build(),
so this file is safe to keep in a public repo. The caller (the routine's
own prompt, which is private) supplies `profile` at call time."""
import io
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from pypdf import PdfReader, PdfWriter

PAGE_W, PAGE_H = 612, 792

def y(top):
    """Convert pdfplumber 'top' (distance from top of page) to reportlab y (from bottom)."""
    return PAGE_H - top

def make_overlay(draw_fn):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    draw_fn(c)
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]

def text(c, x, top, s, size=7.6, font="Helvetica", bold=False):
    c.setFont("Helvetica-Bold" if bold else font, size)
    c.setFillColor(black)
    c.drawString(x, y(top) - size*0.8, s)

def text_center(c, cx, top, bottom, s, size=8, bold=True):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.setFillColor(black)
    w = c.stringWidth(s, "Helvetica-Bold" if bold else "Helvetica", size)
    baseline = (y(top) + y(bottom)) / 2 - size * 0.35
    c.drawString(cx - w/2, baseline, s)

def checkbox(c, x1, top, bottom, checked, size=9.5, gap=4):
    """Draw a small square checkbox right after a word (x1 = word's right edge),
    vertically centered on the word, with a bold X inside if checked."""
    cy_top = (top + bottom) / 2 - size/2
    box_x = x1 + gap
    box_y = y(cy_top + size)
    c.setLineWidth(0.8)
    c.rect(box_x, box_y, size, size)
    if checked:
        c.setLineWidth(1.3)
        pad = 1.6
        c.line(box_x+pad, box_y+pad, box_x+size-pad, box_y+size-pad)
        c.line(box_x+pad, box_y+size-pad, box_x+size-pad, box_y+pad)

def digit_boxes(c, dividers, top, bottom, s, size=8):
    """Place each character of s centered in successive grid cells defined by dividers."""
    for i, ch in enumerate(s):
        if i >= len(dividers) - 1:
            break
        cx = (dividers[i] + dividers[i+1]) / 2
        text_center(c, cx, top, bottom, ch, size=size, bold=True)

# Digit-grid column boundaries shared by the Identity Number / Passport number rows
ID_GRID = [403.0, 421.0, 434.6, 448.0, 459.8, 475.1, 488.9, 501.7, 514.5, 527.3, 540.1, 552.9, 565.7, 578.6]

def build(position, department, reference, start_availability, date_str, profile,
          out_name="application.pdf", tmp_dir=None,
          background_pdf=None, cv_pdf_path=None):
    """
    profile: dict with the candidate's personal data. Required keys:
      surname, full_names, dob (DD/MM/YYYY), id_number, passport_number ("N/A" if none),
      race ("african"|"white"|"coloured"|"indian"|"other"), gender ("male"|"female"),
      disability (bool), sa_citizen (bool), nationality (str, "N/A" if sa_citizen),
      work_permit (bool), criminal_offence (bool), pending_criminal_case (bool),
      dismissed_misconduct (bool), pending_disciplinary (bool), resigned_pending_disciplinary (bool),
      discharged_ill_health (bool), conducting_business_with_state (bool),
      relinquish_business_interests (bool),
      years_experience_private (str), years_experience_public (str),
      registration_date (str, "N/A" if none), registration_number (str, "N/A" if none),
      initials (str),
      preferred_language (str), correspondence_method ("post"|"email"|"fax"|"telephone"),
      email (str), phone (str),
      languages: list of (name, speak_rating, write_rating) tuples, up to 2,
      qualifications: list of (institution, qualification, year) tuples, up to 3,
      other_registration (str, "N/A" if none),
      work_experience: dict {employer_line1, employer_line2 (optional), position,
        month (MM), year (YY), status} or None if no experience yet,
      previously_employed (bool),
      references: list of (name, position, phone) tuples, up to 2,
      signature_name (str)
    """
    import os
    BASE = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = tmp_dir or BASE
    background_pdf = background_pdf or os.path.join(BASE, "z83_blank_official.pdf")

    def wrap(s, width):
        import textwrap
        return textwrap.wrap(s, width) or [""]

    def yn(c_, x_yes, x_no, top, bottom, value):
        checkbox(c_, x_yes, top, bottom, bool(value))
        checkbox(c_, x_no, top, bottom, not value)

    # ---------- PAGE 1 ----------
    def draw_page1(c):
        # Section A
        for i, line in enumerate(wrap(position, 40)):
            text(c, 245, 143 + i*9, line, bold=True)
        for i, line in enumerate(wrap(department, 26)):
            text(c, 411, 143 + i*9, line, bold=True)
        for i, line in enumerate(wrap(reference, 40)):
            text(c, 245, 202 + i*9, line, bold=True)
        for i, line in enumerate(wrap(start_availability, 26)):
            text(c, 411, 202 + i*9, line, bold=True)

        # Section B - Surname / Full names: stacked as two rows to the right of the label
        text(c, 354, 271, profile["surname"], size=7.6, bold=True)
        text(c, 354, 284, profile["full_names"], size=7.6, bold=True)

        # DOB
        text(c, 288, 320, profile["dob"], size=7, bold=True)
        # Identity Number - one digit per grid box
        digit_boxes(c, ID_GRID, 293.4, 311.9, profile["id_number"])
        # Passport number - N/A across the first grid boxes
        digit_boxes(c, ID_GRID, 312.1, 330.85, profile.get("passport_number", "N/A"))

        # Race -> checkbox after each option
        race = profile["race"]
        checkbox(c, 314.7, 335.2, 343.3, race == "african")
        checkbox(c, 376.5, 335.2, 343.3, race == "white")
        checkbox(c, 443.8, 335.2, 343.3, race == "coloured")
        checkbox(c, 506.5, 335.2, 343.3, race == "indian", size=8, gap=1.5)  # narrow sub-column, avoid divider
        checkbox(c, 559.4, 335.2, 343.3, race == "other")

        # Gender
        gender = profile["gender"]
        checkbox(c, 508.1, 350.5, 358.5, gender == "female", size=8, gap=1.5)  # narrow sub-column, avoid divider
        checkbox(c, 557.3, 350.5, 358.5, gender == "male")

        # Disability
        yn(c, 501.5, 553.8, 365.8, 373.9, profile["disability"])
        # SA citizen
        yn(c, 501.5, 553.8, 381.1, 389.1, profile["sa_citizen"])
        # Nationality (blank, N/A if sa_citizen)
        text(c, 478, 399, profile.get("nationality", "N/A"), size=7)
        # Work permit
        yn(c, 501.5, 553.8, 411.7, 419.7, profile["work_permit"])
        # Criminal offence
        yn(c, 501.5, 553.8, 424.3, 432.3, profile["criminal_offence"])
        # Pending criminal case
        yn(c, 501.5, 553.8, 454.9, 462.9, profile["pending_criminal_case"])
        # Dismissed misconduct
        yn(c, 501.5, 553.8, 485.5, 493.5, profile["dismissed_misconduct"])
        # Pending disciplinary case
        yn(c, 501.5, 553.8, 520.0, 528.1, profile["pending_disciplinary"])
        # Resigned pending disciplinary
        yn(c, 501.5, 553.8, 550.6, 558.7, profile["resigned_pending_disciplinary"])
        # Discharged/retired ill-health
        yn(c, 501.5, 553.8, 592.2, 600.2, profile["discharged_ill_health"])
        # Conducting business with State
        yn(c, 501.5, 553.8, 620.3, 628.3, profile["conducting_business_with_state"])
        # Relinquish business interests
        yn(c, 501.5, 553.8, 657.6, 665.6, profile["relinquish_business_interests"])

        # Years experience Private / Public
        text(c, 478, 708, profile["years_experience_private"], size=7)
        text(c, 525, 708, profile["years_experience_public"], size=7)
        # Registration date / reg no
        text(c, 484, 737, profile.get("registration_date", "N/A"), size=7)
        text(c, 532, 737, profile.get("registration_number", "N/A"), size=7)

        # Initial (bottom right)
        text(c, 553, 764, profile["initials"], size=8, bold=True)

    # ---------- PAGE 2 ----------
    def draw_page2(c):
        # Preferred language
        text(c, 245, 88, profile["preferred_language"], bold=True)
        # Method for correspondence -> checkbox after each option
        method = profile["correspondence_method"]
        checkbox(c, 369.2, 106.8, 114.9, method == "post")
        checkbox(c, 437.8, 106.8, 114.9, method == "email")
        checkbox(c, 495.8, 106.8, 114.9, method == "fax")
        checkbox(c, 569.6, 106.8, 114.9, method == "telephone", size=6.5, gap=1.2)  # narrow cell, avoid divider
        # Contact details - a stray vertical grid line runs through this cell at x~327,
        # so start the value past it to avoid the text being sliced by the line.
        text(c, 333, 148, profile["email"], size=7.4, bold=True)
        text(c, 333, 160, profile["phone"], size=7.4, bold=True)

        # Section D languages - up to 2 sit inside the shaded gray strip
        # (top=213.86 to bottom=223.10 on the real form), side by side, with
        # Speak / Write-or-read ratings in the rows below each.
        langs = profile["languages"]
        lang_x = [214, 286]
        rating_x = [212, 283]
        for i, (name, speak, write) in enumerate(langs[:2]):
            text(c, lang_x[i], 215.5, name, size=7, bold=True)
            text(c, rating_x[i], 225.5, speak, size=7.6, bold=True)
            text(c, rating_x[i], 244.5, write, size=7.6, bold=True)

        # Section E qualifications (up to 3 rows)
        quals = profile["qualifications"]
        qual_tops = [312, 332, 352]
        for i, (institution, qualification, yr) in enumerate(quals[:3]):
            top = qual_tops[i]
            text(c, 84.6, top, institution, size=7.4)
            text(c, 304.4, top, qualification, size=7.4)
            text(c, 488.6, top, yr, size=7.4)
        text(c, 280, 382.9, profile.get("other_registration", "N/A"), size=7.4)

        # Section F work experience.
        # The MM/YY sub-header sits in the row right above (top~442.3); the actual data
        # row is the next one down (450.4-469.4), so the entry goes there to avoid it.
        we = profile.get("work_experience")
        if we:
            text(c, 84.6, 452, we["employer_line1"], size=7, bold=True)
            if we.get("employer_line2"):
                text(c, 84.6, 461, we["employer_line2"], size=6.6)
            text(c, 224.1, 456, we["position"], size=7.4)
            text_center(c, 334, 450.4, 469.4, we["month"], size=7, bold=False)
            text_center(c, 366, 450.4, 469.4, we["year"], size=7, bold=False)
            text(c, 444.7, 456, we["status"], size=7)
        # previously employed
        yn(c, 458.9, 493.7, 513.1, 521.1, profile["previously_employed"])

        # Section G references (up to 2)
        refs = profile["references"]
        ref_tops = [595, 615]
        for i, (name, pos, phone) in enumerate(refs[:2]):
            top = ref_tops[i]
            text(c, 84.6, top, name, size=7.4)
            text(c, 234.7, top, pos, size=7.4)
            text(c, 384.7, top, phone, size=7.4)

        # Signature / Date
        text(c, 140, 697.4, profile["signature_name"], bold=True)
        text(c, 345, 697.4, date_str, bold=True)

        # Initial (bottom right)
        text(c, 553, 764, profile["initials"], size=8, bold=True)

    bg = PdfReader(background_pdf)
    ov1 = make_overlay(draw_page1)
    ov2 = make_overlay(draw_page2)

    writer = PdfWriter()
    p1 = bg.pages[0]
    p1.merge_page(ov1)
    writer.add_page(p1)
    p2 = bg.pages[1]
    p2.merge_page(ov2)
    writer.add_page(p2)

    if cv_pdf_path:
        for p in PdfReader(cv_pdf_path).pages:
            writer.add_page(p)

    out_path = os.path.join(tmp_dir, out_name)
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path

def compact_for_email(pdf_path, out_path, z83_page_count=2, dpi=72):
    """Rasterize only the Z83 pages (which carry the government form's heavy
    embedded font subsets) at a modest DPI to keep the email attachment small,
    while leaving the CV pages (already lightweight, text-based) untouched."""
    import pdfplumber
    from pypdf import PdfReader, PdfWriter
    import io

    src = pdfplumber.open(pdf_path)
    imgs = []
    for page in src.pages[:z83_page_count]:
        im = page.to_image(resolution=dpi).original.convert("L")
        im = im.point(lambda x: 0 if x < 200 else 255, mode="1")
        imgs.append(im)

    buf = io.BytesIO()
    imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:])
    buf.seek(0)
    z83_raster = PdfReader(buf)

    writer = PdfWriter()
    for p in z83_raster.pages:
        writer.add_page(p)
    orig = PdfReader(pdf_path)
    for p in orig.pages[z83_page_count:]:
        writer.add_page(p)
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path
