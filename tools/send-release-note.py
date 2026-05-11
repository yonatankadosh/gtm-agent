#!/usr/bin/env python3
"""
Render a markdown release-note source into the locked Cyvore email-safe HTML
template and send it via SMTP, with the Cyvore mark embedded as an inline
image (CID).

Two modes:
  --mode preview   Send a single approval copy to yonatank@cyvore.com.
                   No CCs. Subject is prefixed with "[PREVIEW]".
  --mode publish   Send one email per recipient (To: <recipient>), each with
                   the Cyvore-team CC list on it, so every recipient thread
                   has the internal team visible. Default CC list is the
                   Cyvore team below; override with --cc.

Markdown source schema (YAML frontmatter + sections):

    ---
    title: Reliability & Accuracy Update
    subtitle: We've just deployed an update to your environment — here's what changed.
    ---

    ## TL;DR

    - Bullet one
    - Bullet two

    ## Changelog

    ### [improvement] Item title

    Paragraph body for this item.

    ### [bug fix] Another item

    Body...

    ## Closing

    If you have any questions...

Tag vocabulary (extendable in TAG_STYLES below):
  improvement, bug fix, new feature, security, breaking change

Usage:
    python3 tools/send-release-note.py \
        --file output/cs/release-notes/2026-05-11-reliability-accuracy.md \
        --mode preview

    python3 tools/send-release-note.py \
        --file output/cs/release-notes/2026-05-11-reliability-accuracy.md \
        --mode publish \
        --to "alice@customer.com,bob@customer.com"
"""

import argparse
import json
import re
import smtplib
import sys
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SCRIPT_DIR / "email-config.json"
LOGO_PATH = SCRIPT_DIR / "assets" / "cyvore-logo-mark.png"

APPROVER_EMAIL = "yonatank@cyvore.com"
DEFAULT_CYVORE_TEAM_CC = [
    "ellar@cyvore.com",
    "peterv@cyvore.com",
    "yoav@cyvore.com",
    "yiftach@cyvore.com",
]

TAG_STYLES = {
    "improvement":     {"bg": "#ddeeff", "fg": "#185FA5"},
    "bug fix":         {"bg": "#e6f3de", "fg": "#3B6D11"},
    "new feature":     {"bg": "#e8e0ff", "fg": "#5F2BF8"},
    "security":        {"bg": "#ffe5d9", "fg": "#A04A1F"},
    "breaking change": {"bg": "#fde2e2", "fg": "#B11D1D"},
}
DEFAULT_TAG_STYLE = {"bg": "#eeeeee", "fg": "#555555"}


def load_config():
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    for k in ("smtp_host", "smtp_port", "sender_email", "app_password"):
        if not cfg.get(k):
            print(f"Error: Missing config key: {k}", file=sys.stderr)
            sys.exit(1)
    return cfg


def parse_source(md_text):
    """Parse the release-note markdown into a structured dict."""
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.DOTALL)
    if not fm_match:
        raise ValueError(
            "Release-note markdown must start with YAML frontmatter "
            "containing at least `title` and `subtitle`."
        )
    fm_raw = fm_match.group(1)
    body = md_text[fm_match.end():]

    front = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            front[key.strip().lower()] = val.strip()

    title = front.get("title", "").strip()
    subtitle = front.get("subtitle", "").strip()
    if not title:
        raise ValueError("Frontmatter is missing `title`.")

    sections = {}
    current = None
    buf = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m and not line.startswith("###"):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        else:
            if current is not None:
                buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()

    tldr_bullets = []
    if "tl;dr" in sections:
        for line in sections["tl;dr"].splitlines():
            line = line.strip()
            if line.startswith("- "):
                tldr_bullets.append(line[2:].strip())

    items = []
    if "changelog" in sections:
        chunks = re.split(r"^###\s+", sections["changelog"], flags=re.MULTILINE)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            head, _, rest = chunk.partition("\n")
            head_match = re.match(r"^\[([^\]]+)\]\s+(.*)$", head.strip())
            if not head_match:
                continue
            tag = head_match.group(1).strip().lower()
            item_title = head_match.group(2).strip()
            body_text = rest.strip()
            items.append({"tag": tag, "title": item_title, "body": body_text})

    closing = sections.get("closing", "").strip()

    return {
        "title": title,
        "subtitle": subtitle,
        "tldr": tldr_bullets,
        "items": items,
        "closing": closing,
    }


def escape(s):
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def render_html(doc):
    """Render the parsed doc into the locked email-safe HTML template."""
    title = escape(doc["title"])
    subtitle = escape(doc["subtitle"])

    tldr_rows = []
    last = len(doc["tldr"]) - 1
    for i, b in enumerate(doc["tldr"]):
        pad = "" if i == last else "padding-bottom:8px;"
        tldr_rows.append(
            f'<tr>'
            f'<td width="20" valign="top" style="width:20px; padding-top:3px; '
            f'color:#1D9E75; font-size:13.5px; line-height:1.5;">&#10003;</td>'
            f'<td valign="top" style="font-size:13.5px; color:#1a1a18; '
            f'line-height:1.5; {pad}">{escape(b)}</td>'
            f'</tr>'
        )
    tldr_block = "\n                      ".join(tldr_rows) if tldr_rows else (
        '<tr><td style="font-size:13.5px; color:#888780;">'
        '(no TL;DR provided)</td></tr>'
    )

    item_blocks = []
    n = len(doc["items"])
    for i, it in enumerate(doc["items"]):
        if n == 1:
            radius = "12px"
        elif i == 0:
            radius = "12px 12px 4px 4px"
        elif i == n - 1:
            radius = "4px 4px 12px 12px"
        else:
            radius = "4px"
        margin = "margin-bottom:2px;" if i < n - 1 else ""

        style = TAG_STYLES.get(it["tag"], DEFAULT_TAG_STYLE)
        tag_label = escape(it["tag"])
        item_title = escape(it["title"])
        body_text = escape(it["body"])

        item_blocks.append(f'''
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff; border:1px solid #e2e0d8; border-radius:{radius}; {margin}">
                <tr>
                  <td style="padding:16px 20px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:8px;">
                      <tr>
                        <td style="background:{style['bg']}; color:{style['fg']}; font-size:11px; font-weight:500; padding:3px 8px; border-radius:4px; white-space:nowrap;">{tag_label}</td>
                        <td style="padding-left:10px; font-size:15px; font-weight:500; color:#1a1a18;">{item_title}</td>
                      </tr>
                    </table>
                    <p style="margin:0; font-size:14px; color:#5f5e5a; line-height:1.65;">{body_text}</p>
                  </td>
                </tr>
              </table>''')

    items_html = "".join(item_blocks)

    closing = escape(doc["closing"]) if doc["closing"] else \
        "If you have any questions about these changes or their impact on your environment, we're happy to walk you through them."

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="x-apple-disable-message-reformatting" />
  <title>{title}</title>
</head>
<body style="margin:0; padding:0; background-color:#f5f5f3; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; color:#1a1a18;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f5f5f3;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table role="presentation" width="620" cellpadding="0" cellspacing="0" border="0" style="max-width:620px; width:100%; background:#ffffff; border:1px solid #e2e0d8; border-radius:16px; overflow:hidden;">
          <tr>
            <td style="padding:24px 32px 20px; border-bottom:1px solid #e2e0d8;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding-right:14px; vertical-align:middle; line-height:0;">
                    <img src="cid:cyvore-logo" width="32" height="39" alt="Cyvore" style="display:block; border:0; outline:none; text-decoration:none; height:39px; width:32px;" />
                  </td>
                  <td style="vertical-align:middle; font-size:12px; font-weight:500; color:#888780; letter-spacing:1px; text-transform:uppercase;">
                    Platform release
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 32px 32px;">
              <h1 style="font-size:22px; font-weight:500; margin:0 0 6px; color:#1a1a18; line-height:1.3;">{title}</h1>
              <p style="font-size:14px; color:#888780; margin:0 0 24px;">{subtitle}</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f5f5f3; border:1px solid #e2e0d8; border-radius:12px; margin-bottom:28px;">
                <tr>
                  <td style="padding:16px 20px;">
                    <p style="margin:0 0 12px; font-size:11px; font-weight:500; text-transform:uppercase; letter-spacing:1px; color:#888780;">TL;DR</p>
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      {tldr_block}
                    </table>
                  </td>
                </tr>
              </table>
{items_html}
              <p style="font-size:14px; color:#5f5e5a; margin:24px 0 0; line-height:1.6;">{closing}</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:28px; border-top:1px solid #e2e0d8;">
                <tr>
                  <td style="padding-top:20px;">
                    <p style="font-size:13px; color:#888780; margin:0;">The Cyvore Team</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
'''
    return html


def render_plain(doc):
    lines = [doc["title"], "", doc["subtitle"], "", "TL;DR"]
    for b in doc["tldr"]:
        lines.append(f" - {b}")
    lines.append("")
    for it in doc["items"]:
        lines.append(f"[{it['tag']}] {it['title']}")
        lines.append(it["body"])
        lines.append("")
    if doc["closing"]:
        lines.append(doc["closing"])
        lines.append("")
    lines.append("— The Cyvore Team")
    return "\n".join(lines)


def build_message(sender, to_addrs, cc_addrs, subject, html, plain, logo_bytes):
    root = MIMEMultipart("related")
    root["From"] = sender
    root["To"] = ", ".join(to_addrs)
    if cc_addrs:
        root["Cc"] = ", ".join(cc_addrs)
    root["Subject"] = subject

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain, "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    root.attach(alt)

    img = MIMEImage(logo_bytes, _subtype="png")
    img.add_header("Content-ID", "<cyvore-logo>")
    img.add_header("Content-Disposition", "inline", filename="cyvore-logo.png")
    root.attach(img)

    return root


def smtp_send(cfg, msg, all_recipients):
    pw = cfg["app_password"].replace(" ", "")
    port = cfg["smtp_port"]
    host = cfg["smtp_host"]
    sender = cfg["sender_email"]
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(sender, pw)
            s.sendmail(sender, all_recipients, msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(sender, pw)
            s.sendmail(sender, all_recipients, msg.as_string())


def split_csv(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser(description="Render and send a Cyvore release-note email.")
    parser.add_argument("--file", required=True, help="Path to the markdown release-note source")
    parser.add_argument("--mode", choices=["preview", "publish"], default=None,
                        help="preview = single approval send to the approver; "
                             "publish = one email per recipient with Cyvore-team CCs. "
                             "Required unless --render-only is set.")
    parser.add_argument("--to", default="",
                        help="Comma-separated recipient list (required for publish; ignored for preview)")
    parser.add_argument("--cc", default="",
                        help="Comma-separated CC override (default: built-in Cyvore team)")
    parser.add_argument("--approver", default=APPROVER_EMAIL,
                        help=f"Approver email for preview (default: {APPROVER_EMAIL})")
    parser.add_argument("--render-only", action="store_true",
                        help="Render the HTML and write the .html sibling file, do not send")
    args = parser.parse_args()

    src = Path(args.file)
    if not src.exists():
        print(f"Error: source not found: {src}", file=sys.stderr)
        sys.exit(1)
    if not LOGO_PATH.exists():
        print(f"Error: logo not found: {LOGO_PATH}", file=sys.stderr)
        sys.exit(1)

    md = src.read_text(encoding="utf-8")
    doc = parse_source(md)

    html = render_html(doc)
    plain = render_plain(doc)
    subject = f"Cyvore - Platform Release: {doc['title']}"

    html_path = src.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"Rendered HTML: {html_path}")

    if args.render_only:
        return

    if args.mode is None:
        print("Error: --mode is required (preview or publish) unless --render-only is set.",
              file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    logo_bytes = LOGO_PATH.read_bytes()

    if args.mode == "preview":
        to_addrs = [args.approver]
        cc_addrs = split_csv(args.cc)
        preview_subject = f"[PREVIEW] {subject}"
        msg = build_message(cfg["sender_email"], to_addrs, cc_addrs, preview_subject,
                            html, plain, logo_bytes)
        smtp_send(cfg, msg, to_addrs + cc_addrs)
        print(f"Preview sent to: {args.approver}")
        if cc_addrs:
            print(f"Preview CC: {', '.join(cc_addrs)}")
        print(f"Subject: {preview_subject}")
        return

    recipients = split_csv(args.to)
    if not recipients:
        print("Error: --to is required for publish mode (comma-separated recipients).",
              file=sys.stderr)
        sys.exit(1)
    cc_addrs = split_csv(args.cc) if args.cc else list(DEFAULT_CYVORE_TEAM_CC)

    sent = []
    for r in recipients:
        msg = build_message(cfg["sender_email"], [r], cc_addrs, subject,
                            html, plain, logo_bytes)
        smtp_send(cfg, msg, [r] + cc_addrs)
        sent.append(r)
        print(f"Sent to: {r}  (CC: {', '.join(cc_addrs) if cc_addrs else '-'})")

    print(f"\nPublished to {len(sent)} recipient(s). CC on every send: "
          f"{', '.join(cc_addrs) if cc_addrs else '-'}")
    print(f"Subject: {subject}")


if __name__ == "__main__":
    main()
