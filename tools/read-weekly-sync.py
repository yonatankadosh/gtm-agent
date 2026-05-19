#!/usr/bin/env python3
"""
Read the Cyvore GTM Weekly Sync Google Sheet and emit structured data.

The canonical workbook is the Google Sheet configured at
`tools/google-sheets-config.json`. Each tab is one weekly review, named in
the user's convention `DD.MM.YYYY` (e.g. `10.05.2026`). Each tab has a
header row with these 8 columns (unchanged from the deprecated xlsx era):

    Tier | Company/Lead Name | Deal/Lead Stage | Status | Next Step | Assignee | Done? | moving status

Modes:

    Default (no flags) — print the latest tab as JSON to stdout.

        python3 tools/read-weekly-sync.py

    --week YYYY-WW — pick the tab whose date falls in this ISO week.

        python3 tools/read-weekly-sync.py --week 2026-19

    --prior — also include the prior tab (one position before the chosen
    tab). Useful for Done? reconciliation. JSON output gains a "prior" key.

        python3 tools/read-weekly-sync.py --prior

    --by-assignee — write one markdown task file per Assignee under
    output/exec-comms/weekly-tasks/{YYYY-WW}/{owner-slug}.md, instead of
    JSON to stdout. Each file lists this week's owned rows + prior week's
    incomplete rows (Done? empty), plus a one-line send-email snippet.

        python3 tools/read-weekly-sync.py --by-assignee

    --list — list all tab names and exit.

    --config PATH — override the path to tools/google-sheets-config.json
    (default: standard location).

Multi-owner cells like "Yoav, Ori" are split — each owner gets the row in
their task file.
"""

import argparse
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_ROOT = REPO_ROOT / "output" / "exec-comms" / "weekly-tasks"

EXPECTED_HEADERS = [
    "Tier",
    "Company/Lead Name",
    "Deal/Lead Stage",
    "Status",
    "Next Step",
    "Assignee",
    "Done?",
    "moving status",
]


def load_sheets_client():
    spec = importlib.util.spec_from_file_location(
        "sheets_client", REPO_ROOT / "tools" / "sheets-client.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_tab_date(tab_name):
    """Tab names are DD.MM.YYYY. Return a date or None."""
    m = re.match(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$", tab_name)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def list_dated_tabs(sc):
    """Return list of (tab_name, date) sorted by date ascending. Tabs with
    unparseable names are dropped with a stderr warning."""
    pairs = []
    for name in sc.list_tabs():
        d = parse_tab_date(name)
        if d is None:
            sys.stderr.write(f"WARNING: skipping tab with non-date name: {name!r}\n")
            continue
        pairs.append((name, d))
    pairs.sort(key=lambda p: p[1])
    return pairs


def iso_week_of(d):
    y, w, _ = d.isocalendar()
    return f"{y:04d}-{w:02d}"


def pick_tab(tabs, week_arg):
    """Pick (tab_name, date) and the index in tabs. If week_arg given,
    find the tab whose date falls in that ISO week. Otherwise return the
    latest tab."""
    if week_arg is None:
        if not tabs:
            return None, -1
        return tabs[-1], len(tabs) - 1
    for i, (name, d) in enumerate(tabs):
        if iso_week_of(d) == week_arg:
            return (name, d), i
    return None, -1


def split_owners(assignee_cell):
    """Split 'Yoav, Ori' or 'Yoav/Ori' into ['Yoav', 'Ori']. Return [] for None."""
    if assignee_cell is None:
        return []
    parts = re.split(r"[,/]| and ", str(assignee_cell))
    return [p.strip() for p in parts if p.strip()]


def slugify_owner(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def is_done(rec):
    """Done? column — V means done. Empty / falsy means not done."""
    v = rec.get("Done?")
    if v is None:
        return False
    return str(v).strip().lower() in ("v", "yes", "y", "true", "x", "✓", "done")


def render_owner_md(owner, week_iso, this_week_rows, prior_incomplete_rows, sheet_url):
    """One markdown file per owner. Contains this week's tasks + prior week's
    incomplete tasks. Includes a send-email snippet."""
    lines = []
    lines.append(f"# Weekly Tasks — {owner} — Week {week_iso}")
    lines.append("")
    lines.append(f"Generated from the [Cyvore GTM Weekly Sync Google Sheet]({sheet_url}).")
    lines.append("")

    lines.append("## This week")
    lines.append("")
    if this_week_rows:
        lines.append("| Tier | Account | Stage | Next Step | Status |")
        lines.append("|---|---|---|---|---|")
        for r in this_week_rows:
            tier = r.get("Tier") or ""
            acct = r.get("Company/Lead Name") or ""
            stage = r.get("Deal/Lead Stage") or ""
            nxt = (r.get("Next Step") or "").replace("\n", " ")
            status = (r.get("Status") or "").replace("\n", " ")
            lines.append(f"| {tier} | {acct} | {stage} | {nxt} | {status} |")
    else:
        lines.append("_No items owned this week._")
    lines.append("")

    lines.append("## Carry-overs from last week (Done? was empty)")
    lines.append("")
    if prior_incomplete_rows:
        lines.append("| Tier | Account | Stage | Last week's Next Step |")
        lines.append("|---|---|---|---|")
        for r in prior_incomplete_rows:
            tier = r.get("Tier") or ""
            acct = r.get("Company/Lead Name") or ""
            stage = r.get("Deal/Lead Stage") or ""
            nxt = (r.get("Next Step") or "").replace("\n", " ")
            lines.append(f"| {tier} | {acct} | {stage} | {nxt} |")
    else:
        lines.append("_None — clean slate from last week._")
    lines.append("")

    owner_slug = slugify_owner(owner)
    lines.append("---")
    lines.append("")
    lines.append("Send via:")
    lines.append("")
    lines.append("```")
    lines.append(
        f'python tools/send-email.py --to "{owner.lower()}@cyvore.com" '
        f'--subject "Weekly tasks — Week {week_iso}" '
        f'--file "output/exec-comms/weekly-tasks/{week_iso}/{owner_slug}.md"'
    )
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def write_by_assignee(this_rows, prior_rows, week_iso, sheet_url):
    """Write one markdown file per unique owner under TASKS_ROOT/{week_iso}/."""
    target_dir = TASKS_ROOT / week_iso
    target_dir.mkdir(parents=True, exist_ok=True)

    by_owner_this = {}
    for r in this_rows:
        for owner in split_owners(r.get("Assignee")):
            by_owner_this.setdefault(owner, []).append(r)

    by_owner_prior_incomplete = {}
    if prior_rows is not None:
        prior_by_account = {
            (r.get("Company/Lead Name") or "").strip().lower(): r for r in prior_rows
        }
        for acct_key, r in prior_by_account.items():
            if is_done(r):
                continue
            if not r.get("Next Step"):
                continue
            for owner in split_owners(r.get("Assignee")):
                by_owner_prior_incomplete.setdefault(owner, []).append(r)

    owners = sorted(set(by_owner_this) | set(by_owner_prior_incomplete))
    written = []
    for owner in owners:
        md = render_owner_md(
            owner,
            week_iso,
            by_owner_this.get(owner, []),
            by_owner_prior_incomplete.get(owner, []),
            sheet_url,
        )
        path = target_dir / f"{slugify_owner(owner)}.md"
        path.write_text(md, encoding="utf-8")
        written.append(str(path.relative_to(REPO_ROOT)))
    return written


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--week", default=None, help="ISO week YYYY-WW (default: latest tab)")
    p.add_argument("--prior", action="store_true", help="Also include the prior tab")
    p.add_argument("--by-assignee", action="store_true", help="Write per-owner markdown files instead of JSON")
    p.add_argument("--list", action="store_true", help="List all tabs and exit")
    p.add_argument(
        "--config",
        default=None,
        help="Path to tools/google-sheets-config.json (default: standard location)",
    )
    args = p.parse_args()

    sheets_module = load_sheets_client()
    sc = sheets_module.SheetsClient(args.config)

    tabs = list_dated_tabs(sc)

    if args.list:
        for name, d in tabs:
            print(f"{name}\t{d.isoformat()}\t{iso_week_of(d)}")
        return

    if not tabs:
        sys.stderr.write(
            "ERROR: no date-named tabs found in the Sheet. Seed it first via "
            "tools/migrate-xlsx-to-sheet.py or tools/generate-weekly-tab.py.\n"
        )
        sys.exit(2)

    chosen, idx = pick_tab(tabs, args.week)
    if chosen is None:
        sys.stderr.write(f"ERROR: no tab found for week {args.week!r}.\n")
        sys.exit(2)
    tab_name, tab_date = chosen
    week_iso = iso_week_of(tab_date)

    this_rows = sc.read_tab(tab_name)

    prior_name = None
    prior_rows = None
    if args.prior or args.by_assignee:
        if idx > 0:
            prior_name, _ = tabs[idx - 1]
            prior_rows = sc.read_tab(prior_name)

    if args.by_assignee:
        written = write_by_assignee(this_rows, prior_rows, week_iso, sc.tab_url(tab_name))
        result = {
            "week": week_iso,
            "tab": tab_name,
            "tab_date": tab_date.isoformat(),
            "written": written,
            "owners": len(written),
            "sheet_url": sc.spreadsheet_url,
            "tab_url": sc.tab_url(tab_name),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    out = {
        "week": week_iso,
        "tab": tab_name,
        "tab_date": tab_date.isoformat(),
        "sheet_url": sc.spreadsheet_url,
        "tab_url": sc.tab_url(tab_name),
        "rows": this_rows,
        "summary": {
            "total": len(this_rows),
            "tier_a": sum(1 for r in this_rows if (r.get("Tier") or "").upper() == "A"),
            "tier_b": sum(1 for r in this_rows if (r.get("Tier") or "").upper() == "B"),
            "by_stage": {},
            "done_count": sum(1 for r in this_rows if is_done(r)),
            "next_step_count": sum(1 for r in this_rows if r.get("Next Step")),
        },
    }
    for r in this_rows:
        s = r.get("Deal/Lead Stage") or "(none)"
        out["summary"]["by_stage"][s] = out["summary"]["by_stage"].get(s, 0) + 1

    if prior_rows is not None:
        out["prior"] = {
            "tab": prior_name,
            "tab_url": sc.tab_url(prior_name),
            "rows": prior_rows,
            "summary": {
                "total": len(prior_rows),
                "done_count": sum(1 for r in prior_rows if is_done(r)),
                "next_step_count": sum(1 for r in prior_rows if r.get("Next Step")),
            },
        }
        prior_with_step = [r for r in prior_rows if r.get("Next Step")]
        prior_done = [r for r in prior_with_step if is_done(r)]
        out["done_scorecard"] = {
            "completed": len(prior_done),
            "total": len(prior_with_step),
            "percent": round(100.0 * len(prior_done) / len(prior_with_step), 1) if prior_with_step else None,
        }

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
