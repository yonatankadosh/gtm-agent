#!/usr/bin/env python3
"""
Outer-join consolidator: Sheet plus HubSpot to a single HubSpot write plan.

Direction: Sheet to HubSpot. The user edits the current Sheet tab during the
week (and sometimes HubSpot directly). This tool reconciles both sides into
one plan that hubspot-batch.py can apply.

Three-way merge model:

  base     = state/sheet-snapshots/{tab}.json (written by generate-weekly-tab
             at the moment the tab was generated; captures both the sheet
             rows AND the HubSpot record state at that moment)
  sheet    = current Google Sheet (live, user-edited)
  hubspot  = current HubSpot state (live)

For each sheet row we classify:

  - NEW                  Row not in base, not in mapping. Propose create-deal
                         or create-lead based on the row's Stage column.
  - SHEET_EDIT_ONLY      Sheet differs from base, HubSpot unchanged. Push
                         Sheet values to HubSpot (update / move).
  - HUBSPOT_EDIT_ONLY    Sheet matches base, HubSpot's hs_lastmodifieddate
                         is newer than the snapshot. No push; HubSpot wins.
                         The next generated tab will reflect HubSpot's
                         current values.
  - CONFLICT             Both sides edited. Default policy: SHEET WINS
                         (per the user's chosen rule). Logged in the report
                         so the user sees what was overwritten.
  - NO_CHANGE            Neither side moved.

Outer-join discipline: HubSpot records that have NO row in the current Sheet
are PRESERVED. Removing a row from the Sheet never deletes anything in
HubSpot. (Hard kills still go through the explicit Phase 4 / hubspot-batch
kill flow.)

Outputs (always):
  - output/pipeline/{YYYY-WW}-merge-plan.json    hubspot-batch.py compatible
  - output/pipeline/{YYYY-WW}-merge-report.md    human-readable diff report
  - JSON summary on stdout

Modes:
  --dry-run (default)  Build plan + report. Do not call HubSpot.
  --apply              Build plan, then invoke hubspot-batch.py to apply it.
                       After successful creates, append new HubSpot IDs to
                       state/hubspot-mapping.json so future rows match by
                       mapping key.

Usage:
    python3 tools/sheet-hubspot-merge.py
    python3 tools/sheet-hubspot-merge.py --tab 18.05.2026
    python3 tools/sheet-hubspot-merge.py --apply
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HS_CONFIG = REPO_ROOT / "tools" / "hubspot-config.json"
MAPPING_PATH = REPO_ROOT / "state" / "hubspot-mapping.json"
SNAPSHOT_DIR = REPO_ROOT / "state" / "sheet-snapshots"
PIPELINE_DIR = REPO_ROOT / "output" / "pipeline"
HUBSPOT_BATCH = REPO_ROOT / "tools" / "hubspot-batch.py"

API_BASE = "https://api.hubapi.com"
LEADS_OBJECT_TYPE = "0-136"

DEAL_PROPERTIES = [
    "dealname", "dealstage", "hs_next_step",
    "cyvore_weekly_status", "pipeline", "hs_lastmodifieddate",
]
LEAD_PROPERTIES = [
    "hs_lead_name", "hs_pipeline_stage", "hs_lead_status",
    "cyvore_next_step", "cyvore_weekly_status", "hs_lastmodifieddate",
]

# Stage labels we never write to HubSpot (defensive: these should not be in
# the Sheet either, but if a user types one in we surface it as a kill).
EXCLUDED_STAGES = {"Closed Lost", "Disqualified"}

# Map from the Sheet's Stage dropdown value -> (object_type, pipeline_match)
# pipeline_match is matched against pipeline labels (case- and punctuation-
# insensitive substring) at runtime so we resolve to the right HubSpot
# pipeline_id even if the user renames pipelines.
NEW_ROW_STAGE_RULES = {
    "CS":                          ("deal", "sales"),
    "Closed Won":                  ("deal", "sales"),
    "Running POC":                 ("deal", "sales"),
    "Finalizing the POC":          ("deal", "sales"),
    "In meetings/conversations":   ("deal", "sales"),
    "New":                         ("lead", "bd"),
    "Attempting":                  ("lead", "bd"),
    "Connected":                   ("lead", "bd"),
    "Qualified":                   ("lead", "bd"),
    "Negotiations":                ("deal", "collab"),
    "Collaborating":               ("deal", "collab"),
}


def die(msg, code=2):
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def load_token():
    if not HS_CONFIG.exists():
        die(f"Missing {HS_CONFIG.relative_to(REPO_ROOT)} (HubSpot Private App token)")
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
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        die(f"HubSpot API error: {method} {url} -> {e.code}\n{body_text[:600]}", code=3)


def fetch_pipelines(token, object_type):
    """stage_id -> {label, pipeline_id, pipeline_label, displayOrder}"""
    resp = http("GET", f"/crm/v3/pipelines/{object_type}", token)
    out = {}
    for pipeline in resp.get("results", []):
        for stage in pipeline.get("stages", []):
            out[stage["id"]] = {
                "label": stage.get("label") or stage["id"],
                "pipeline_id": pipeline["id"],
                "pipeline_label": pipeline.get("label") or pipeline["id"],
                "displayOrder": stage.get("displayOrder", 999),
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
            return out


def load_sheets_client():
    spec = importlib.util.spec_from_file_location(
        "sheets_client", REPO_ROOT / "tools" / "sheets-client.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def latest_dated_tab(sc):
    pat = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$")
    pairs = []
    for name in sc.list_tabs():
        m = pat.match(name)
        if not m:
            continue
        d, mo, y = (int(x) for x in m.groups())
        try:
            from datetime import date as _date
            pairs.append((name, _date(y, mo, d)))
        except ValueError:
            continue
    if not pairs:
        return None
    pairs.sort(key=lambda p: p[1])
    return pairs[-1][0]


def iso_week_of_tab(tab_name):
    m = re.match(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$", tab_name)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    from datetime import date as _date
    iy, iw, _ = _date(y, mo, d).isocalendar()
    return f"{iy:04d}-{int(iw):02d}"


def parse_iso_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            return datetime.fromtimestamp(int(s) / 1000.0)
        except (ValueError, TypeError):
            return None


def norm_pipeline_match(label):
    return re.sub(r"[^a-z0-9]", "", (label or "").lower())


def resolve_pipeline_id(deal_pipelines, lead_pipelines, match_key):
    """match_key in {'sales', 'bd', 'collab'} -> (object_type, pipeline_id, pipeline_label, stage_lookup)
    Falls back to None if no pipeline label matches the substring."""
    needle = {"sales": "sales", "bd": "bd", "collab": "collaborations"}[match_key]
    for pipelines, ot in ((deal_pipelines, "deal"), (lead_pipelines, "lead")):
        seen_pipes = {}
        for stage_id, info in pipelines.items():
            pid = info["pipeline_id"]
            seen_pipes.setdefault(pid, info["pipeline_label"])
        for pid, plabel in seen_pipes.items():
            if needle in norm_pipeline_match(plabel):
                stages = {info["label"]: stage_id for stage_id, info in pipelines.items()
                          if info["pipeline_id"] == pid}
                return ot, pid, plabel, stages
    return None


def strip_disambiguation_suffix(name):
    """'Cato (Suite)' -> ('Cato', 'Suite'). 'AT&T*' -> ('AT&T', None) and unmapped=True."""
    n = (name or "").strip()
    unmapped = False
    if n.endswith("*"):
        unmapped = True
        n = n[:-1].strip()
    label = None
    m = re.match(r"^(.*?)\s*\(([^()]+)\)\s*$", n)
    if m:
        n, label = m.group(1).strip(), m.group(2).strip()
    return n, label, unmapped


def strings_equal(a, b):
    return (a or "").strip() == (b or "").strip()


def diff_fields(current, base):
    """Return dict of fields that changed (from base to current). Compares on
    'stage_label', 'status', 'next_step'. 'name' is informational only."""
    out = {}
    for k in ("stage_label", "status", "next_step"):
        if not strings_equal(current.get(k), base.get(k)):
            out[k] = (base.get(k) or "", current.get(k) or "")
    return out


def hs_record_was_modified(rec, snapshot_generated_at):
    """rec is a current-HubSpot snapshot dict (with hs_lastmodifieddate).
    snapshot_generated_at is an ISO string from snapshot.generated_at."""
    rec_ts = parse_iso_dt(rec.get("hs_lastmodifieddate"))
    base_ts = parse_iso_dt(snapshot_generated_at)
    if rec_ts is None or base_ts is None:
        return False
    if rec_ts.tzinfo is None and base_ts.tzinfo is not None:
        rec_ts = rec_ts.replace(tzinfo=base_ts.tzinfo)
    if base_ts.tzinfo is None and rec_ts.tzinfo is not None:
        base_ts = base_ts.replace(tzinfo=rec_ts.tzinfo)
    return rec_ts > base_ts


def build_hubspot_state_index(deals, leads, deal_pipelines, lead_pipelines):
    """index by (type, id) -> normalized record dict (same shape as snapshot.hubspot_records)."""
    out = {}
    for d in deals:
        rid = str(d.get("id"))
        props = d.get("properties") or {}
        stage_id = props.get("dealstage")
        info = deal_pipelines.get(stage_id, {}) if stage_id else {}
        out[("deal", rid)] = {
            "id": rid, "type": "deal",
            "name": props.get("dealname"),
            "pipeline_id": info.get("pipeline_id"),
            "pipeline_label": info.get("pipeline_label"),
            "stage_id": stage_id,
            "stage_label": info.get("label"),
            "status": props.get("cyvore_weekly_status") or "",
            "next_step": props.get("hs_next_step") or "",
            "hs_lastmodifieddate": props.get("hs_lastmodifieddate"),
        }
    for ld in leads:
        rid = str(ld.get("id"))
        props = ld.get("properties") or {}
        stage_id = props.get("hs_pipeline_stage")
        info = lead_pipelines.get(stage_id, {}) if stage_id else {}
        out[("lead", rid)] = {
            "id": rid, "type": "lead",
            "name": props.get("hs_lead_name"),
            "pipeline_id": info.get("pipeline_id"),
            "pipeline_label": info.get("pipeline_label"),
            "stage_id": stage_id,
            "stage_label": info.get("label"),
            "status": props.get("cyvore_weekly_status") or "",
            "next_step": props.get("cyvore_next_step") or "",
            "hs_lastmodifieddate": props.get("hs_lastmodifieddate"),
        }
    return out


def classify_existing(sheet_row_now, base_row, hs_now, generated_at):
    """Return (classification, push_props, conflict_fields).

    Inputs are field-aligned dicts with keys: stage_label, status, next_step.
    """
    sheet_diff = diff_fields(sheet_row_now, base_row)
    hs_was_edited = hs_record_was_modified(hs_now, generated_at) if hs_now else False
    hs_diff = diff_fields(hs_now or {}, base_row)
    if hs_now and not hs_was_edited:
        hs_diff = {}

    if not sheet_diff and not hs_diff:
        return "NO_CHANGE", {}, []

    if sheet_diff and not hs_diff:
        return "SHEET_EDIT_ONLY", _push_props_from_sheet(sheet_row_now, hs_now), []

    if hs_diff and not sheet_diff:
        return "HUBSPOT_EDIT_ONLY", {}, []

    overlap = sorted(set(sheet_diff.keys()) & set(hs_diff.keys()))
    distinct_overlap = [k for k in overlap if sheet_diff[k][1] != hs_diff[k][1]]

    if not distinct_overlap:
        merged = _push_props_from_sheet(sheet_row_now, hs_now)
        return "SHEET_EDIT_ONLY", merged, []
    return "CONFLICT", _push_props_from_sheet(sheet_row_now, hs_now), distinct_overlap


def _push_props_from_sheet(sheet_row, hs_now):
    """Build the HubSpot props dict to push from a Sheet row. hs_now (the
    current HubSpot record) gives us the object type so we can pick the
    right next-step property name."""
    props = {}
    if "status" in sheet_row:
        props["cyvore_weekly_status"] = sheet_row.get("status") or ""
    next_step = sheet_row.get("next_step") or ""
    if hs_now and hs_now.get("type") == "lead":
        props["cyvore_next_step"] = next_step
    else:
        props["hs_next_step"] = next_step
    return props


def normalize_sheet_row(raw):
    """Pull just the fields we use from a SheetsClient.read_tab() row."""
    name_raw = (raw.get("Company/Lead Name") or "").strip()
    if not name_raw:
        return None
    full_name, dis_label, unmapped_marker = strip_disambiguation_suffix(name_raw)
    full_no_marker = name_raw[:-1].rstrip() if unmapped_marker else name_raw
    return {
        "raw_name": name_raw,
        "full_name": full_no_marker,
        "name": full_name,
        "label": dis_label,
        "unmapped_marker": unmapped_marker,
        "stage_label": (raw.get("Deal/Lead Stage") or "").strip(),
        "status": (raw.get("Status") or "").strip(),
        "next_step": (raw.get("Next Step") or "").strip(),
    }


def lookup_mapping_records(mapping, *candidates):
    """Try each candidate name in order; return the first match's records.
    Returns list of dicts: [{type, id, label}]."""
    entry = None
    for cand in candidates:
        if not cand:
            continue
        e = (mapping or {}).get(cand)
        if e and isinstance(e, dict):
            entry = e
            break
    if not entry:
        return []
    out = []
    for d in entry.get("deals") or []:
        if d.get("id") is not None:
            out.append({"type": "deal", "id": str(d["id"]), "label": d.get("label") or ""})
    for ld in entry.get("leads") or []:
        if ld.get("id") is not None:
            out.append({"type": "lead", "id": str(ld["id"]), "label": ld.get("label") or ""})
    return out


def pick_target_record(sheet_row, mapping_records, base_index):
    """Choose which HubSpot record this Sheet row targets when the mapping has
    multiple. Strategy:
      1. If the Sheet row has a disambiguation label -> match by mapping label
         (case-insensitive substring).
      2. If exactly one record in the mapping -> that record.
      3. If multiple -> pick the one whose base snapshot stage_label matches
         the Sheet row's current stage; else first.
    """
    if not mapping_records:
        return None
    if sheet_row.get("label"):
        needle = sheet_row["label"].lower()
        for m in mapping_records:
            if needle in (m.get("label") or "").lower():
                return m
    if len(mapping_records) == 1:
        return mapping_records[0]
    sheet_stage = sheet_row.get("stage_label") or ""
    for m in mapping_records:
        base = base_index.get((m["type"], m["id"]))
        if base and strings_equal(base.get("stage_label"), sheet_stage):
            return m
    return mapping_records[0]


def stage_id_for_label(pipelines, pipeline_id, label):
    for sid, info in pipelines.items():
        if info["pipeline_id"] == pipeline_id and strings_equal(info["label"], label):
            return sid
    return None


def build_plan(tab_rows, snapshot, mapping, deal_pipelines, lead_pipelines, hs_index):
    """Return (plan, report_entries, summary_counts).

    plan = list of items in hubspot-batch.py format.
    report_entries = per-row dicts for the markdown report.
    summary_counts = {'NEW': N, 'SHEET_EDIT_ONLY': N, ...}
    """
    plan = []
    report = []
    counts = {
        "NEW": 0, "SHEET_EDIT_ONLY": 0, "HUBSPOT_EDIT_ONLY": 0,
        "CONFLICT": 0, "NO_CHANGE": 0, "DELETED_FROM_SHEET": 0,
        "UNMAPPED_NO_BASE": 0, "EXCLUDED_STAGE": 0,
    }

    base_sheet_rows = {r["name"]: r for r in snapshot.get("sheet_rows", []) if r.get("name")}
    base_hubspot_index = {(r["type"], r["id"]): r for r in snapshot.get("hubspot_records", [])}
    generated_at = snapshot.get("generated_at")

    seen_sheet_keys = set()

    for raw in tab_rows:
        sr = normalize_sheet_row(raw)
        if not sr:
            continue
        seen_sheet_keys.add(sr["raw_name"])

        if sr["stage_label"] in EXCLUDED_STAGES:
            counts["EXCLUDED_STAGE"] += 1
            report.append({
                "name": sr["raw_name"], "classification": "EXCLUDED_STAGE",
                "note": f"Sheet stage is {sr['stage_label']!r}; use the kill flow (hubspot-batch.py kill) for explicit kills.",
            })
            continue

        mapping_records = lookup_mapping_records(mapping, sr["full_name"], sr["name"])

        if not mapping_records and sr["unmapped_marker"]:
            base_row = base_sheet_rows.get(sr["raw_name"])
            if base_row and base_row.get("id") and base_row.get("type"):
                target = {"type": base_row["type"], "id": str(base_row["id"]), "label": ""}
                mapping_records = [target]

        if not mapping_records:
            rule = NEW_ROW_STAGE_RULES.get(sr["stage_label"])
            if not rule:
                counts["UNMAPPED_NO_BASE"] += 1
                report.append({
                    "name": sr["raw_name"], "classification": "NEW_AMBIGUOUS",
                    "note": f"Stage {sr['stage_label']!r} not in NEW_ROW_STAGE_RULES; "
                            f"can't infer object type / pipeline. Skipping.",
                })
                continue
            obj_type, pipeline_match = rule
            resolved = resolve_pipeline_id(deal_pipelines, lead_pipelines, pipeline_match)
            if not resolved:
                counts["UNMAPPED_NO_BASE"] += 1
                report.append({
                    "name": sr["raw_name"], "classification": "NEW_NO_PIPELINE",
                    "note": f"Could not resolve pipeline {pipeline_match!r} in HubSpot. Skipping.",
                })
                continue
            res_obj_type, pid, plabel, stages = resolved
            if res_obj_type != obj_type:
                obj_type = res_obj_type
            stage_id = stages.get(sr["stage_label"])
            if not stage_id:
                counts["UNMAPPED_NO_BASE"] += 1
                report.append({
                    "name": sr["raw_name"], "classification": "NEW_NO_STAGE",
                    "note": f"Stage {sr['stage_label']!r} not present in pipeline {plabel!r}.",
                })
                continue
            counts["NEW"] += 1
            if obj_type == "deal":
                item = {
                    "op": "create-deal",
                    "name": sr["name"],
                    "stage": "in-meetings",
                    "props": {
                        "pipeline": pid,
                        "dealstage": stage_id,
                        "cyvore_weekly_status": sr["status"],
                        "hs_next_step": sr["next_step"],
                    },
                }
            else:
                item = {
                    "op": "create-lead",
                    "name": sr["name"],
                    "stage": "connected",
                    "status": sr["status"],
                    "next_step": sr["next_step"],
                    "props": {
                        "hs_pipeline_stage": stage_id,
                        "hs_pipeline": pid,
                    },
                }
            plan.append(item)
            report.append({
                "name": sr["raw_name"], "classification": "NEW",
                "note": f"Will create {obj_type} in pipeline {plabel!r}, stage {sr['stage_label']!r}.",
                "details": {"object_type": obj_type, "pipeline": plabel, "stage": sr["stage_label"]},
            })
            continue

        target = pick_target_record(sr, mapping_records, base_hubspot_index)
        hs_now = hs_index.get((target["type"], target["id"]))
        if not hs_now:
            counts["UNMAPPED_NO_BASE"] += 1
            report.append({
                "name": sr["raw_name"], "classification": "MAPPING_STALE",
                "note": f"Mapping points to {target['type']} id={target['id']} which is not in current "
                        f"HubSpot results (archived? deleted?). Skipping.",
            })
            continue

        base = base_hubspot_index.get((target["type"], target["id"])) or {}

        sheet_now = {
            "stage_label": sr["stage_label"], "status": sr["status"], "next_step": sr["next_step"],
        }
        sheet_base = base_sheet_rows.get(sr["raw_name"]) or {
            "stage_label": base.get("stage_label", ""),
            "status": base.get("status", ""),
            "next_step": base.get("next_step", ""),
        }

        classification, push_props, conflict_fields = classify_existing(
            sheet_now, sheet_base, hs_now, generated_at,
        )
        counts[classification] = counts.get(classification, 0) + 1

        if classification in ("SHEET_EDIT_ONLY", "CONFLICT") and push_props:
            stage_changed = not strings_equal(sheet_now["stage_label"], hs_now.get("stage_label"))
            if stage_changed:
                pipelines = deal_pipelines if target["type"] == "deal" else lead_pipelines
                target_pid = hs_now.get("pipeline_id")
                stage_id = stage_id_for_label(pipelines, target_pid, sheet_now["stage_label"])
                if stage_id:
                    plan.append({
                        "op": "move",
                        "type": target["type"],
                        "id": target["id"],
                        "to": stage_id,
                        "props": push_props,
                    })
                else:
                    plan.append({
                        "op": "update",
                        "type": target["type"],
                        "id": target["id"],
                        "props": push_props,
                    })
                    report.append({
                        "name": sr["raw_name"], "classification": "STAGE_DRIFT_UNRESOLVED",
                        "note": f"Sheet says stage {sheet_now['stage_label']!r} but no matching "
                                f"stage in pipeline {hs_now.get('pipeline_label')!r}; "
                                f"stage NOT moved. Status / next-step still pushed.",
                    })
            else:
                plan.append({
                    "op": "update",
                    "type": target["type"],
                    "id": target["id"],
                    "props": push_props,
                })

        report.append({
            "name": sr["raw_name"], "classification": classification,
            "target": f"{target['type']}#{target['id']}",
            "sheet_now": sheet_now,
            "hubspot_now": {
                "stage_label": hs_now.get("stage_label"),
                "status": hs_now.get("status"),
                "next_step": hs_now.get("next_step"),
                "hs_lastmodifieddate": hs_now.get("hs_lastmodifieddate"),
            },
            "base": {
                "stage_label": sheet_base.get("stage_label"),
                "status": sheet_base.get("status"),
                "next_step": sheet_base.get("next_step"),
            },
            "conflict_fields": conflict_fields,
            "push_props": push_props if classification in ("SHEET_EDIT_ONLY", "CONFLICT") else {},
        })

    for base_name in base_sheet_rows:
        if base_name not in seen_sheet_keys:
            counts["DELETED_FROM_SHEET"] += 1
            report.append({
                "name": base_name, "classification": "DELETED_FROM_SHEET",
                "note": "Row was in last week's snapshot but is missing from the current Sheet. "
                        "Outer-join rule: HubSpot record preserved (no kill).",
            })

    return plan, report, counts


def render_report_md(tab_name, snapshot, plan, report, counts, sheet_url):
    lines = []
    lines.append(f"# Sheet HubSpot Merge Plan -- tab {tab_name}")
    lines.append("")
    lines.append(f"- **Generated at:** {datetime.now().astimezone().isoformat(timespec='seconds')}")
    lines.append(f"- **Snapshot base:** {snapshot.get('generated_at')}")
    lines.append(f"- **Sheet:** {sheet_url}")
    lines.append(f"- **Operations in plan:** {len(plan)}")
    lines.append("")
    lines.append("## Summary by classification")
    lines.append("")
    lines.append("| Classification | Count | Action |")
    lines.append("|---|---:|---|")
    explanations = {
        "NEW": "Create in HubSpot",
        "SHEET_EDIT_ONLY": "Push Sheet -> HubSpot",
        "HUBSPOT_EDIT_ONLY": "No-op (HubSpot wins; reflected in next tab)",
        "CONFLICT": "Sheet wins (overwrites HubSpot edit)",
        "NO_CHANGE": "No-op",
        "DELETED_FROM_SHEET": "Preserve in HubSpot (outer-join rule)",
        "UNMAPPED_NO_BASE": "Skipped (need mapping or base info)",
        "EXCLUDED_STAGE": "Skipped (use kill flow for explicit kills)",
    }
    for k in ["NEW", "SHEET_EDIT_ONLY", "HUBSPOT_EDIT_ONLY", "CONFLICT",
              "NO_CHANGE", "DELETED_FROM_SHEET", "UNMAPPED_NO_BASE", "EXCLUDED_STAGE"]:
        lines.append(f"| {k} | {counts.get(k, 0)} | {explanations[k]} |")
    lines.append("")

    grouped = {}
    for r in report:
        grouped.setdefault(r["classification"], []).append(r)
    for k in ["NEW", "CONFLICT", "SHEET_EDIT_ONLY", "HUBSPOT_EDIT_ONLY",
              "NO_CHANGE", "DELETED_FROM_SHEET", "STAGE_DRIFT_UNRESOLVED",
              "EXCLUDED_STAGE", "MAPPING_STALE", "NEW_AMBIGUOUS",
              "NEW_NO_PIPELINE", "NEW_NO_STAGE"]:
        if k not in grouped:
            continue
        lines.append(f"## {k}")
        lines.append("")
        for r in grouped[k]:
            lines.append(f"### {r['name']}")
            lines.append("")
            if "target" in r:
                lines.append(f"- HubSpot record: `{r['target']}`")
            if "note" in r:
                lines.append(f"- {r['note']}")
            if "details" in r:
                d = r["details"]
                lines.append(f"- Will create: **{d['object_type']}** in **{d['pipeline']}** at stage **{d['stage']}**")
            if "sheet_now" in r:
                sn = r["sheet_now"]; hn = r["hubspot_now"]; b = r["base"]
                lines.append("")
                lines.append("| Field | Base (snapshot) | HubSpot now | Sheet now |")
                lines.append("|---|---|---|---|")
                for f in ("stage_label", "status", "next_step"):
                    lines.append(f"| {f} | {b.get(f) or ''} | {hn.get(f) or ''} | {sn.get(f) or ''} |")
                if r.get("conflict_fields"):
                    lines.append("")
                    lines.append(f"**Conflict on:** {', '.join(r['conflict_fields'])} -> Sheet wins.")
                if r.get("push_props"):
                    lines.append("")
                    lines.append("Will push:")
                    for pk, pv in r["push_props"].items():
                        lines.append(f"- `{pk}` = {pv!r}")
            lines.append("")
    return "\n".join(lines)


def update_mapping_with_creates(mapping, plan, batch_results):
    """For each successful create-deal / create-lead in batch_results, append
    the new ID to the matching mapping entry. Creates a new mapping entry if
    none exists. Returns a list of changes for logging."""
    changes = []
    by_index = {r.get("index", i + 1): r for i, r in enumerate(batch_results)}
    for i, item in enumerate(plan, 1):
        if item.get("op") not in ("create-deal", "create-lead"):
            continue
        result = by_index.get(i, {})
        if not result.get("ok"):
            continue
        name = item.get("name")
        new_id = result.get("deal_id") or result.get("lead_id")
        if not new_id:
            continue
        kind = "deals" if item["op"] == "create-deal" else "leads"
        entry = mapping.setdefault(name, {"deals": [], "leads": []})
        entry.setdefault(kind, []).append({"id": int(new_id), "label": ""})
        changes.append({"name": name, "kind": kind, "id": int(new_id)})
    return changes


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--tab", default=None,
                    help="Tab name to consolidate (DD.MM.YYYY). Default: latest dated tab.")
    ap.add_argument("--snapshot", default=None,
                    help="Path to snapshot JSON. Default: state/sheet-snapshots/{tab}.json")
    ap.add_argument("--config", default=None, help="Path to tools/google-sheets-config.json")
    ap.add_argument("--apply", action="store_true",
                    help="Apply the plan via hubspot-batch.py and update the mapping with new IDs.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build plan + report only (default behavior). Mutually exclusive with --apply.")
    args = ap.parse_args()

    if args.apply and args.dry_run:
        die("Use either --apply or --dry-run, not both.", code=4)

    sheets_module = load_sheets_client()
    sc = sheets_module.SheetsClient(args.config)

    tab_name = args.tab or latest_dated_tab(sc)
    if not tab_name:
        die("No dated tab found in the Sheet.")
    sys.stderr.write(f"[merge] Tab: {tab_name}\n")

    snap_path = Path(args.snapshot) if args.snapshot else (SNAPSHOT_DIR / f"{tab_name}.json")
    if not snap_path.exists():
        die(f"snapshot not found at {snap_path}. "
            "Did you run generate-weekly-tab.py for this tab?", code=4)
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    sys.stderr.write(f"[merge] Snapshot: {snap_path.relative_to(REPO_ROOT)} "
                     f"(generated_at={snapshot.get('generated_at')})\n")

    sys.stderr.write(f"[merge] Reading sheet rows...\n")
    raw_rows = sc.read_tab(tab_name)
    sys.stderr.write(f"[merge] Got {len(raw_rows)} data rows from sheet.\n")

    if not MAPPING_PATH.exists():
        die(f"mapping not found at {MAPPING_PATH.relative_to(REPO_ROOT)}")
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

    token = load_token()
    sys.stderr.write(f"[merge] Fetching HubSpot pipelines + objects...\n")
    deal_pipelines = fetch_pipelines(token, "deals")
    lead_pipelines = fetch_pipelines(token, LEADS_OBJECT_TYPE)
    all_deals = fetch_all_objects(token, "deals", DEAL_PROPERTIES)
    all_leads = fetch_all_objects(token, LEADS_OBJECT_TYPE, LEAD_PROPERTIES)
    sys.stderr.write(f"[merge] HubSpot: {len(all_deals)} deals + {len(all_leads)} leads.\n")

    hs_index = build_hubspot_state_index(all_deals, all_leads, deal_pipelines, lead_pipelines)

    plan, report, counts = build_plan(
        raw_rows, snapshot, mapping, deal_pipelines, lead_pipelines, hs_index,
    )

    yyyy_ww = iso_week_of_tab(tab_name) or "unknown-week"
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    plan_path = PIPELINE_DIR / f"{yyyy_ww}-merge-plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path = PIPELINE_DIR / f"{yyyy_ww}-merge-report.md"
    report_md = render_report_md(tab_name, snapshot, plan, report, counts, sc.spreadsheet_url)
    report_path.write_text(report_md, encoding="utf-8")

    sys.stderr.write(f"[merge] Plan: {plan_path.relative_to(REPO_ROOT)} ({len(plan)} ops)\n")
    sys.stderr.write(f"[merge] Report: {report_path.relative_to(REPO_ROOT)}\n")
    for k in ["NEW", "SHEET_EDIT_ONLY", "HUBSPOT_EDIT_ONLY", "CONFLICT",
              "NO_CHANGE", "DELETED_FROM_SHEET", "UNMAPPED_NO_BASE", "EXCLUDED_STAGE"]:
        if counts.get(k):
            sys.stderr.write(f"[merge]   {k}: {counts[k]}\n")

    summary = {
        "tab": tab_name,
        "iso_week": yyyy_ww,
        "snapshot_generated_at": snapshot.get("generated_at"),
        "plan_path": str(plan_path.relative_to(REPO_ROOT)),
        "report_path": str(report_path.relative_to(REPO_ROOT)),
        "ops_in_plan": len(plan),
        "counts": counts,
        "applied": False,
    }

    if args.apply:
        if not plan:
            sys.stderr.write("[merge] Plan is empty -- nothing to apply.\n")
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return
        sys.stderr.write(f"[merge] Applying {len(plan)} operations via hubspot-batch.py...\n")
        proc = subprocess.run(
            [sys.executable, str(HUBSPOT_BATCH), "batch", "--plan", str(plan_path)],
            capture_output=True, text=True,
        )
        sys.stderr.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            die(f"hubspot-batch.py exited with code {proc.returncode}", code=proc.returncode)

        result_glob = sorted(Path("/tmp").glob("hubspot-batch-result-*.json"),
                             key=lambda p: p.stat().st_mtime, reverse=True)
        if result_glob:
            batch_results = json.loads(result_glob[0].read_text(encoding="utf-8"))
            mapping_changes = update_mapping_with_creates(mapping, plan, batch_results)
            if mapping_changes:
                MAPPING_PATH.write_text(
                    json.dumps(mapping, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                sys.stderr.write(
                    f"[merge] Updated mapping with {len(mapping_changes)} new HubSpot IDs.\n"
                )
                summary["mapping_changes"] = mapping_changes
            summary["batch_result_file"] = str(result_glob[0])
        summary["applied"] = True

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
