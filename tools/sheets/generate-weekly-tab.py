#!/usr/bin/env python3
"""
Generate this Monday's tab in the Cyvore GTM Weekly Sync Google Sheet from
live HubSpot state. Reverse direction of hubspot-status-sync (which is
Sheet -> HubSpot).

Behavior (rewritten 2026-W22):
  - The tab is BUILT FROM SCRATCH from current HubSpot state, not cloned-and-
    patched from last week. This guarantees the Sheet view exactly matches
    HubSpot's current pipelines (no stale rows linger, no manual surgery).
  - HubSpot records whose stage is in EXCLUDED_STAGES (Closed Lost,
    Disqualified) are NEVER written. The Monday meeting only sees live work.
  - Records are grouped by HubSpot pipeline label (Sales, BD&Leads,
    Collaborations&Partnerships, ...), and within each pipeline by stage
    (using HubSpot's displayOrder). Section + stage subheader rows are
    inserted as visual structure; the read path skips them.
  - Tier / Assignee / moving status are CARRIED FORWARD from the most
    recent prior tab by Company/Lead Name lookup. Done? is intentionally
    NOT carried — every week starts fresh.
  - When a row has no Tier in the prior tab (or no prior tab match), Tier
    defaults to A.
  - Mapped records (in state/hubspot-mapping.json) use the user-chosen
    mapping key as the Company/Lead Name; if the company has multiple HubSpot
    records (Cato has Feed + Suite), the per-deal label disambiguates
    ('Cato (Suite)' vs 'Cato (Feed)') so each row has a single, unambiguous
    stage.
  - Unmapped HubSpot records are integrated into the natural pipeline/stage
    groups, with the name suffixed '*' so the user can triage them into the
    mapping over time.
  - Cell formatting is applied via Sheets batchUpdate: header (dark blue),
    pipeline section (navy), stage subheader (light gray italic), per-stage
    stage cell (palette graded by progression), Tier-A (gold) vs Tier-B
    (silver).

Usage:
    python3 tools/sheets/generate-weekly-tab.py                       # this Monday
    python3 tools/sheets/generate-weekly-tab.py --target-date 2026-05-25
    python3 tools/sheets/generate-weekly-tab.py --force               # overwrite existing
    python3 tools/sheets/generate-weekly-tab.py --dry-run             # plan only
"""

import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HS_CONFIG = REPO_ROOT / "tools" / "hubspot" / "hubspot-config.json"
MAPPING_PATH = REPO_ROOT / "state" / "hubspot-mapping.json"
SNAPSHOT_DIR = REPO_ROOT / "state" / "sheet-snapshots"

API_BASE = "https://api.hubapi.com"
LEADS_OBJECT_TYPE = "0-136"

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
COL = {h: i + 1 for i, h in enumerate(EXPECTED_HEADERS)}

DEAL_PROPERTIES = [
    "dealname",
    "dealstage",
    "hs_next_step",
    "cyvore_weekly_status",
    "pipeline",
    "amount",
    "closedate",
    "hs_lastmodifieddate",
]
LEAD_PROPERTIES = [
    "hs_lead_name",
    "hs_pipeline_stage",
    "hs_lead_status",
    "cyvore_next_step",
    "cyvore_weekly_status",
    "hs_lastmodifieddate",
]

# Stages we never write to the Sheet — dead lanes don't deserve meeting time.
EXCLUDED_STAGES = {"Closed Lost", "Disqualified"}

# Dropdown vocabularies (data validation) applied to data rows.
# Tier and Done? are static; Assignee mirrors the original xlsx; Stage is
# computed dynamically (HubSpot's full live stage set, minus excluded stages,
# ordered by STAGE_DROPDOWN_PRIORITY then alphabetically for unknowns).
TIER_OPTIONS = ["A", "B"]
DONE_OPTIONS = ["V"]
ASSIGNEE_OPTIONS = ["Ella", "Yoav", "Ori", "Yonatan", "Peter", "Yiftach", "Aviv"]
STAGE_DROPDOWN_PRIORITY = [
    # Sales-side, most-advanced first (matches the original xlsx convention so
    # users tabbing through the dropdown hit the most likely "next" stage first
    # when a deal is moving forward).
    "CS",
    "Closed Won",
    "Running POC",
    "Finalizing the POC",
    "In meetings/conversations",
    "Connected",
    "Attempting",
    "New",
    "Qualified",
    # Collaborations/partnerships side.
    "Negotiations",
    "Collaborating",
]

# Render order for pipelines. Match is case-insensitive and ignores
# whitespace / non-alphanum (so "BD & Leads" matches "BD&Leads").
DEFAULT_PIPELINE_ORDER = [
    "Sales",
    "BD&Leads",
    "Collaborations&Partnerships",
]

# RGB on 0..1 scale (Sheets API convention).
COLOR = {
    "header_bg":         {"red": 0.27, "green": 0.45, "blue": 0.77},
    "header_text":       {"red": 1.00, "green": 1.00, "blue": 1.00},
    "section_bg":        {"red": 0.20, "green": 0.30, "blue": 0.50},
    "section_text":      {"red": 1.00, "green": 1.00, "blue": 1.00},
    "stage_header_bg":   {"red": 0.93, "green": 0.93, "blue": 0.93},
    "tier_a":            {"red": 1.00, "green": 0.95, "blue": 0.80},
    "tier_b":            {"red": 0.92, "green": 0.92, "blue": 0.92},
    "unmapped_marker":   {"red": 1.00, "green": 0.93, "blue": 0.85},
    "stage_new":         {"red": 0.85, "green": 0.92, "blue": 1.00},
    "stage_attempting":  {"red": 0.78, "green": 0.87, "blue": 0.97},
    "stage_connected":   {"red": 0.69, "green": 0.81, "blue": 0.93},
    "stage_qualified":   {"red": 0.58, "green": 0.75, "blue": 0.90},
    "stage_meetings":    {"red": 1.00, "green": 0.90, "blue": 0.70},
    "stage_running_poc": {"red": 1.00, "green": 0.83, "blue": 0.55},
    "stage_finalizing":  {"red": 1.00, "green": 0.95, "blue": 0.55},
    "stage_cs":          {"red": 0.78, "green": 0.91, "blue": 0.70},
    "stage_closed_won":  {"red": 0.50, "green": 0.80, "blue": 0.50},
    "stage_default":     {"red": 0.96, "green": 0.96, "blue": 0.96},
}


def stage_color_key(stage_label):
    """Best-effort mapping from a stage label to a color key."""
    s = (stage_label or "").lower()
    if s == "new" or "newly" in s:
        return "stage_new"
    if "attempt" in s:
        return "stage_attempting"
    if "connect" in s:
        return "stage_connected"
    if "qualif" in s and "dis" not in s:
        return "stage_qualified"
    if "meet" in s or "convers" in s:
        return "stage_meetings"
    if "running" in s or s == "poc":
        return "stage_running_poc"
    if "finaliz" in s:
        return "stage_finalizing"
    if s == "cs" or "customer success" in s:
        return "stage_cs"
    if "won" in s:
        return "stage_closed_won"
    return "stage_default"


# ---- HubSpot REST -----------------------------------------------------------


def die(msg, code=2):
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def load_token():
    if not HS_CONFIG.exists():
        die(f"Missing {HS_CONFIG.relative_to(REPO_ROOT)}.")
    cfg = json.loads(HS_CONFIG.read_text(encoding="utf-8"))
    token = cfg.get("private_app_token")
    if not token:
        die(f"{HS_CONFIG} has no 'private_app_token'.")
    return token


def http(method, path, token, body=None, query=None):
    url = API_BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else None
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        die(f"HubSpot {method} {url} -> HTTP {e.code} {e.reason}: {body_text}", code=3)
    except urllib.error.URLError as e:
        die(f"Network error: {e}", code=3)


def fetch_pipelines(token, object_type):
    """Return dict: stage_id -> {label, pipeline_id, pipeline_label, displayOrder, archived}."""
    resp = http("GET", f"/crm/v3/pipelines/{object_type}", token)
    out = {}
    for pipeline in resp.get("results", []):
        for stage in pipeline.get("stages", []):
            out[stage["id"]] = {
                "label": stage.get("label") or stage["id"],
                "pipeline_id": pipeline["id"],
                "pipeline_label": pipeline.get("label") or pipeline["id"],
                "displayOrder": stage.get("displayOrder", 999),
                "archived": stage.get("archived", False),
            }
    return out


def fetch_all_objects(token, object_type, properties):
    out, after = [], None
    while True:
        query = {"limit": 100, "properties": ",".join(properties), "archived": "false"}
        if after:
            query["after"] = after
        resp = http("GET", f"/crm/v3/objects/{object_type}", token, query=query)
        out.extend(resp.get("results", []))
        after = resp.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
        time.sleep(0.05)
    return out


# ---- Date / tab name helpers -----------------------------------------------


def this_monday(target_date=None):
    if target_date is None:
        target_date = date.today()
    return target_date - timedelta(days=target_date.weekday())


def fmt_tab(d):
    return d.strftime("%d.%m.%Y")


def parse_tab_date(name):
    m = re.match(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$", name)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def latest_tab_name(tabs):
    pairs = [(n, parse_tab_date(n)) for n in tabs]
    pairs = [p for p in pairs if p[1]]
    if not pairs:
        return None
    pairs.sort(key=lambda p: p[1])
    return pairs[-1][0]


# ---- Mapping + record assembly ---------------------------------------------


def build_inverse_mapping(mapping):
    """Returns (deal_id_to_(name,label), lead_id_to_(name,label),
    name_to_record_count). The count drives multi-record name disambiguation
    (e.g. 'Cato (Feed)' vs 'Cato (Suite)' when Cato has 2 deals)."""
    deal_inv, lead_inv, counts = {}, {}, {}
    for name, entry in (mapping or {}).items():
        if name.startswith("_") or not isinstance(entry, dict):
            continue
        deals = entry.get("deals") or []
        leads = entry.get("leads") or []
        counts[name] = len(deals) + len(leads)
        for d in deals:
            if d.get("id") is not None:
                deal_inv[str(d["id"])] = (name, d.get("label") or "")
        for ld in leads:
            if ld.get("id") is not None:
                lead_inv[str(ld["id"])] = (name, ld.get("label") or "")
    return deal_inv, lead_inv, counts


def display_name(mapping_key, label, hubspot_default, multi_record):
    """Compose the row's Company/Lead Name."""
    if mapping_key:
        if multi_record and label:
            return f"{mapping_key} ({label})"
        return mapping_key
    return f"{hubspot_default}*"  # unmapped marker


def build_records(deal_inv, lead_inv, counts, deals, leads, deal_pipelines, lead_pipelines):
    records = []
    for d in deals:
        rid = str(d.get("id"))
        props = d.get("properties") or {}
        info = deal_pipelines.get(props.get("dealstage"), {})
        stage = info.get("label", "<unknown>")
        if stage in EXCLUDED_STAGES:
            continue
        mkey, label = deal_inv.get(rid, (None, ""))
        records.append({
            "type": "deal",
            "id": rid,
            "name": display_name(
                mkey, label,
                props.get("dealname") or f"<deal {rid}>",
                multi_record=mkey is not None and counts.get(mkey, 0) > 1,
            ),
            "mapping_key": mkey,
            "pipeline": info.get("pipeline_label") or "Unknown",
            "stage": stage,
            "stage_order": info.get("displayOrder", 999),
            "status": props.get("cyvore_weekly_status") or "",
            "next_step": props.get("hs_next_step") or "",
        })
    for ld in leads:
        rid = str(ld.get("id"))
        props = ld.get("properties") or {}
        info = lead_pipelines.get(props.get("hs_pipeline_stage"), {})
        stage = info.get("label", "<unknown>")
        if stage in EXCLUDED_STAGES:
            continue
        mkey, label = lead_inv.get(rid, (None, ""))
        records.append({
            "type": "lead",
            "id": rid,
            "name": display_name(
                mkey, label,
                props.get("hs_lead_name") or f"<lead {rid}>",
                multi_record=mkey is not None and counts.get(mkey, 0) > 1,
            ),
            "mapping_key": mkey,
            "pipeline": info.get("pipeline_label") or "Unknown",
            "stage": stage,
            "stage_order": info.get("displayOrder", 999),
            "status": props.get("cyvore_weekly_status") or "",
            "next_step": props.get("cyvore_next_step") or "",
        })
    return records


def pipeline_display_label(name):
    """Trim noise from HubSpot's verbose pipeline labels for display in the
    Sheet's section headers. 'Cyvore Sales Pipeline' -> 'SALES'."""
    out = re.sub(r"^\s*cyvore\s+", "", name or "", flags=re.IGNORECASE)
    out = re.sub(r"\s+pipeline\s*$", "", out, flags=re.IGNORECASE).strip()
    return out.upper() if out else (name or "").upper()


def normalize_pipeline_order(records, requested):
    """Return the order to render pipelines. Match `requested` first by
    substring (case- and punctuation-insensitive — so 'Sales' matches
    'Cyvore Sales Pipeline'), then any others alphabetically."""
    def norm(s):
        return re.sub(r"[^a-z0-9&]", "", (s or "").lower())
    record_pipelines = sorted({r["pipeline"] for r in records}, key=str.lower)
    norms = [(norm(p), p) for p in record_pipelines]
    seen, seen_set = [], set()
    for want in requested:
        want_n = norm(want)
        if not want_n:
            continue
        # Prefer exact matches, then substring matches (handles HubSpot's
        # 'Cyvore Sales Pipeline' vs the user's shorthand 'Sales').
        match = next((p for n, p in norms if n == want_n and p not in seen_set), None)
        if not match:
            match = next((p for n, p in norms if want_n in n and p not in seen_set), None)
        if match:
            seen.append(match)
            seen_set.add(match)
    for p in record_pipelines:
        if p not in seen_set:
            seen.append(p)
            seen_set.add(p)
    return seen


# ---- Prior-tab metadata ------------------------------------------------------


def read_prev_metadata(sc, prev_tab_name):
    """Build {name_lower: {Tier, Assignee, moving status}} from the prior tab.
    Done? is intentionally not carried. Multi-record disambiguators
    ('Cato (Feed)') also register under their bare name ('Cato')."""
    if not prev_tab_name:
        return {}
    out = {}
    for r in sc.read_tab(prev_tab_name):
        name = (r.get("Company/Lead Name") or "").strip()
        if not name:
            continue
        if name.endswith("*"):
            name = name[:-1].strip()
        bare = re.sub(r"\s*\(.*\)\s*$", "", name).strip()
        meta = {
            "Tier": (r.get("Tier") or "").strip() or None,
            "Assignee": r.get("Assignee"),
            "moving status": r.get("moving status"),
        }
        for k in {name.lower(), bare.lower()}:
            out.setdefault(k, meta)
    return out


def lookup_metadata(prev_metadata, name):
    if not name:
        return {}
    n = name.strip()
    if n.endswith("*"):
        n = n[:-1].strip()
    key = n.lower()
    if key in prev_metadata:
        return prev_metadata[key]
    bare = re.sub(r"\s*\(.*\)\s*$", "", n).strip().lower()
    return prev_metadata.get(bare, {})


# ---- Sheet layout + formatting plan ----------------------------------------


def build_sheet_layout(records, prev_metadata, pipeline_order):
    """Return (rows, formats, data_rows). rows includes header + section/stage
    subheaders + data rows. formats are 1-indexed inclusive ranges with style
    hints. data_rows is the sorted list of 1-indexed row numbers that hold
    real data rows (i.e. NOT the header / section / stage subheader rows).
    Validation rules (dropdowns) are applied only to data_rows."""
    rows = [list(EXPECTED_HEADERS)]  # row 1 (header)
    formats = [{
        "range": {"start_row": 1, "end_row": 1, "start_col": 1, "end_col": len(EXPECTED_HEADERS)},
        "background": COLOR["header_bg"], "foreground": COLOR["header_text"], "bold": True,
    }]
    data_rows = []

    by_pipeline = {}
    for r in records:
        by_pipeline.setdefault(r["pipeline"], []).append(r)

    for pipeline in pipeline_order:
        prs = by_pipeline.get(pipeline, [])
        if not prs:
            continue
        # PIPELINE section header row.
        sec_row = [""] * len(EXPECTED_HEADERS)
        sec_row[COL["Company/Lead Name"] - 1] = f"PIPELINE: {pipeline_display_label(pipeline)}"
        rows.append(sec_row)
        formats.append({
            "range": {"start_row": len(rows), "end_row": len(rows),
                      "start_col": 1, "end_col": len(EXPECTED_HEADERS)},
            "background": COLOR["section_bg"],
            "foreground": COLOR["section_text"],
            "bold": True,
        })

        # Group by stage (preserve HubSpot's displayOrder).
        by_stage = {}
        for r in prs:
            by_stage.setdefault((r["stage_order"], r["stage"]), []).append(r)

        for (_order, stage), recs in sorted(by_stage.items()):
            stg_row = [""] * len(EXPECTED_HEADERS)
            stg_row[COL["Company/Lead Name"] - 1] = f"  {stage}"
            rows.append(stg_row)
            formats.append({
                "range": {"start_row": len(rows), "end_row": len(rows),
                          "start_col": 1, "end_col": len(EXPECTED_HEADERS)},
                "background": COLOR["stage_header_bg"],
                "italic": True, "bold": True,
            })
            for rec in sorted(recs, key=lambda x: (x["name"] or "").lower()):
                meta = lookup_metadata(prev_metadata, rec["name"])
                tier = meta.get("Tier") or "A"
                row_idx = len(rows) + 1
                data_rows.append(row_idx)
                rows.append([
                    tier,
                    rec["name"],
                    rec["stage"],
                    rec["status"],
                    rec["next_step"],
                    meta.get("Assignee") or "",
                    "",  # Done? blank for new week
                    meta.get("moving status") or "",
                ])
                # Stage cell color
                ck = stage_color_key(rec["stage"])
                formats.append({
                    "range": {"start_row": row_idx, "end_row": row_idx,
                              "start_col": COL["Deal/Lead Stage"],
                              "end_col": COL["Deal/Lead Stage"]},
                    "background": COLOR[ck],
                })
                # Tier cell color
                if tier == "A":
                    formats.append({
                        "range": {"start_row": row_idx, "end_row": row_idx,
                                  "start_col": COL["Tier"], "end_col": COL["Tier"]},
                        "background": COLOR["tier_a"], "bold": True,
                        "horizontal_alignment": "CENTER",
                    })
                elif tier == "B":
                    formats.append({
                        "range": {"start_row": row_idx, "end_row": row_idx,
                                  "start_col": COL["Tier"], "end_col": COL["Tier"]},
                        "background": COLOR["tier_b"],
                        "horizontal_alignment": "CENTER",
                    })
                # Unmapped name cell highlight
                if rec["name"].endswith("*"):
                    formats.append({
                        "range": {"start_row": row_idx, "end_row": row_idx,
                                  "start_col": COL["Company/Lead Name"],
                                  "end_col": COL["Company/Lead Name"]},
                        "background": COLOR["unmapped_marker"], "italic": True,
                    })
    return rows, formats, data_rows


def compress_to_ranges(sorted_indices):
    """[2,3,4, 7,8, 10] -> [(2,4), (7,8), (10,10)]"""
    if not sorted_indices:
        return []
    out = []
    s = e = sorted_indices[0]
    for i in sorted_indices[1:]:
        if i == e + 1:
            e = i
        else:
            out.append((s, e))
            s = e = i
    out.append((s, e))
    return out


def build_stage_dropdown_options(records):
    """Return the ordered list of stage names for the Deal/Lead Stage dropdown.

    Pulled from the live records (already filtered against EXCLUDED_STAGES) plus
    the priority list (so users can move a deal INTO a stage that's not yet
    represented in this week's tab — e.g. Closed Won before any deal lands).
    Stages in STAGE_DROPDOWN_PRIORITY come first in priority order; any extra
    stages observed in records are appended alphabetically.
    """
    seen = set()
    for r in records:
        if r["stage"] and r["stage"] not in EXCLUDED_STAGES:
            seen.add(r["stage"])
    # Always offer the priority stages, even if no live record sits there yet.
    universe = set(STAGE_DROPDOWN_PRIORITY) | seen
    ordered = [s for s in STAGE_DROPDOWN_PRIORITY if s in universe]
    extras = sorted(s for s in universe if s not in STAGE_DROPDOWN_PRIORITY)
    return ordered + extras


def build_validation_requests(data_rows, stage_options):
    """Return list of validation dicts for SheetsClient.apply_data_validations.

    Applied per-column (Tier, Stage, Assignee, Done?) to contiguous spans of
    data rows so dropdown arrows don't appear on the section/stage subheader
    rows.
    """
    if not data_rows:
        return []
    spans = compress_to_ranges(sorted(data_rows))
    columns = [
        ("Tier", TIER_OPTIONS),
        ("Deal/Lead Stage", stage_options),
        ("Assignee", ASSIGNEE_OPTIONS),
        ("Done?", DONE_OPTIONS),
    ]
    out = []
    for col_name, options in columns:
        if not options:
            continue
        col_idx = COL[col_name]
        for s, e in spans:
            out.append({
                "range": {"start_row": s, "end_row": e,
                          "start_col": col_idx, "end_col": col_idx},
                "values": list(options),
                "strict": False,
                "show_custom_ui": True,
            })
    return out


def write_snapshot(snapshot_dir, tab_name, monday, generated_at,
                   records, all_deals, all_leads, deal_pipelines, lead_pipelines):
    """Write the post-generation state to state/sheet-snapshots/{tab}.json.

    This is the BASE for the 3-way merge in tools/sheets/sheet-hubspot-merge.py:
      - sheet_rows: what generate-weekly-tab.py wrote into the tab. The merge
        compares the user-edited Sheet against this to detect Sheet-side edits.
      - hubspot_records: per-record (id, type, stage, status, next_step,
        hs_lastmodifieddate). The merge compares HubSpot's state against this
        to detect HubSpot-side edits ('hs_lastmodifieddate > generated_at'
        means HubSpot changed since the snapshot).
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    sheet_rows = []
    for r in records:
        sheet_rows.append({
            "name": r["name"],
            "mapping_key": r["mapping_key"],
            "type": r["type"],
            "id": r["id"],
            "pipeline_label": r["pipeline"],
            "stage_label": r["stage"],
            "status": r["status"],
            "next_step": r["next_step"],
        })

    def _record_snapshot(obj, object_type, pipelines):
        rid = str(obj.get("id"))
        props = obj.get("properties") or {}
        stage_id = props.get("dealstage") if object_type == "deal" else props.get("hs_pipeline_stage")
        info = pipelines.get(stage_id, {}) if stage_id else {}
        return {
            "id": rid,
            "type": object_type,
            "name": props.get("dealname") if object_type == "deal" else props.get("hs_lead_name"),
            "pipeline_id": info.get("pipeline_id"),
            "pipeline_label": info.get("pipeline_label"),
            "stage_id": stage_id,
            "stage_label": info.get("label"),
            "status": props.get("cyvore_weekly_status") or "",
            "next_step": (props.get("hs_next_step") if object_type == "deal" else props.get("cyvore_next_step")) or "",
            "hs_lastmodifieddate": props.get("hs_lastmodifieddate"),
        }

    hubspot_records = []
    for d in all_deals:
        hubspot_records.append(_record_snapshot(d, "deal", deal_pipelines))
    for ld in all_leads:
        hubspot_records.append(_record_snapshot(ld, "lead", lead_pipelines))

    payload = {
        "schema_version": 1,
        "tab_name": tab_name,
        "monday": monday.isoformat(),
        "generated_at": generated_at,
        "sheet_rows": sheet_rows,
        "hubspot_records": hubspot_records,
    }
    out_path = snapshot_dir / f"{tab_name}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def load_sheets_client():
    spec = importlib.util.spec_from_file_location(
        "sheets_client", REPO_ROOT / "tools" / "sheets" / "sheets-client.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--target-date", default=None,
                   help="Generate the tab for this date's Monday (YYYY-MM-DD). Default: this Monday.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite an existing tab with the same name")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute the plan without writing")
    p.add_argument("--config", default=None,
                   help="Path to tools/sheets/google-sheets-config.json")
    args = p.parse_args()

    if args.target_date:
        try:
            target = datetime.strptime(args.target_date, "%Y-%m-%d").date()
        except ValueError:
            die("--target-date must be YYYY-MM-DD", code=4)
    else:
        target = date.today()
    monday = this_monday(target)
    new_tab_name = fmt_tab(monday)
    sys.stderr.write(f"[generate-weekly-tab] Target Monday: {monday.isoformat()} -> tab {new_tab_name!r}\n")

    if not MAPPING_PATH.exists():
        die(f"mapping not found at {MAPPING_PATH.relative_to(REPO_ROOT)}")
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

    token = load_token()
    sys.stderr.write("[generate-weekly-tab] Fetching HubSpot pipelines...\n")
    deal_pipelines = fetch_pipelines(token, "deals")
    lead_pipelines = fetch_pipelines(token, LEADS_OBJECT_TYPE)

    sys.stderr.write("[generate-weekly-tab] Fetching all open deals + non-archived leads...\n")
    all_deals = fetch_all_objects(token, "deals", DEAL_PROPERTIES)
    all_leads = fetch_all_objects(token, LEADS_OBJECT_TYPE, LEAD_PROPERTIES)
    sys.stderr.write(
        f"[generate-weekly-tab] Got {len(all_deals)} deals + {len(all_leads)} leads (pre-filter).\n"
    )

    deal_inv, lead_inv, counts = build_inverse_mapping(mapping)
    records = build_records(deal_inv, lead_inv, counts,
                            all_deals, all_leads, deal_pipelines, lead_pipelines)
    sys.stderr.write(
        f"[generate-weekly-tab] After excluding {sorted(EXCLUDED_STAGES)}: {len(records)} records.\n"
    )
    pipeline_order = normalize_pipeline_order(records, DEFAULT_PIPELINE_ORDER)
    sys.stderr.write(f"[generate-weekly-tab] Pipeline order: {pipeline_order}\n")

    if args.dry_run:
        report = {
            "target_monday": monday.isoformat(),
            "new_tab_name": new_tab_name,
            "pipeline_order": pipeline_order,
            "records_count": len(records),
            "by_pipeline_stage": {},
            "unmapped_count": sum(1 for r in records if not r["mapping_key"]),
        }
        for p_name in pipeline_order:
            counts_in = {}
            for r in records:
                if r["pipeline"] != p_name:
                    continue
                counts_in[r["stage"]] = counts_in.get(r["stage"], 0) + 1
            report["by_pipeline_stage"][p_name] = dict(
                sorted(counts_in.items(), key=lambda kv: -kv[1])
            )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    sheets_module = load_sheets_client()
    sc = sheets_module.SheetsClient(args.config)

    tabs = sc.list_tabs()
    prev_tab = latest_tab_name([t for t in tabs if t != new_tab_name])
    sys.stderr.write(
        f"[generate-weekly-tab] Carrying Tier/Assignee/moving-status forward from prior tab: {prev_tab!r}\n"
    )
    prev_metadata = read_prev_metadata(sc, prev_tab) if prev_tab else {}

    if sc.tab_exists(new_tab_name) and not args.force:
        die(
            f"tab {new_tab_name!r} already exists in the Sheet. "
            "Use --force to overwrite, or pick a different --target-date.",
            code=4,
        )

    rows, formats, data_rows = build_sheet_layout(records, prev_metadata, pipeline_order)
    stage_options = build_stage_dropdown_options(records)
    validations = build_validation_requests(data_rows, stage_options)
    sys.stderr.write(
        f"[generate-weekly-tab] Built {len(rows)} rows + {len(formats)} format requests "
        f"+ {len(validations)} validation requests across {len(data_rows)} data rows.\n"
    )
    sys.stderr.write(f"[generate-weekly-tab] Stage dropdown options: {stage_options}\n")

    if sc.tab_exists(new_tab_name):
        sys.stderr.write(f"[generate-weekly-tab] Deleting existing {new_tab_name!r} (--force).\n")
        sc.delete_tab(new_tab_name)

    sc.create_tab(new_tab_name, rows=max(len(rows) + 5, 100), cols=len(EXPECTED_HEADERS))
    sc.write_full_tab(new_tab_name, rows, with_header=False)

    sys.stderr.write(f"[generate-weekly-tab] Applying {len(formats)} format requests...\n")
    sc.batch_update_format(new_tab_name, formats)

    if validations:
        sys.stderr.write(f"[generate-weekly-tab] Applying {len(validations)} dropdowns...\n")
        sc.apply_data_validations(new_tab_name, validations)

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    snapshot_path = write_snapshot(
        SNAPSHOT_DIR, new_tab_name, monday, generated_at,
        records, all_deals, all_leads, deal_pipelines, lead_pipelines,
    )
    sys.stderr.write(
        f"[generate-weekly-tab] Wrote merge snapshot -> "
        f"{snapshot_path.relative_to(REPO_ROOT)}\n"
    )

    summary = {
        "target_monday": monday.isoformat(),
        "new_tab_name": new_tab_name,
        "previous_tab_used_for_metadata": prev_tab,
        "records_written": len(records),
        "by_pipeline": {
            p_name: sum(1 for r in records if r["pipeline"] == p_name)
            for p_name in pipeline_order
        },
        "unmapped_in_output": sum(1 for r in records if not r["mapping_key"]),
        "sheet_url": sc.spreadsheet_url,
        "tab_url": sc.tab_url(new_tab_name),
        "snapshot_path": str(snapshot_path.relative_to(REPO_ROOT)),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
