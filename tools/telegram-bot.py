#!/usr/bin/env python3
"""
Telegram bot for looking up GTM research/outreach files and emailing them.

Account-level commands:
    /send cyera                         -- email Cyera research to default recipient
    /send cyera to name@example.com     -- email to specific recipient
    /outreach cyera                     -- email Cyera outreach instead of research
    /outreach cyera to name@example.com
    /list                               -- list all companies with research
    /list icp-a                         -- list companies in a specific ICP

Cadence commands (deliver the latest agent output by audience):
    /pipeline                           -- email the latest weekly pipeline snapshot
    /digest    (or /weekly)             -- email the latest internal weekly digest
    /board                              -- email the latest quarterly board update
    /investor                           -- email the latest monthly investor letter
    /allhands                           -- email the latest all-hands script

Each cadence command serves the latest file from the matching agent output
folder (`output/pipeline/` for /pipeline, `output/exec-comms/{audience}/` for
the others). The artifacts themselves are produced inside Cursor by the
relevant agent (Sales for pipeline, Chief of Staff for the rest).

HubSpot write commands (mid-week, single-record, confirmation-gated):
    /update <account> status: X next: Y -- write Status + Next Step
    /note   <account> <free text>       -- log a HubSpot Note on the record
    /stage  <account> <stage label>     -- move record to a new stage
    /kill   <account> reason: <text>    -- Closed Lost / Disqualified + reason note
    /state  <account>                   -- read-only: show HubSpot's current values
    /yes (or /apply)                    -- apply the most recent pending write
    /cancel                             -- abandon any pending write
Each write command first replies with a "About to..." preview; you must send
/yes within 60 seconds to apply. Anything else cancels.

    /help                               -- show available commands

Start with:  python3 tools/telegram-bot.py
"""

from __future__ import annotations

import json
import logging
import re
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from html import escape
from difflib import SequenceMatcher
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import markdown as md_lib
from telegram import Update
from telegram.error import Conflict
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SCRIPT_DIR / "email-config.json"
HUBSPOT_CONFIG_PATH = SCRIPT_DIR / "hubspot-config.json"
HUBSPOT_MAPPING_PATH = PROJECT_ROOT / "state" / "hubspot-mapping.json"
RESEARCH_DIR = PROJECT_ROOT / "output" / "research"
OUTREACH_DIR = PROJECT_ROOT / "output" / "outreach"
PIPELINE_DIR = PROJECT_ROOT / "output" / "pipeline"
EXEC_COMMS_DIR = PROJECT_ROOT / "output" / "exec-comms"

HUBSPOT_API_BASE = "https://api.hubapi.com"
LEADS_OBJECT_TYPE = "0-136"
PENDING_TTL_SECONDS = 60

PENDING_WRITES: dict[int, dict] = {}

ICP_FOLDERS = {
    "icp-a": "icp-a-suite",
    "icp-a-suite": "icp-a-suite",
    "suite": "icp-a-suite",
    "icp-b": "icp-b-feed",
    "icp-b-feed": "icp-b-feed",
    "feed": "icp-b-feed",
    "icp-c": "icp-c-marketplace",
    "icp-c-marketplace": "icp-c-marketplace",
    "marketplace": "icp-c-marketplace",
    "icp-d": "icp-d-telecom",
    "icp-d-telecom": "icp-d-telecom",
    "telecom": "icp-d-telecom",
}

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
<p style="color: #999; font-size: 0.85em;">Sent via GTM Agent Telegram Bot.</p>
</body>
</html>
"""


def load_config():
    if not CONFIG_PATH.exists():
        logger.error("Config file not found at %s", CONFIG_PATH)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


async def check_access(update: Update) -> bool:
    """Return True if the user is allowed. Silently ignore unauthorized users."""
    config = load_config()
    allowed = config.get("allowed_telegram_ids", [])
    if not allowed:
        return True
    user_id = update.effective_user.id
    if user_id not in allowed:
        logger.warning("Unauthorized access attempt from user %s (%s)", user_id, update.effective_user.username)
        await update.message.reply_text("Access denied. Your Telegram ID is not in the allowed list.")
        return False
    return True


def find_files(base_dir: Path) -> dict[str, Path]:
    """Return a dict of {slug: path} for all .md files under base_dir."""
    results = {}
    if not base_dir.exists():
        return results
    for icp_folder in sorted(base_dir.iterdir()):
        if not icp_folder.is_dir():
            continue
        for md_file in sorted(icp_folder.glob("*.md")):
            if md_file.name == ".gitkeep":
                continue
            results[md_file.stem] = md_file
    return results


def find_latest_dated_file(directory: Path) -> Path | None:
    """Return the most recently modified .md file in `directory` (excluding .gitkeep).

    Used by cadence commands (/pipeline, /digest, /board, /investor, /allhands)
    which serve the most recent artifact written by the relevant agent.
    """
    if not directory.exists():
        return None
    candidates = [
        p for p in directory.glob("*.md")
        if p.name != ".gitkeep" and p.is_file()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def fuzzy_match(query: str, candidates: dict[str, Path], threshold: float = 0.5) -> list[tuple[str, Path, float]]:
    """Match a query against file slugs. Returns sorted matches above threshold."""
    query_normalized = query.lower().replace(" ", "-").replace("_", "-")

    # Exact match first
    if query_normalized in candidates:
        return [(query_normalized, candidates[query_normalized], 1.0)]

    # Substring match
    substring_matches = []
    for slug, path in candidates.items():
        if query_normalized in slug or slug in query_normalized:
            substring_matches.append((slug, path, 0.9))
    if substring_matches:
        return sorted(substring_matches, key=lambda x: x[2], reverse=True)

    # Fuzzy match
    scored = []
    for slug, path in candidates.items():
        ratio = SequenceMatcher(None, query_normalized, slug).ratio()
        if ratio >= threshold:
            scored.append((slug, path, ratio))
    return sorted(scored, key=lambda x: x[2], reverse=True)


def send_email(config: dict, recipient: str, subject: str, file_path: Path) -> str:
    """Send a markdown file as HTML email. Returns status message."""
    md_content = file_path.read_text(encoding="utf-8")
    html_body = md_lib.markdown(md_content, extensions=["tables", "fenced_code", "nl2br"])
    html = HTML_WRAPPER.format(content=html_body)

    msg = MIMEMultipart("mixed")
    msg["From"] = config["sender_email"]
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(html, "html"))

    attachment = MIMEApplication(md_content.encode("utf-8"), Name=file_path.name)
    attachment["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
    msg.attach(attachment)

    port = config["smtp_port"]
    password = config["app_password"].replace(" ", "")
    if port == 465:
        with smtplib.SMTP_SSL(config["smtp_host"], port) as server:
            server.login(config["sender_email"], password)
            server.sendmail(config["sender_email"], [recipient], msg.as_string())
    else:
        with smtplib.SMTP(config["smtp_host"], port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config["sender_email"], password)
            server.sendmail(config["sender_email"], [recipient], msg.as_string())

    return f"Sent to {recipient}"


def parse_send_args(text: str) -> tuple[str, str | None]:
    """Parse '/send cyera to email@example.com' into (company, recipient_or_None)."""
    match = re.match(r"(.+?)\s+to\s+([\w.+-]+@[\w.-]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text.strip(), None


async def cmd_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /send command — look up research and email it."""
    if not await check_access(update):
        return
    config = load_config()
    args_text = " ".join(context.args) if context.args else ""
    if not args_text:
        await update.message.reply_text("Usage: /send <company> [to email@example.com]")
        return

    company_query, recipient = parse_send_args(args_text)
    recipient = recipient or config.get("default_recipient")
    if not recipient:
        await update.message.reply_text("No recipient specified and no default_recipient in config.")
        return

    await update.message.reply_text(f"Looking up research for '{company_query}'...")

    candidates = find_files(RESEARCH_DIR)
    matches = fuzzy_match(company_query, candidates)

    if not matches:
        await update.message.reply_text(f"No research found for '{company_query}'.\n\nUse /list to see available companies.")
        return

    if len(matches) > 1 and matches[0][2] < 0.9:
        options = "\n".join(f"  - /send {slug}" for slug, _, _ in matches[:5])
        await update.message.reply_text(f"Multiple matches for '{company_query}':\n{options}")
        return

    slug, file_path, _ = matches[0]
    company_name = slug.replace("-", " ").title()
    subject = f"Account Research: {company_name}"

    try:
        status = send_email(config, recipient, subject, file_path)
        icp_folder = file_path.parent.name
        await update.message.reply_text(f"✅ {status}\n📄 {company_name} ({icp_folder})\n📧 Subject: {subject}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def cmd_outreach(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /outreach command — look up outreach file and email it."""
    if not await check_access(update):
        return
    config = load_config()
    args_text = " ".join(context.args) if context.args else ""
    if not args_text:
        await update.message.reply_text("Usage: /outreach <company> [to email@example.com]")
        return

    company_query, recipient = parse_send_args(args_text)
    recipient = recipient or config.get("default_recipient")
    if not recipient:
        await update.message.reply_text("No recipient specified and no default_recipient in config.")
        return

    await update.message.reply_text(f"Looking up outreach for '{company_query}'...")

    candidates = find_files(OUTREACH_DIR)
    matches = fuzzy_match(company_query, candidates)

    if not matches:
        await update.message.reply_text(f"No outreach found for '{company_query}'.\n\nUse /list to see available companies.")
        return

    if len(matches) > 1 and matches[0][2] < 0.9:
        options = "\n".join(f"  - /outreach {slug}" for slug, _, _ in matches[:5])
        await update.message.reply_text(f"Multiple matches for '{company_query}':\n{options}")
        return

    slug, file_path, _ = matches[0]
    company_name = slug.replace("-", " ").title()
    subject = f"Outreach Plan: {company_name}"

    try:
        status = send_email(config, recipient, subject, file_path)
        icp_folder = file_path.parent.name
        await update.message.reply_text(f"✅ {status}\n📄 {company_name} outreach ({icp_folder})\n📧 Subject: {subject}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command — show available research files."""
    if not await check_access(update):
        return
    filter_icp = None
    if context.args:
        key = context.args[0].lower()
        filter_icp = ICP_FOLDERS.get(key)
        if not filter_icp:
            valid = ", ".join(sorted(set(ICP_FOLDERS.values())))
            await update.message.reply_text(f"Unknown ICP '{key}'.\nValid: {valid}")
            return

    research = find_files(RESEARCH_DIR)
    outreach = find_files(OUTREACH_DIR)

    if filter_icp:
        research = {k: v for k, v in research.items() if v.parent.name == filter_icp}
        outreach = {k: v for k, v in outreach.items() if v.parent.name == filter_icp}

    if not research and not outreach:
        msg = "No files found."
        if filter_icp:
            msg += f" (filtered to {filter_icp})"
        await update.message.reply_text(msg)
        return

    icp_groups: dict[str, list[str]] = {}
    for slug, path in research.items():
        folder = path.parent.name
        has_outreach = slug in outreach
        marker = "📄+✉️" if has_outreach else "📄"
        icp_groups.setdefault(folder, []).append(f"  {marker} {slug}")

    for slug, path in outreach.items():
        if slug not in research:
            folder = path.parent.name
            icp_groups.setdefault(folder, []).append(f"  ✉️ {slug}")

    # HTML + escape: Telegram Markdown breaks on _ and other chars in company slugs
    parts: list[str] = ["📋 <b>Available Companies</b>"]
    for folder in sorted(icp_groups.keys()):
        parts.append(f"\n<b>{escape(folder)}</b>")
        for item in sorted(icp_groups[folder]):
            parts.append("\n" + escape(item))

    parts.append("\n\n📄 = research  ✉️ = outreach")
    parts.append("\nUse /send &lt;company&gt; or /outreach &lt;company&gt;")

    await update.message.reply_text("".join(parts), parse_mode="HTML")


async def _send_latest_cadence(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    directory: Path,
    label: str,
    subject_prefix: str,
) -> None:
    """Shared handler for cadence commands: find latest .md in `directory` and email it."""
    if not await check_access(update):
        return
    config = load_config()
    args_text = " ".join(context.args) if context.args else ""

    email_match = re.search(r"[\w.+-]+@[\w.-]+", args_text)
    recipient = email_match.group(0) if email_match else config.get("default_recipient")
    if not recipient:
        await update.message.reply_text("No recipient specified and no default_recipient in config.")
        return

    latest = find_latest_dated_file(directory)
    if latest is None:
        await update.message.reply_text(
            f"No {label} file found in {directory.relative_to(PROJECT_ROOT)}.\n\n"
            f"In Cursor, ask the agent to produce the latest {label} first."
        )
        return

    subject = f"{subject_prefix}: {latest.stem}"
    try:
        status = send_email(config, recipient, subject, latest)
        await update.message.reply_text(
            f"✅ {status}\n📄 {label} ({latest.name})\n📧 Subject: {subject}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pipeline — email the latest weekly pipeline snapshot."""
    await _send_latest_cadence(
        update, context, PIPELINE_DIR, "weekly pipeline snapshot", "Pipeline Snapshot"
    )


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /digest and /weekly — email the latest internal weekly digest."""
    await _send_latest_cadence(
        update, context, EXEC_COMMS_DIR / "weekly", "weekly digest", "Weekly Digest"
    )


async def cmd_board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /board — email the latest quarterly board update."""
    await _send_latest_cadence(
        update, context, EXEC_COMMS_DIR / "board", "board update", "Board Update"
    )


async def cmd_investor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /investor — email the latest monthly investor letter."""
    await _send_latest_cadence(
        update, context, EXEC_COMMS_DIR / "investor", "investor letter", "Investor Update"
    )


async def cmd_allhands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /allhands — email the latest all-hands script."""
    await _send_latest_cadence(
        update, context, EXEC_COMMS_DIR / "all-hands", "all-hands script", "All-Hands Update"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help and /start commands."""
    if not await check_access(update):
        return
    help_text = (
        "🫆 <b>Cyvore GTM-Agent Bot</b>\n\n"
        "<b>Account commands:</b>\n"
        "/send &lt;company&gt; — email research to your default email\n"
        "/send &lt;company&gt; to email — email to a specific address\n"
        "/outreach &lt;company&gt; — email outreach plan\n"
        "/list — show all companies with files\n"
        "/list icp-a — filter by ICP (icp-a, icp-b, icp-c, icp-d)\n\n"
        "<b>Cadence commands</b> (latest agent output):\n"
        "/pipeline — latest weekly pipeline snapshot\n"
        "/digest (or /weekly) — latest internal weekly digest\n"
        "/board — latest quarterly board update\n"
        "/investor — latest monthly investor letter\n"
        "/allhands — latest all-hands script\n\n"
        "<b>HubSpot writes</b> (60s confirmation, all need /yes after):\n"
        "/update &lt;acct&gt; status: X next: Y — push Status + Next Step\n"
        "/note &lt;acct&gt; &lt;text&gt; — log a HubSpot Note on the record\n"
        "/stage &lt;acct&gt; &lt;stage&gt; — move to a new stage\n"
        "/kill &lt;acct&gt; reason: &lt;text&gt; — Closed Lost / Disqualified + reason\n"
        "/state &lt;acct&gt; — read-only: current HubSpot values\n"
        "/yes (or /apply) — apply the most recent pending write\n"
        "/cancel — discard pending write\n\n"
        "/help — show this message\n\n"
        "<b>Examples:</b>\n"
        "<code>/send cyera</code>\n"
        "<code>/outreach bank hapoalim</code>\n"
        "<code>/update cato status: install complete next: sign next week</code>\n"
        "<code>/note att Sarah confirmed Q3 POC kickoff today</code>\n"
        "<code>/kill mekorot reason: 53d untouched, no sponsor</code>\n"
        "<code>/state cato</code>\n\n"
        "Cadence files are produced inside Cursor by the relevant agent "
        "(Sales for /pipeline, Chief of Staff for the rest). "
        "Run `run weekly` in Cursor first if a file is missing."
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


# ---------------------------------------------------------------------------
# HubSpot write commands (mirror agents/sales/skills/hubspot-quick-update.md)
# ---------------------------------------------------------------------------


def hubspot_token() -> str | None:
    if not HUBSPOT_CONFIG_PATH.exists():
        return None
    try:
        cfg = json.loads(HUBSPOT_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    token = cfg.get("private_app_token")
    return token if isinstance(token, str) and token else None


def load_mapping() -> dict | None:
    if not HUBSPOT_MAPPING_PATH.exists():
        return None
    try:
        return json.loads(HUBSPOT_MAPPING_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def hubspot_request(method: str, path: str, token: str, *, body=None, query=None):
    """Synchronous HubSpot REST call. Returns (status, parsed_json_or_text)."""
    url = HUBSPOT_API_BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return resp.status, None
            return resp.status, json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        return e.code, err_body
    except urllib.error.URLError as e:
        return 0, str(e)


def resolve_account(query: str, mapping: dict) -> tuple[str | None, dict | None, list[str]]:
    """Resolve user's free-text account query against state/hubspot-mapping.json.
    Returns (matched_key, entry, candidates_for_disambiguation).
    candidates is non-empty only when match is ambiguous."""
    keys = [k for k in mapping.keys() if not k.startswith("_")]
    q = query.strip()
    q_lower = q.lower()

    if q in mapping:
        return q, mapping[q], []

    for k in keys:
        if k.lower() == q_lower:
            return k, mapping[k], []

    substring = [k for k in keys if q_lower in k.lower() or k.lower() in q_lower]
    if len(substring) == 1:
        k = substring[0]
        return k, mapping[k], []
    if len(substring) > 1:
        return None, None, substring[:5]

    scored = []
    for k in keys:
        ratio = SequenceMatcher(None, q_lower, k.lower()).ratio()
        if ratio >= 0.55:
            scored.append((ratio, k))
    scored.sort(reverse=True)
    if not scored:
        return None, None, []
    if len(scored) == 1 or scored[0][0] - scored[1][0] > 0.15:
        k = scored[0][1]
        return k, mapping[k], []
    return None, None, [k for _, k in scored[:5]]


def parse_update_args(text: str) -> dict:
    """Parse '/update <account> status: X next: Y' into {account, status, next_step}.
    Order doesn't matter; missing fields are None. Both keywords are optional but
    at least one must be present."""
    out = {"account": None, "status": None, "next_step": None}
    text = text.strip()
    pattern = re.compile(
        r"\b(status|next(?:\s*step)?)\s*[:=]\s*(.+?)(?=\s+\b(?:status|next(?:\s*step)?)\s*[:=]|$)",
        re.IGNORECASE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        out["account"] = text
        return out
    out["account"] = text[: matches[0].start()].strip().rstrip(":,")
    for m in matches:
        kind = m.group(1).lower().replace(" ", "")
        value = m.group(2).strip().rstrip(",")
        if kind == "status":
            out["status"] = value
        else:
            out["next_step"] = value
    return out


def parse_kill_args(text: str) -> tuple[str, str | None]:
    """Parse '/kill <account> reason: ...' -> (account, reason)."""
    m = re.search(r"\breason\s*[:=]\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
    if m:
        return text[: m.start()].strip().rstrip(":,"), m.group(1).strip()
    return text.strip(), None


def parse_stage_args(text: str) -> tuple[str, str | None]:
    """Parse '/stage <account> <stage>' -> (account, stage_label).
    Stage label is everything after the last 'to' keyword if present,
    otherwise the last whitespace-separated token. Falls back to splitting
    on the last colon."""
    m = re.search(r"\bto\s+(.+)$", text, re.IGNORECASE | re.DOTALL)
    if m:
        return text[: m.start()].strip().rstrip(":,"), m.group(1).strip()
    parts = text.rsplit(":", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return text.strip(), None


def fetch_record_summary(entry: dict, token: str) -> list[dict]:
    """Fetch current Status + Next Step + stage for every deal/lead linked to
    the mapping entry. Returns list of {type, id, label, status, next_step,
    stage, url}. Empty list if no records or HubSpot read fails."""
    out = []
    for d in entry.get("deals") or []:
        rid = str(d["id"])
        status, payload = hubspot_request(
            "GET",
            f"/crm/v3/objects/deals/{rid}",
            token,
            query={
                "properties": "dealname,dealstage,hs_next_step,cyvore_weekly_status"
            },
        )
        if status == 200 and isinstance(payload, dict):
            props = payload.get("properties") or {}
            out.append(
                {
                    "type": "deal",
                    "id": rid,
                    "label": d.get("label") or props.get("dealname") or "",
                    "status_value": props.get("cyvore_weekly_status") or "",
                    "next_step": props.get("hs_next_step") or "",
                    "stage": props.get("dealstage") or "",
                    "url": f"https://app.hubspot.com/contacts/_/record/0-3/{rid}",
                }
            )
    for ld in entry.get("leads") or []:
        rid = str(ld["id"])
        status, payload = hubspot_request(
            "GET",
            f"/crm/v3/objects/{LEADS_OBJECT_TYPE}/{rid}",
            token,
            query={
                "properties": "hs_lead_name,hs_pipeline_stage,cyvore_next_step,cyvore_weekly_status"
            },
        )
        if status == 200 and isinstance(payload, dict):
            props = payload.get("properties") or {}
            out.append(
                {
                    "type": "lead",
                    "id": rid,
                    "label": ld.get("label") or props.get("hs_lead_name") or "",
                    "status_value": props.get("cyvore_weekly_status") or "",
                    "next_step": props.get("cyvore_next_step") or "",
                    "stage": props.get("hs_pipeline_stage") or "",
                    "url": f"https://app.hubspot.com/contacts/_/record/{LEADS_OBJECT_TYPE}/{rid}",
                }
            )
    return out


def stash_pending(chat_id: int, action: dict) -> None:
    PENDING_WRITES[chat_id] = {**action, "expires_at": time.time() + PENDING_TTL_SECONDS}


def pop_pending(chat_id: int) -> dict | None:
    pending = PENDING_WRITES.pop(chat_id, None)
    if pending is None:
        return None
    if pending.get("expires_at", 0) < time.time():
        return None
    return pending


def append_quick_update_log(entry_line: str) -> None:
    """Append a one-line audit entry to output/pipeline/{YYYY-WW}-sync-log.md.
    Creates the file with a minimal header if missing. Mirrors the format
    used by agents/sales/skills/hubspot-quick-update.md."""
    week = datetime.now().strftime("%G-%V")
    log_path = PROJECT_ROOT / "output" / "pipeline" / f"{week}-sync-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(
            f"# HubSpot Sync Log — Week {week}\n\n"
            "**Type:** Quick-updates (mid-week single-record edits via Telegram bot or hubspot-quick-update skill).\n\n"
            "## Quick-update entries\n\n",
            encoding="utf-8",
        )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry_line.rstrip() + "\n")


async def _setup_check(update: Update) -> tuple[str, dict] | None:
    """Common gate for HubSpot commands: token + mapping must be present."""
    if not await check_access(update):
        return None
    token = hubspot_token()
    if not token:
        await update.message.reply_text(
            "HubSpot Private App token not configured. Add tools/hubspot-config.json on the bot host."
        )
        return None
    mapping = load_mapping()
    if mapping is None:
        await update.message.reply_text(
            "state/hubspot-mapping.json not found on the bot host. Cannot resolve account."
        )
        return None
    return token, mapping


async def cmd_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Read-only: show HubSpot's current Status / Next Step / stage for an account."""
    setup = await _setup_check(update)
    if setup is None:
        return
    token, mapping = setup
    args_text = " ".join(context.args).strip() if context.args else ""
    if not args_text:
        await update.message.reply_text("Usage: /state <account>")
        return

    key, entry, candidates = resolve_account(args_text, mapping)
    if not entry:
        if candidates:
            opts = "\n".join(f"  /state {c}" for c in candidates)
            await update.message.reply_text(f"Multiple matches for '{args_text}':\n{opts}")
        else:
            await update.message.reply_text(
                f"'{args_text}' not in state/hubspot-mapping.json."
            )
        return

    records = fetch_record_summary(entry, token)
    if not records:
        await update.message.reply_text(
            f"<b>{escape(key)}</b> — mapped but no HubSpot records returned (read error or empty).",
            parse_mode="HTML",
        )
        return

    parts = [f"<b>{escape(key)}</b> ({len(records)} record(s)):"]
    for r in records:
        parts.append(
            f"\n• {escape(r['type'])} {escape(str(r['label']))} (id {r['id']})\n"
            f"  status: {escape(r['status_value']) or '<i>(empty)</i>'}\n"
            f"  next:   {escape(r['next_step']) or '<i>(empty)</i>'}\n"
            f"  stage:  <code>{escape(r['stage'])}</code>\n"
            f"  <a href=\"{r['url']}\">open in HubSpot</a>"
        )
    await update.message.reply_text("\n".join(parts), parse_mode="HTML", disable_web_page_preview=True)


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Propose Status / Next Step write. /yes within 60s applies it."""
    setup = await _setup_check(update)
    if setup is None:
        return
    token, mapping = setup
    args_text = " ".join(context.args).strip() if context.args else ""
    if not args_text:
        await update.message.reply_text(
            "Usage: /update <account> status: X next: Y\n"
            "(at least one of status / next is required)"
        )
        return

    parsed = parse_update_args(args_text)
    if not parsed["account"]:
        await update.message.reply_text("Couldn't parse account name from your message.")
        return
    if parsed["status"] is None and parsed["next_step"] is None:
        await update.message.reply_text("Need at least one of `status:` or `next:`.")
        return

    key, entry, candidates = resolve_account(parsed["account"], mapping)
    if not entry:
        if candidates:
            opts = "\n".join(f"  /update {c} status: ... next: ..." for c in candidates)
            await update.message.reply_text(f"Multiple matches for '{parsed['account']}':\n{opts}")
        else:
            await update.message.reply_text(
                f"'{parsed['account']}' not in state/hubspot-mapping.json."
            )
        return

    targets = []
    for d in entry.get("deals") or []:
        targets.append({"type": "deal", "id": str(d["id"]), "label": d.get("label", "")})
    for ld in entry.get("leads") or []:
        targets.append({"type": "lead", "id": str(ld["id"]), "label": ld.get("label", "")})
    if not targets:
        await update.message.reply_text(f"'{key}' has no linked deals or leads in the mapping.")
        return

    stash_pending(
        update.effective_chat.id,
        {
            "kind": "update",
            "account": key,
            "targets": targets,
            "status": parsed["status"],
            "next_step": parsed["next_step"],
        },
    )

    label_lines = "\n".join(
        f"  • {t['type']} {t['label']} (id {t['id']})" for t in targets
    )
    field_lines = []
    if parsed["status"] is not None:
        field_lines.append(f"  cyvore_weekly_status = {parsed['status']!r}")
    if parsed["next_step"] is not None:
        field_lines.append(
            f"  {'hs_next_step' if any(t['type'] == 'deal' for t in targets) else 'cyvore_next_step'} = {parsed['next_step']!r}"
        )
    msg = (
        f"<b>About to update {escape(key)}</b> ({len(targets)} record(s)):\n"
        f"<pre>{escape(label_lines)}</pre>\n"
        f"<pre>{escape(chr(10).join(field_lines))}</pre>\n"
        f"Reply /yes within {PENDING_TTL_SECONDS}s to apply, /cancel to drop."
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Propose a HubSpot Note write. /yes within 60s applies it."""
    setup = await _setup_check(update)
    if setup is None:
        return
    token, mapping = setup
    args_text = " ".join(context.args).strip() if context.args else ""
    if not args_text:
        await update.message.reply_text("Usage: /note <account> <free-text body>")
        return

    parts = args_text.split(None, 1)
    if len(parts) < 2:
        await update.message.reply_text("Note body is empty. Usage: /note <account> <body>")
        return

    account_query, body = parts[0], parts[1].strip()
    longer_match = re.match(r"(.+?)\s+([:\-—].+)$", args_text)
    if longer_match:
        account_query = longer_match.group(1).strip()
        body = longer_match.group(2).lstrip(":-— ").strip()

    key, entry, candidates = resolve_account(account_query, mapping)
    if not entry:
        if len(parts) >= 2:
            for sep_count in range(2, 5):
                sub_parts = args_text.split(None, sep_count)
                if len(sub_parts) > sep_count:
                    candidate_acct = " ".join(sub_parts[:sep_count])
                    candidate_body = sub_parts[sep_count]
                    key2, entry2, _ = resolve_account(candidate_acct, mapping)
                    if entry2:
                        key, entry, account_query, body = (
                            key2,
                            entry2,
                            candidate_acct,
                            candidate_body,
                        )
                        candidates = []
                        break
    if not entry:
        if candidates:
            opts = "\n".join(f"  /note {c} <body>" for c in candidates)
            await update.message.reply_text(f"Multiple matches for '{account_query}':\n{opts}")
        else:
            await update.message.reply_text(f"'{account_query}' not in state/hubspot-mapping.json.")
        return

    targets = []
    for d in entry.get("deals") or []:
        targets.append({"type": "deal", "id": str(d["id"]), "label": d.get("label", "")})
    for ld in entry.get("leads") or []:
        targets.append({"type": "lead", "id": str(ld["id"]), "label": ld.get("label", "")})
    if not targets:
        await update.message.reply_text(f"'{key}' has no linked deals or leads in the mapping.")
        return

    stash_pending(
        update.effective_chat.id,
        {"kind": "note", "account": key, "targets": targets, "body": body},
    )

    label_lines = "\n".join(
        f"  • {t['type']} {t['label']} (id {t['id']})" for t in targets
    )
    msg = (
        f"<b>About to log a HubSpot Note on {escape(key)}</b> "
        f"({len(targets)} record(s)):\n"
        f"<pre>{escape(label_lines)}</pre>\n"
        f"<i>body:</i> {escape(body)}\n"
        f"Reply /yes within {PENDING_TTL_SECONDS}s to apply, /cancel to drop."
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_stage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Propose a stage change. /yes within 60s applies it."""
    setup = await _setup_check(update)
    if setup is None:
        return
    token, mapping = setup
    args_text = " ".join(context.args).strip() if context.args else ""
    if not args_text:
        await update.message.reply_text(
            "Usage: /stage <account> to <stage label> (or /stage <account>: <stage>)"
        )
        return
    account_query, stage_label = parse_stage_args(args_text)
    if not stage_label:
        await update.message.reply_text(
            "Couldn't parse the target stage. Try: /stage cato to Running POC"
        )
        return

    key, entry, candidates = resolve_account(account_query, mapping)
    if not entry:
        if candidates:
            opts = "\n".join(f"  /stage {c} to {stage_label}" for c in candidates)
            await update.message.reply_text(f"Multiple matches for '{account_query}':\n{opts}")
        else:
            await update.message.reply_text(f"'{account_query}' not in state/hubspot-mapping.json.")
        return

    targets = []
    for d in entry.get("deals") or []:
        targets.append({"type": "deal", "id": str(d["id"]), "label": d.get("label", "")})
    for ld in entry.get("leads") or []:
        targets.append({"type": "lead", "id": str(ld["id"]), "label": ld.get("label", "")})
    if not targets:
        await update.message.reply_text(f"'{key}' has no linked deals or leads in the mapping.")
        return

    resolved = resolve_stage_label(stage_label, token, targets[0]["type"])
    if resolved is None:
        await update.message.reply_text(
            f"Stage label '{stage_label}' didn't match any HubSpot stage. "
            "Use /state &lt;account&gt; to see live stage values, "
            "or use the canonical labels from agents/sales/skills/hubspot-quick-update.md.",
            parse_mode="HTML",
        )
        return

    stash_pending(
        update.effective_chat.id,
        {
            "kind": "stage",
            "account": key,
            "targets": targets,
            "stage_id": resolved["id"],
            "stage_label": resolved["label"],
        },
    )

    label_lines = "\n".join(
        f"  • {t['type']} {t['label']} (id {t['id']})" for t in targets
    )
    msg = (
        f"<b>About to move {escape(key)}</b> ({len(targets)} record(s)) "
        f"to stage <code>{escape(resolved['label'])}</code> (id {resolved['id']}):\n"
        f"<pre>{escape(label_lines)}</pre>\n"
        f"Reply /yes within {PENDING_TTL_SECONDS}s to apply, /cancel to drop."
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Propose Closed Lost / Disqualified + reason note. /yes within 60s applies."""
    setup = await _setup_check(update)
    if setup is None:
        return
    token, mapping = setup
    args_text = " ".join(context.args).strip() if context.args else ""
    if not args_text:
        await update.message.reply_text("Usage: /kill <account> reason: <text>")
        return
    account_query, reason = parse_kill_args(args_text)
    if not reason:
        await update.message.reply_text("Reason is mandatory. Usage: /kill <account> reason: <text>")
        return

    key, entry, candidates = resolve_account(account_query, mapping)
    if not entry:
        if candidates:
            opts = "\n".join(f"  /kill {c} reason: {reason}" for c in candidates)
            await update.message.reply_text(f"Multiple matches for '{account_query}':\n{opts}")
        else:
            await update.message.reply_text(f"'{account_query}' not in state/hubspot-mapping.json.")
        return

    targets = []
    for d in entry.get("deals") or []:
        targets.append({"type": "deal", "id": str(d["id"]), "label": d.get("label", "")})
    for ld in entry.get("leads") or []:
        targets.append({"type": "lead", "id": str(ld["id"]), "label": ld.get("label", "")})
    if not targets:
        await update.message.reply_text(f"'{key}' has no linked deals or leads in the mapping.")
        return

    closed_lost_label = "Closed Lost" if any(t["type"] == "deal" for t in targets) else "Disqualified"
    resolved = resolve_stage_label(closed_lost_label, token, targets[0]["type"])
    if resolved is None:
        await update.message.reply_text(
            f"Couldn't resolve '{closed_lost_label}' stage in HubSpot. Aborting."
        )
        return

    stash_pending(
        update.effective_chat.id,
        {
            "kind": "kill",
            "account": key,
            "targets": targets,
            "stage_id": resolved["id"],
            "stage_label": resolved["label"],
            "reason": reason,
        },
    )

    label_lines = "\n".join(
        f"  • {t['type']} {t['label']} (id {t['id']})" for t in targets
    )
    msg = (
        f"<b>About to kill {escape(key)}</b>:\n"
        f"<pre>{escape(label_lines)}</pre>\n"
        f"  1. Move to <code>{escape(resolved['label'])}</code> (id {resolved['id']})\n"
        f"  2. Log Note: <i>Closed Lost — {escape(reason)}</i>\n"
        f"Reply /yes within {PENDING_TTL_SECONDS}s to apply, /cancel to drop."
    )
    await update.message.reply_text(msg, parse_mode="HTML")


def resolve_stage_label(label: str, token: str, object_type: str) -> dict | None:
    """Look up a stage by label across HubSpot pipelines for the given object type.
    object_type: 'deal' or 'lead'. Returns {id, label} or None."""
    api_obj = "deals" if object_type == "deal" else LEADS_OBJECT_TYPE
    status, payload = hubspot_request("GET", f"/crm/v3/pipelines/{api_obj}", token)
    if status != 200 or not isinstance(payload, dict):
        return None
    label_lower = label.strip().lower()
    aliases = {
        "closed lost": ["closed lost", "closedlost", "lost", "killed", "dead"],
        "closed won": ["closed won", "closedwon", "won", "signed"],
        "disqualified": ["disqualified", "unqualified", "kill", "dead", "lost"],
        "running poc": ["running poc"],
        "finalizing the poc": ["finalizing the poc", "finalizing"],
        "in meetings/conversations": ["in meetings/conversations", "meetings", "in meetings"],
    }
    expand = []
    for canonical, alts in aliases.items():
        if label_lower in alts:
            expand.append(canonical)
            break
    candidates = [label_lower] + expand

    for pipeline in payload.get("results", []):
        for stage in pipeline.get("stages", []):
            slug = (stage.get("label") or "").strip().lower()
            if slug in candidates or label_lower == stage.get("id"):
                return {"id": stage["id"], "label": stage.get("label") or stage["id"]}
    return None


async def _apply_update(token: str, action: dict) -> tuple[bool, str]:
    """Apply a stashed 'update' action (Status + Next Step). Returns (ok, summary)."""
    succeeded, failed = [], []
    for t in action["targets"]:
        if t["type"] == "deal":
            props = {}
            if action["status"] is not None:
                props["cyvore_weekly_status"] = action["status"]
            if action["next_step"] is not None:
                props["hs_next_step"] = action["next_step"]
            status_code, payload = hubspot_request(
                "PATCH",
                f"/crm/v3/objects/deals/{t['id']}",
                token,
                body={"properties": props},
            )
        else:
            props = {}
            if action["status"] is not None:
                props["cyvore_weekly_status"] = action["status"]
            if action["next_step"] is not None:
                props["cyvore_next_step"] = action["next_step"]
            status_code, payload = hubspot_request(
                "PATCH",
                f"/crm/v3/objects/{LEADS_OBJECT_TYPE}/{t['id']}",
                token,
                body={"properties": props},
            )
        if status_code in (200, 201):
            succeeded.append(t)
        else:
            failed.append((t, status_code, payload))

    log_lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M IDT")
    for t in succeeded:
        log_lines.append(
            f"- {ts}: telegram /update on {action['account']} ({t['type']} {t['id']}): "
            f"status={action['status']!r}, next={action['next_step']!r} — applied."
        )
    for t, code, payload in failed:
        log_lines.append(
            f"- {ts}: telegram /update on {action['account']} ({t['type']} {t['id']}): FAILED "
            f"http={code} body={str(payload)[:200]!r}"
        )
    if log_lines:
        for line in log_lines:
            append_quick_update_log(line)

    if not failed:
        return True, f"Updated {len(succeeded)} record(s) on {action['account']}."
    return False, (
        f"Updated {len(succeeded)} record(s); failed {len(failed)}. "
        f"First error: http={failed[0][1]} body={str(failed[0][2])[:200]}"
    )


async def _create_note(token: str, body: str, target_type: str, target_id: str) -> tuple[int, dict | str]:
    """Create a HubSpot Note and associate to the target via v4 associations.
    Note: Lead notes use object 0-136 association IDs; Deal notes use 0-3.
    The create payload below uses inline associations (works for deals reliably;
    for leads, requires the right associationTypeId — we fetch it on demand)."""
    if target_type == "deal":
        assoc_type_id = 214
        to_object = "deals"
    else:
        assoc_type_id = 866
        to_object = LEADS_OBJECT_TYPE

    timestamp_ms = int(time.time() * 1000)
    body_payload = {
        "properties": {
            "hs_note_body": body,
            "hs_timestamp": str(timestamp_ms),
        },
        "associations": [
            {
                "to": {"id": str(target_id)},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": assoc_type_id,
                    }
                ],
            }
        ],
    }
    return hubspot_request("POST", "/crm/v3/objects/notes", token, body=body_payload)


async def _apply_note(token: str, action: dict) -> tuple[bool, str]:
    succeeded, failed = [], []
    for t in action["targets"]:
        status_code, payload = await _create_note(token, action["body"], t["type"], t["id"])
        if status_code in (200, 201):
            succeeded.append(t)
        else:
            failed.append((t, status_code, payload))

    ts = datetime.now().strftime("%Y-%m-%d %H:%M IDT")
    for t in succeeded:
        append_quick_update_log(
            f"- {ts}: telegram /note on {action['account']} ({t['type']} {t['id']}): "
            f"body={action['body'][:120]!r} — applied."
        )
    for t, code, payload in failed:
        append_quick_update_log(
            f"- {ts}: telegram /note on {action['account']} ({t['type']} {t['id']}): FAILED "
            f"http={code} body={str(payload)[:200]!r}"
        )

    if not failed:
        return True, f"Logged Note on {len(succeeded)} record(s) of {action['account']}."
    return False, (
        f"Logged on {len(succeeded)}; failed {len(failed)}. "
        f"First error: http={failed[0][1]} body={str(failed[0][2])[:200]}"
    )


async def _apply_stage(token: str, action: dict) -> tuple[bool, str]:
    succeeded, failed = [], []
    for t in action["targets"]:
        if t["type"] == "deal":
            props = {"dealstage": action["stage_id"]}
            url = f"/crm/v3/objects/deals/{t['id']}"
        else:
            props = {"hs_pipeline_stage": action["stage_id"]}
            url = f"/crm/v3/objects/{LEADS_OBJECT_TYPE}/{t['id']}"
        status_code, payload = hubspot_request(
            "PATCH", url, token, body={"properties": props}
        )
        if status_code in (200, 201):
            succeeded.append(t)
        else:
            failed.append((t, status_code, payload))

    ts = datetime.now().strftime("%Y-%m-%d %H:%M IDT")
    for t in succeeded:
        append_quick_update_log(
            f"- {ts}: telegram /stage on {action['account']} ({t['type']} {t['id']}): "
            f"-> {action['stage_label']!r} — applied."
        )
    for t, code, payload in failed:
        append_quick_update_log(
            f"- {ts}: telegram /stage on {action['account']} ({t['type']} {t['id']}): FAILED "
            f"http={code} body={str(payload)[:200]!r}"
        )

    if not failed:
        return True, f"Moved {len(succeeded)} record(s) of {action['account']} -> {action['stage_label']}."
    return False, (
        f"Moved {len(succeeded)}; failed {len(failed)}. "
        f"First error: http={failed[0][1]} body={str(failed[0][2])[:200]}"
    )


async def _apply_kill(token: str, action: dict) -> tuple[bool, str]:
    stage_ok, stage_msg = await _apply_stage(token, action)
    note_action = {
        "account": action["account"],
        "targets": action["targets"],
        "body": f"Closed Lost — {action['reason']}",
    }
    note_ok, note_msg = await _apply_note(token, note_action)
    if stage_ok and note_ok:
        return True, f"Killed {action['account']}: stage + note both applied."
    return False, f"Stage: {stage_msg}; Note: {note_msg}"


async def cmd_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Apply the most recent pending write for this chat."""
    if not await check_access(update):
        return
    token = hubspot_token()
    if not token:
        await update.message.reply_text("HubSpot token not configured on bot host.")
        return
    chat_id = update.effective_chat.id
    pending = pop_pending(chat_id)
    if not pending:
        await update.message.reply_text(
            "Nothing to apply (or your previous proposal expired). Send a fresh /update, /note, /stage or /kill."
        )
        return

    kind = pending["kind"]
    if kind == "update":
        ok, msg = await _apply_update(token, pending)
    elif kind == "note":
        ok, msg = await _apply_note(token, pending)
    elif kind == "stage":
        ok, msg = await _apply_stage(token, pending)
    elif kind == "kill":
        ok, msg = await _apply_kill(token, pending)
    else:
        await update.message.reply_text(f"Unknown pending action kind: {kind!r}")
        return

    prefix = "✅" if ok else "⚠️"
    await update.message.reply_text(f"{prefix} {msg}")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Discard any pending HubSpot write for this chat."""
    if not await check_access(update):
        return
    if PENDING_WRITES.pop(update.effective_chat.id, None):
        await update.message.reply_text("Pending HubSpot write discarded.")
    else:
        await update.message.reply_text("No pending HubSpot write to cancel.")


async def post_init(application: Application) -> None:
    """Remove webhook so getUpdates/polling works (fixes silent failure after API or infra changes)."""
    await application.bot.delete_webhook(drop_pending_updates=True)
    me = await application.bot.get_me()
    logger.info("Webhook cleared; polling as @%s (%s)", me.username, me.id)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    logger.exception("Handler error: %s", err)
    if isinstance(err, Conflict):
        logger.error(
            "Telegram Conflict: another process is polling this bot token. "
            "Stop local `telegram-bot.py` or duplicate systemd services; only one instance allowed."
        )


def main():
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token:
        logger.error("No telegram_bot_token in config. Add it to tools/email-config.json")
        sys.exit(1)

    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    app.add_error_handler(on_error)

    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("send", cmd_send))
    app.add_handler(CommandHandler("outreach", cmd_outreach))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("pipeline", cmd_pipeline))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("weekly", cmd_digest))
    app.add_handler(CommandHandler("board", cmd_board))
    app.add_handler(CommandHandler("investor", cmd_investor))
    app.add_handler(CommandHandler("allhands", cmd_allhands))
    app.add_handler(CommandHandler("update", cmd_update))
    app.add_handler(CommandHandler("note", cmd_note))
    app.add_handler(CommandHandler("stage", cmd_stage))
    app.add_handler(CommandHandler("kill", cmd_kill))
    app.add_handler(CommandHandler("state", cmd_state))
    app.add_handler(CommandHandler("yes", cmd_yes))
    app.add_handler(CommandHandler("apply", cmd_yes))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    logger.info("Bot starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
