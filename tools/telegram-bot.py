#!/usr/bin/env python3
"""
Telegram bot for looking up GTM research/outreach files and emailing them.

Commands:
    /send cyera                         -- email Cyera research to default recipient
    /send cyera to name@example.com     -- email to specific recipient
    /outreach cyera                     -- email Cyera outreach instead of research
    /outreach cyera to name@example.com
    /list                               -- list all companies with research
    /list icp-a                         -- list companies in a specific ICP
    /help                               -- show available commands

Start with:  python3 tools/telegram-bot.py
"""

from __future__ import annotations

import json
import logging
import re
import smtplib
import sys
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
RESEARCH_DIR = PROJECT_ROOT / "output" / "research"
OUTREACH_DIR = PROJECT_ROOT / "output" / "outreach"

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


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help and /start commands."""
    if not await check_access(update):
        return
    help_text = (
        "🫆 <b>Cyvore GTM-Agent Bot</b>\n\n"
        "<b>Commands:</b>\n"
        "/send &lt;company&gt; — email research to your default email\n"
        "/send &lt;company&gt; to email — email to a specific address\n"
        "/outreach &lt;company&gt; — email outreach plan\n"
        "/list — show all companies with files\n"
        "/list icp-a — filter by ICP (icp-a, icp-b, icp-c, icp-d)\n"
        "/help — show this message\n\n"
        "<b>Examples:</b>\n"
        "<code>/send cyera</code>\n"
        "<code>/send bezeq to colleague@company.com</code>\n"
        "<code>/outreach bank hapoalim</code>\n"
        "<code>/list icp-b</code>"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


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

    logger.info("Bot starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
