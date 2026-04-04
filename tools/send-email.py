#!/usr/bin/env python3
"""
Send a markdown research/outreach file as a formatted HTML email
with the original .md attached.

Usage:
    python tools/send-email.py \
        --to "recipient@example.com" \
        --subject "Account Research: Cyera" \
        --file "output/research/icp-a-suite/cyera.md"

    python tools/send-email.py \
        --to "recipient@example.com" \
        --cc "colleague@example.com" \
        --subject "Account Research: Cyera" \
        --file "output/research/icp-a-suite/cyera.md"
"""

import argparse
import json
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

import markdown

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "email-config.json"

HTML_WRAPPER = """\
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
  h1 {{ color: #111; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
  h2 {{ color: #333; margin-top: 28px; }}
  h3 {{ color: #555; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background-color: #f5f5f5; font-weight: 600; }}
  tr:nth-child(even) {{ background-color: #fafafa; }}
  blockquote {{ border-left: 3px solid #ccc; margin: 16px 0; padding: 8px 16px; color: #555; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }}
  strong {{ color: #111; }}
</style>
</head>
<body>
{content}
<hr>
<p style="color: #999; font-size: 0.85em;">Sent via GTM Agent. Original markdown file attached.</p>
</body>
</html>
"""


def load_config():
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found at {CONFIG_PATH}", file=sys.stderr)
        print("Create it from email-config.template.json and fill in your credentials.", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    required = ["smtp_host", "smtp_port", "sender_email", "app_password"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        print(f"Error: Missing config keys: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return config


def build_email(sender, to_addrs, cc_addrs, subject, md_content, file_path):
    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    msg["Subject"] = subject

    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    html = HTML_WRAPPER.format(content=html_body)
    msg.attach(MIMEText(html, "html"))

    attachment = MIMEApplication(md_content.encode("utf-8"), Name=file_path.name)
    attachment["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
    msg.attach(attachment)

    return msg


def send(config, msg, all_recipients):
    port = config["smtp_port"]
    password = config["app_password"].replace(" ", "")
    if port == 465:
        with smtplib.SMTP_SSL(config["smtp_host"], port) as server:
            server.login(config["sender_email"], password)
            server.sendmail(config["sender_email"], all_recipients, msg.as_string())
    else:
        with smtplib.SMTP(config["smtp_host"], port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config["sender_email"], password)
            server.sendmail(config["sender_email"], all_recipients, msg.as_string())


def main():
    parser = argparse.ArgumentParser(description="Send a markdown file as an HTML email")
    parser.add_argument("--to", required=True, help="Recipient email (comma-separated for multiple)")
    parser.add_argument("--cc", default="", help="CC recipients (comma-separated)")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--file", required=True, help="Path to the markdown file to send")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    md_content = file_path.read_text(encoding="utf-8")
    config = load_config()

    to_addrs = [a.strip() for a in args.to.split(",") if a.strip()]
    cc_addrs = [a.strip() for a in args.cc.split(",") if a.strip()]
    all_recipients = to_addrs + cc_addrs

    msg = build_email(config["sender_email"], to_addrs, cc_addrs, args.subject, md_content, file_path)
    send(config, msg, all_recipients)

    print(f"Sent to: {', '.join(to_addrs)}")
    if cc_addrs:
        print(f"CC: {', '.join(cc_addrs)}")
    print(f"Subject: {args.subject}")
    print(f"File: {file_path}")


if __name__ == "__main__":
    main()
