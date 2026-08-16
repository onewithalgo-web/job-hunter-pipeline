# job-hunter-pipeline

Generic Z83 (South African public-service job application form) builder and
byte-perfect Gmail sender, used by an automated weekly job-application
routine. This repo is intentionally **public and contains no personal data**
— every candidate-specific value (name, ID number, contact details,
CV content, etc.) is passed in as a function argument at call time by the
routine's own prompt, which is private to the routine owner's account.

## Files

- `z83_overlay.py` — fills the real official Z83 form (`z83_blank_official.pdf`)
  via a precise reportlab overlay, and merges it with a CV PDF into one
  combined application PDF. Call `z83_overlay.build(..., profile={...})` —
  see the docstring on `build()` for the full shape of `profile`.
- `z83_blank_official.pdf` — the real DPSA Z83 form background (a blank
  public government form, not personal data).
- `build_cv.py` — generic, parameterized CV builder. Call
  `build_cv.build_cv(full_name=..., address=..., ..., out_path="cv.pdf")`.
- `send_gmail_cloud.py` — sends a built PDF via the Gmail API directly in
  code (byte-perfect, no model transcription of the binary attachment).
  Requires three environment secrets set on whichever cloud environment
  runs this:
  - `GMAIL_CLIENT_ID`
  - `GMAIL_CLIENT_SECRET`
  - `GMAIL_REFRESH_TOKEN`

## Usage

```python
from build_cv import build_cv
from send_gmail_cloud import send_email
import z83_overlay

cv_path = build_cv(
    full_name="...", address="...", phone="...", email="...",
    profile_summary="...", personal_data={...}, education=[...],
    skills=[...], work_experience={...}, references=[...],
    out_path="cv.pdf",
)

pdf_path = z83_overlay.build(
    position="...", department="...", reference="...",
    start_availability="Available immediately", date_str="DD/MM/YYYY",
    profile={...},          # see z83_overlay.build docstring
    cv_pdf_path=cv_path,
    out_name="Application_XXXX.pdf",
)

send_email(to="...", subject="...", body_text="...",
           attachment_path=pdf_path, attachment_filename="Application_XXXX.pdf")
```

All candidate values (`profile` dicts, name, contact details, CV content)
are supplied by the caller at runtime — never hardcode real personal data
into these files, since this repo is public.
