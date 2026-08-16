"""
Byte-perfect Gmail sender for the cloud (CCR) job-application pipeline.

Same approach as the local send_gmail.py: reads the PDF attachment from disk
in binary mode and base64-encodes it in code, never through model-generated
text, so it is byte-perfect by construction. The only difference from the
local version is where the OAuth credentials come from -- this cloud
environment has no ~/.gmail-mcp/ directory, so credentials must be supplied
as environment variables (set as secrets on the claude.ai environment used
by this routine):

    GMAIL_CLIENT_ID
    GMAIL_CLIENT_SECRET
    GMAIL_REFRESH_TOKEN

Usage as a library:
    from send_gmail_cloud import send_email
    send_email(to=..., subject=..., body_text=..., attachment_path=..., attachment_filename=...)
"""
import base64
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

TOKEN_URI = "https://oauth2.googleapis.com/token"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

REQUIRED_ENV_VARS = ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"]


def get_access_token():
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "These must be set as secrets on this environment before the "
            "pipeline can send mail."
        )

    resp = requests.post(
        TOKEN_URI,
        data={
            "client_id": os.environ["GMAIL_CLIENT_ID"],
            "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
            "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_email(to, subject, body_text, attachment_path=None, attachment_filename=None,
                cc=None, bcc=None):
    access_token = get_access_token()

    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    msg.attach(MIMEText(body_text, "plain"))

    if attachment_path:
        with open(attachment_path, "rb") as f:
            raw_bytes = f.read()
        part = MIMEApplication(raw_bytes, _subtype="pdf")
        part.add_header(
            "Content-Disposition", "attachment",
            filename=attachment_filename or os.path.basename(attachment_path),
        )
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = requests.post(
        SEND_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"raw": raw},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()
