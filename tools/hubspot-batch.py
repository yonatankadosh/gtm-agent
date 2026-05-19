#!/usr/bin/env python3
"""
HubSpot batch operations via REST — the fallback when the HubSpot MCP is
unavailable, and the standard tool for batch ops larger than a single record.

Auth: reads `tools/hubspot-config.json` Private App token. Required scopes for
the FULL set of operations (verified 2026-05-18):
    - crm.objects.deals.read+write
    - crm.objects.leads.read+write   (object 0-136 — MCP doesn't expose this)
    - crm.objects.contacts.write     (Lead-create needs a Contact OR Company association)
    - crm.objects.companies.read+write
    - (engagements / notes are covered by the deals + leads write scopes)

Subcommands:

    update                     Update properties on an existing deal/lead.
    kill                       Move to Closed Lost (deal) / Disqualified (lead) and log a Note.
    move                       Change stage on a deal/lead. (Use this for resurrections too.)
    note                       Log a HubSpot Note engagement on a deal/lead.
    create-deal                Create a new deal in a given pipeline + stage.
    create-lead                Create a new lead with auto-resolved primary Company association.
    batch --plan PATH          Apply a JSON plan with a mix of the above ops (preferred for the
                               weekly Monday flow). See "Plan format" below.

Each subcommand supports --dry-run (no writes).

Stage labels (canonical, mirrors agents/sales/skills/hubspot-quick-update.md):
    Deal stages       label                          id
    -------------     -----------------------------  ---------
    in-meetings       In meetings/conversations      3886559469
    finalizing        Finalizing the POC             3886559471
    running-poc       Running POC                    3886559472
    closed-won        Closed Won                     3886559473
    closed-lost       Closed Lost                    3889241322

    Lead stages       label             id
    -------------     ----------------  ----------------------
    new               New               new-stage-id
    attempting        Attempting        attempting-stage-id
    connected         Connected         connected-stage-id
    qualified         Qualified         qualified-stage-id
    disqualified      Disqualified      unqualified-stage-id

Association typeIds used:
    Lead -> Company (Primary):  580
    Note -> Deal:               214
    Note -> Lead (0-136):       855

Plan format (passed to `batch --plan PATH`):

    [
      {"op": "update",      "type": "deal", "id": 412482110712, "props": {"hs_next_step": "..."}},
      {"op": "update",      "type": "lead", "id": 1198471582955, "props": {"cyvore_next_step": "..."}},
      {"op": "kill",        "type": "deal", "id": 381006235888, "reason": "No internal sponsor"},
      {"op": "kill",        "type": "lead", "id": 1135197806819, "reason": "No engagement"},
      {"op": "move",        "type": "lead", "id": 1133614826738, "to": "connected",
                            "props": {"cyvore_weekly_status": "met again at axis"}},
      {"op": "create-deal", "name": "WWT - Cyvore Suite", "stage": "in-meetings",
                            "props": {"cyvore_weekly_status": "...", "hs_next_step": "..."}},
      {"op": "create-lead", "name": "Microsoft", "stage": "connected",
                            "status": "...", "next_step": "...",
                            "company_domain": "microsoft.com"},
      {"op": "note",        "type": "deal", "id": 412482110712, "body": "Manual note text"}
    ]

The `batch` command applies items in the listed order, prints per-row results,
and writes a JSON outcome file (`/tmp/hubspot-batch-result-<timestamp>.json`).
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "tools" / "hubspot-config.json"
API = "https://api.hubapi.com"
LEADS_OBJECT = "0-136"

DEAL_STAGES = {
    "in-meetings": "3886559469",
    "negotiations": "3886559470",
    "finalizing": "3886559471",
    "running-poc": "3886559472",
    "waiting-signing": "4131171546",
    "closed-won": "3886559473",
    "closed-lost": "3889241322",
}

LEAD_STAGES = {
    "new": "new-stage-id",
    "attempting": "attempting-stage-id",
    "connected": "connected-stage-id",
    "qualified": "qualified-stage-id",
    "disqualified": "unqualified-stage-id",
}

DEAL_PIPELINE = "2845272281"
LEAD_PIPELINE = "lead-pipeline-id"

ASSOC_LEAD_TO_COMPANY_PRIMARY = 580
ASSOC_NOTE_TO_DEAL = 214
ASSOC_NOTE_TO_LEAD = 855


def die(msg, code=2):
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def load_token():
    if not CONFIG_PATH.exists():
        die(f"Missing {CONFIG_PATH.relative_to(REPO)}")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    token = cfg.get("private_app_token")
    if not token:
        die(f"{CONFIG_PATH} has no 'private_app_token'.")
    return token


def http(token, method, path, body=None, query=None, allow_error=False):
    url = API + path
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
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        if allow_error:
            return {"_error": True, "code": e.code, "body": body_text}
        die(f"HubSpot API error: {method} {url} -> {e.code} {e.reason}\n{body_text[:600]}", code=3)
    except urllib.error.URLError as e:
        die(f"Network error: {e}", code=3)


def now_ms():
    return int(time.time() * 1000)


def deal_stage_id(label_or_alias):
    if label_or_alias in DEAL_STAGES:
        return DEAL_STAGES[label_or_alias]
    if label_or_alias in DEAL_STAGES.values():
        return label_or_alias
    by_label = {
        "in meetings/conversations": DEAL_STAGES["in-meetings"],
        "finalizing the poc": DEAL_STAGES["finalizing"],
        "running poc": DEAL_STAGES["running-poc"],
        "closed won": DEAL_STAGES["closed-won"],
        "closed lost": DEAL_STAGES["closed-lost"],
    }
    return by_label.get(label_or_alias.lower(), label_or_alias)


def lead_stage_id(label_or_alias):
    if label_or_alias in LEAD_STAGES:
        return LEAD_STAGES[label_or_alias]
    if label_or_alias in LEAD_STAGES.values():
        return label_or_alias
    return LEAD_STAGES.get(label_or_alias.lower(), label_or_alias)


# ---- Operations -------------------------------------------------------------

def op_update(token, args, item=None):
    item = item or args
    obj_type = item["type"]
    rec_id = str(item["id"])
    props = item.get("props") or {}
    if not props:
        return {"op": "update", "type": obj_type, "id": rec_id, "skipped": True, "reason": "no props"}
    object_path = "deals" if obj_type == "deal" else LEADS_OBJECT
    if getattr(args, "dry_run", False):
        return {"op": "update", "type": obj_type, "id": rec_id, "dry_run": True, "props": props}
    r = http(token, "PATCH", f"/crm/v3/objects/{object_path}/{rec_id}", {"properties": props}, allow_error=True)
    return {"op": "update", "type": obj_type, "id": rec_id, "ok": not r.get("_error"), "result": r}


def op_move(token, args, item=None):
    item = item or args
    obj_type = item["type"]
    rec_id = str(item["id"])
    to = item.get("to") or item.get("stage")
    if not to:
        return {"op": "move", "type": obj_type, "id": rec_id, "ok": False, "reason": "missing 'to' / 'stage'"}
    extra_props = item.get("props") or {}
    if obj_type == "deal":
        props = {"dealstage": deal_stage_id(to), **extra_props}
        path = f"/crm/v3/objects/deals/{rec_id}"
    else:
        props = {"hs_pipeline_stage": lead_stage_id(to), **extra_props}
        path = f"/crm/v3/objects/{LEADS_OBJECT}/{rec_id}"
    if getattr(args, "dry_run", False):
        return {"op": "move", "type": obj_type, "id": rec_id, "dry_run": True, "props": props}
    r = http(token, "PATCH", path, {"properties": props}, allow_error=True)
    return {"op": "move", "type": obj_type, "id": rec_id, "ok": not r.get("_error"), "result": r}


def op_note(token, args, item=None):
    item = item or args
    obj_type = item["type"]
    rec_id = str(item["id"])
    body_text = item.get("body") or item.get("note")
    if not body_text:
        return {"op": "note", "type": obj_type, "id": rec_id, "ok": False, "reason": "missing 'body'"}
    type_id = ASSOC_NOTE_TO_DEAL if obj_type == "deal" else ASSOC_NOTE_TO_LEAD
    payload = {
        "properties": {"hs_note_body": body_text, "hs_timestamp": str(now_ms())},
        "associations": [{"to": {"id": rec_id},
                          "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": type_id}]}],
    }
    if getattr(args, "dry_run", False):
        return {"op": "note", "type": obj_type, "id": rec_id, "dry_run": True, "payload": payload}
    r = http(token, "POST", "/crm/v3/objects/notes", payload, allow_error=True)
    return {"op": "note", "type": obj_type, "id": rec_id, "ok": not r.get("_error"),
            "note_id": (r or {}).get("id"), "result": r}


def op_kill(token, args, item=None):
    """Move to Closed Lost (deal) / Disqualified (lead) AND log a reason note."""
    item = item or args
    obj_type = item["type"]
    rec_id = str(item["id"])
    reason = item.get("reason")
    if not reason:
        return {"op": "kill", "type": obj_type, "id": rec_id, "ok": False, "reason": "missing 'reason'"}
    if obj_type == "deal":
        move_result = op_move(token, args, {"type": "deal", "id": rec_id, "to": "closed-lost"})
        note_body = f"Closed Lost — {reason}"
    else:
        move_result = op_move(token, args, {"type": "lead", "id": rec_id, "to": "disqualified"})
        note_body = f"Disqualified — {reason}"
    note_result = op_note(token, args, {"type": obj_type, "id": rec_id, "body": note_body})
    return {"op": "kill", "type": obj_type, "id": rec_id,
            "ok": move_result.get("ok") and note_result.get("ok"),
            "move": move_result, "note": note_result}


def op_create_deal(token, args, item=None):
    item = item or args
    name = item["name"]
    stage = item.get("stage", "in-meetings")
    props = {
        "dealname": name,
        "dealstage": deal_stage_id(stage),
        "pipeline": DEAL_PIPELINE,
        **(item.get("props") or {}),
    }
    if getattr(args, "dry_run", False):
        return {"op": "create-deal", "name": name, "dry_run": True, "props": props}
    r = http(token, "POST", "/crm/v3/objects/deals", {"properties": props}, allow_error=True)
    return {"op": "create-deal", "name": name, "ok": not r.get("_error"),
            "deal_id": (r or {}).get("id"), "result": r}


def find_or_create_company(token, name, domain=None, dry_run=False):
    """Return (company_id, how) where how in {'exact', 'fuzzy', 'created', 'dry_run'}."""
    body = {
        "filterGroups": [{"filters": [
            {"propertyName": "name", "operator": "CONTAINS_TOKEN", "value": name}
        ]}],
        "properties": ["name", "domain"], "limit": 5,
    }
    r = http(token, "POST", "/crm/v3/objects/companies/search", body, allow_error=True)
    if not r.get("_error"):
        for m in r.get("results", []):
            mname = (m.get("properties") or {}).get("name", "")
            if mname.lower() == name.lower():
                return m["id"], "exact"
        if r.get("results"):
            return r["results"][0]["id"], "fuzzy"
    # Need to create
    if dry_run:
        return None, "dry_run"
    cprops = {"name": name}
    if domain:
        cprops["domain"] = domain
    rc = http(token, "POST", "/crm/v3/objects/companies", {"properties": cprops}, allow_error=True)
    if rc.get("_error"):
        return None, f"create_failed: {rc.get('body','')[:200]}"
    return rc["id"], "created"


def op_create_lead(token, args, item=None):
    item = item or args
    name = item["name"]
    stage = item.get("stage", "connected")
    status = item.get("status", "")
    next_step = item.get("next_step") or item.get("next") or ""
    domain = item.get("company_domain")
    company_id = item.get("company_id")
    if not company_id:
        company_id, how = find_or_create_company(
            token, name, domain=domain, dry_run=getattr(args, "dry_run", False),
        )
        if company_id is None and getattr(args, "dry_run", False):
            return {"op": "create-lead", "name": name, "dry_run": True,
                    "would_resolve_company": "search-or-create"}
        if company_id is None:
            return {"op": "create-lead", "name": name, "ok": False, "reason": how}
    body = {
        "properties": {
            "hs_lead_name": name,
            "hs_pipeline_stage": lead_stage_id(stage),
            "cyvore_weekly_status": status,
            "cyvore_next_step": next_step,
            **(item.get("props") or {}),  # caller may override stage / pipeline / etc by exact HubSpot ID
        },
        "associations": [
            {"to": {"id": str(company_id)},
             "types": [{"associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": ASSOC_LEAD_TO_COMPANY_PRIMARY}]}
        ],
    }
    if getattr(args, "dry_run", False):
        return {"op": "create-lead", "name": name, "dry_run": True, "company_id": company_id, "body": body}
    r = http(token, "POST", f"/crm/v3/objects/{LEADS_OBJECT}", body, allow_error=True)
    return {"op": "create-lead", "name": name, "company_id": company_id,
            "ok": not r.get("_error"), "lead_id": (r or {}).get("id"), "result": r}


# ---- CLI --------------------------------------------------------------------

def parse_props(items):
    out = {}
    for it in items or []:
        if "=" not in it:
            die(f"--prop must be KEY=VALUE, got: {it!r}", code=4)
        k, v = it.split("=", 1)
        out[k.strip()] = v
    return out


def cmd_update(args):
    token = load_token()
    args.props = parse_props(args.prop)
    item = {"type": args.type, "id": args.id, "props": args.props}
    print(json.dumps(op_update(token, args, item), indent=2, ensure_ascii=False))


def cmd_kill(args):
    token = load_token()
    item = {"type": args.type, "id": args.id, "reason": args.reason}
    print(json.dumps(op_kill(token, args, item), indent=2, ensure_ascii=False))


def cmd_move(args):
    token = load_token()
    item = {"type": args.type, "id": args.id, "to": args.to,
            "props": parse_props(args.prop)}
    print(json.dumps(op_move(token, args, item), indent=2, ensure_ascii=False))


def cmd_note(args):
    token = load_token()
    item = {"type": args.type, "id": args.id, "body": args.body}
    print(json.dumps(op_note(token, args, item), indent=2, ensure_ascii=False))


def cmd_create_deal(args):
    token = load_token()
    item = {"name": args.name, "stage": args.stage, "props": parse_props(args.prop)}
    print(json.dumps(op_create_deal(token, args, item), indent=2, ensure_ascii=False))


def cmd_create_lead(args):
    token = load_token()
    item = {"name": args.name, "stage": args.stage, "status": args.status,
            "next_step": args.next_step, "company_domain": args.company_domain,
            "company_id": args.company_id}
    print(json.dumps(op_create_lead(token, args, item), indent=2, ensure_ascii=False))


def cmd_batch(args):
    token = load_token()
    plan_path = Path(args.plan)
    if not plan_path.exists():
        die(f"plan not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(plan, list):
        die("plan must be a JSON list", code=4)
    dispatch = {
        "update": op_update,
        "kill": op_kill,
        "move": op_move,
        "note": op_note,
        "create-deal": op_create_deal,
        "create-lead": op_create_lead,
    }
    results = []
    print(f"Applying {len(plan)} operations from {plan_path}...")
    for i, item in enumerate(plan, 1):
        fn = dispatch.get(item.get("op"))
        if not fn:
            res = {"index": i, "ok": False, "reason": f"unknown op: {item.get('op')!r}"}
        else:
            res = fn(token, args, item)
            res["index"] = i
        ok = res.get("ok") if not args.dry_run else True
        flag = "OK " if ok else ("DRY" if args.dry_run else "ERR")
        label = item.get("name") or item.get("id") or item.get("op")
        print(f"  [{i:>3}] {flag} {item.get('op'):<13} {item.get('type','-'):<6} {label}")
        results.append(res)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = Path(f"/tmp/hubspot-batch-result-{ts}.json")
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nDone. {sum(1 for r in results if r.get('ok'))} succeeded, "
          f"{sum(1 for r in results if r.get('ok') is False)} failed. "
          f"Outcome: {out_path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_dry_run(sp):
        sp.add_argument("--dry-run", action="store_true")

    su = sub.add_parser("update", help="Update properties on a deal/lead")
    su.add_argument("--type", required=True, choices=["deal", "lead"])
    su.add_argument("--id", required=True)
    su.add_argument("--prop", action="append", help="KEY=VALUE (may repeat)")
    add_dry_run(su)
    su.set_defaults(func=cmd_update)

    sk = sub.add_parser("kill", help="Move to Closed Lost / Disqualified + log reason note")
    sk.add_argument("--type", required=True, choices=["deal", "lead"])
    sk.add_argument("--id", required=True)
    sk.add_argument("--reason", required=True)
    add_dry_run(sk)
    sk.set_defaults(func=cmd_kill)

    sm = sub.add_parser("move", help="Change stage (use for resurrections too)")
    sm.add_argument("--type", required=True, choices=["deal", "lead"])
    sm.add_argument("--id", required=True)
    sm.add_argument("--to", required=True, help="Stage alias (in-meetings/connected/etc.)")
    sm.add_argument("--prop", action="append", help="KEY=VALUE (may repeat) — extra props to set")
    add_dry_run(sm)
    sm.set_defaults(func=cmd_move)

    sn = sub.add_parser("note", help="Log a HubSpot Note")
    sn.add_argument("--type", required=True, choices=["deal", "lead"])
    sn.add_argument("--id", required=True)
    sn.add_argument("--body", required=True)
    add_dry_run(sn)
    sn.set_defaults(func=cmd_note)

    scd = sub.add_parser("create-deal", help="Create a new deal")
    scd.add_argument("--name", required=True)
    scd.add_argument("--stage", default="in-meetings")
    scd.add_argument("--prop", action="append", help="KEY=VALUE (may repeat) — e.g. cyvore_weekly_status=...")
    add_dry_run(scd)
    scd.set_defaults(func=cmd_create_deal)

    scl = sub.add_parser("create-lead", help="Create a new lead with auto Company association")
    scl.add_argument("--name", required=True)
    scl.add_argument("--stage", default="connected")
    scl.add_argument("--status", default="")
    scl.add_argument("--next-step", dest="next_step", default="")
    scl.add_argument("--company-domain", dest="company_domain")
    scl.add_argument("--company-id", dest="company_id", help="Skip resolution; use this exact company")
    add_dry_run(scl)
    scl.set_defaults(func=cmd_create_lead)

    sb = sub.add_parser("batch", help="Apply a JSON plan with mixed ops")
    sb.add_argument("--plan", required=True)
    add_dry_run(sb)
    sb.set_defaults(func=cmd_batch)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
