#!/usr/bin/env python3
"""
HubSpot Leads REST wrapper.

The official HubSpot MCP server (`mcp.hubspot.com`) does NOT expose the Leads
object (object type `0-136`) as of 2026-05. The public CRM v3 REST API does.
This script bridges that gap — used by the hubspot-status-sync skill to read
and write Status + Next Step on early-funnel xlsx rows that live as HubSpot
Leads, not Deals.

Auth: reads a Private App access token from `tools/hubspot/hubspot-config.json`:

    { "private_app_token": "pat-eu1-..." }

Subcommands:

    list                      List all Leads (id, name, stage, next_step, status).
                              Outputs JSON to stdout.

    get --id N                Get one Lead's full property bag. JSON to stdout.

    update --id N \
           [--status "..."] \
           [--next-step "..."] \
           [--dry-run]        Update one Lead. Pass --dry-run to print the
                              request without sending.

    batch --plan PATH \
          [--dry-run]         Read a JSON plan (list of {id, properties: {...}})
                              and apply via HubSpot's batch update endpoint.
                              Used by the agent after the user has confirmed
                              the diff in `output/pipeline/{YYYY-WW}/sync-log.md`.

    init-properties           One-time setup: create the custom properties
                              `cyvore_weekly_status` and `cyvore_next_step`
                              on the Lead object. Idempotent — properties
                              that already exist are skipped.

                              Note: the Lead object has no built-in
                              `hs_next_step` (that's Deal-only). The skill
                              uses `cyvore_next_step` as the Lead-side
                              equivalent.

All write subcommands respect HubSpot's confirmation discipline:
- `update` and `batch` require explicit invocation (not auto-run).
- `--dry-run` always available for safety previews.
- The agent calling this script is expected to have already shown the diff
  to the user and gotten "apply" confirmation per the HubSpot write rule in
  agents/sales/AGENT.md.

Exit codes:
  0  success
  2  config / setup error (missing token, missing file, etc.)
  3  HubSpot API error
  4  validation error (bad CLI args, malformed plan)
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "tools" / "hubspot" / "hubspot-config.json"

API_BASE = "https://api.hubapi.com"
LEADS_OBJECT_TYPE = "0-136"

DEFAULT_PROPERTIES = [
    "hs_lead_name",
    "hs_pipeline_stage",
    "hs_lead_status",
    "cyvore_next_step",
    "cyvore_weekly_status",
    "hs_createdate",
    "hs_lastmodifieddate",
]

# Custom properties this skill expects on the Lead object. The Lead object
# has no built-in `hs_next_step` (that's Deal-only) so we add a symmetric
# `cyvore_next_step` property.
CUSTOM_PROPERTIES = [
    {
        "name": "cyvore_weekly_status",
        "label": "Cyvore Weekly Status",
        "type": "string",
        "fieldType": "textarea",
        "description": "Free-text status copied from the Cyvore GTM Weekly Sync Google Sheet by the hubspot-status-sync skill. Overwritten weekly; prior values preserved via property history.",
        "groupName": "leadinformation",
        "hasUniqueValue": False,
        "hidden": False,
        "formField": False,
    },
    {
        "name": "cyvore_next_step",
        "label": "Cyvore Next Step",
        "type": "string",
        "fieldType": "textarea",
        "description": "Free-text next step copied from the Cyvore GTM Weekly Sync Google Sheet by the hubspot-status-sync skill. Lead-side equivalent of the Deal object's built-in hs_next_step.",
        "groupName": "leadinformation",
        "hasUniqueValue": False,
        "hidden": False,
        "formField": False,
    },
]


def die(msg, code=2):
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def load_token():
    if not CONFIG_PATH.exists():
        die(
            f"Missing {CONFIG_PATH.relative_to(REPO_ROOT)}. Create a HubSpot Private App "
            "(Settings > Integrations > Private Apps) with scopes "
            "crm.objects.leads.read, crm.objects.leads.write, crm.schemas.leads.read, "
            "crm.objects.contacts.read. Save its access token as "
            '{ "private_app_token": "pat-..." } at the path above.'
        )
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{CONFIG_PATH} is not valid JSON: {e}")
    token = cfg.get("private_app_token")
    if not token or not isinstance(token, str):
        die(f"{CONFIG_PATH} is missing 'private_app_token' (string).")
    return token


def http(method, path, token, body=None, query=None, allow_404=False):
    """Single HTTP call to HubSpot. Returns parsed JSON (or None for 204).
    If allow_404 is True, returns None on a 404 response instead of exiting."""
    url = API_BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        if allow_404 and e.code == 404:
            return None
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        sys.stderr.write(
            f"HubSpot API error: {method} {url} -> HTTP {e.code} {e.reason}\n"
            f"Response body: {body_text}\n"
        )
        sys.exit(3)
    except urllib.error.URLError as e:
        die(f"Network error contacting HubSpot: {e}", code=3)


def cmd_list(args):
    token = load_token()
    properties = args.properties or DEFAULT_PROPERTIES
    out = []
    after = None
    while True:
        query = {
            "limit": 100,
            "properties": ",".join(properties),
            "archived": "false",
        }
        if after:
            query["after"] = after
        resp = http("GET", f"/crm/v3/objects/{LEADS_OBJECT_TYPE}", token, query=query)
        for record in resp.get("results", []):
            out.append(
                {
                    "id": record.get("id"),
                    "properties": record.get("properties", {}),
                    "createdAt": record.get("createdAt"),
                    "updatedAt": record.get("updatedAt"),
                    "url": f"https://app.hubspot.com/contacts/{args.portal_id}/record/{LEADS_OBJECT_TYPE}/{record.get('id')}"
                    if args.portal_id
                    else None,
                }
            )
        paging = resp.get("paging", {}).get("next", {})
        after = paging.get("after")
        if not after:
            break
        time.sleep(0.05)
    print(json.dumps({"total": len(out), "results": out}, indent=2, ensure_ascii=False))


def cmd_get(args):
    token = load_token()
    properties = args.properties or DEFAULT_PROPERTIES
    resp = http(
        "GET",
        f"/crm/v3/objects/{LEADS_OBJECT_TYPE}/{args.id}",
        token,
        query={"properties": ",".join(properties)},
    )
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def _build_update_properties(status, next_step):
    props = {}
    if status is not None:
        props["cyvore_weekly_status"] = status
    if next_step is not None:
        props["cyvore_next_step"] = next_step
    return props


def cmd_update(args):
    props = _build_update_properties(args.status, args.next_step)
    if not props:
        die("update requires at least one of --status or --next-step", code=4)
    payload = {"properties": props}
    if args.dry_run:
        print(json.dumps({"dry_run": True, "id": args.id, "payload": payload}, indent=2, ensure_ascii=False))
        return
    token = load_token()
    resp = http(
        "PATCH",
        f"/crm/v3/objects/{LEADS_OBJECT_TYPE}/{args.id}",
        token,
        body=payload,
    )
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_batch(args):
    plan_path = Path(args.plan)
    if not plan_path.exists():
        die(f"plan file not found: {plan_path}", code=4)
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"plan file is not valid JSON: {e}", code=4)

    if not isinstance(plan, list):
        die("plan must be a JSON list of {id, properties} objects", code=4)

    inputs = []
    for i, entry in enumerate(plan):
        if not isinstance(entry, dict):
            die(f"plan[{i}] is not a dict", code=4)
        rec_id = entry.get("id")
        props = entry.get("properties")
        if rec_id is None or not isinstance(props, dict) or not props:
            die(f"plan[{i}] must have 'id' and non-empty 'properties' dict", code=4)
        inputs.append({"id": str(rec_id), "properties": {k: ("" if v is None else str(v)) for k, v in props.items()}})

    if args.dry_run:
        print(json.dumps({"dry_run": True, "count": len(inputs), "inputs": inputs}, indent=2, ensure_ascii=False))
        return

    token = load_token()
    results = []
    for chunk_start in range(0, len(inputs), 100):
        chunk = inputs[chunk_start : chunk_start + 100]
        resp = http(
            "POST",
            f"/crm/v3/objects/{LEADS_OBJECT_TYPE}/batch/update",
            token,
            body={"inputs": chunk},
        )
        results.append(resp)
        time.sleep(0.05)
    print(
        json.dumps(
            {"applied": len(inputs), "responses": results}, indent=2, ensure_ascii=False
        )
    )


def cmd_init_properties(args):
    """Create the cyvore_weekly_status + cyvore_next_step custom properties
    on the Lead object. Idempotent — properties that already exist are
    skipped (and the operation succeeds)."""
    token = load_token()
    summary = []
    for prop in CUSTOM_PROPERTIES:
        existing = http(
            "GET",
            f"/crm/v3/properties/{LEADS_OBJECT_TYPE}/{prop['name']}",
            token,
            allow_404=True,
        )
        if existing and existing.get("name") == prop["name"]:
            summary.append({"property": prop["name"], "status": "exists"})
            continue
        resp = http(
            "POST",
            f"/crm/v3/properties/{LEADS_OBJECT_TYPE}",
            token,
            body=prop,
        )
        summary.append({"property": prop["name"], "status": "created", "label": resp.get("label")})
    print(json.dumps({"results": summary}, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_list = sub.add_parser("list", help="List all Leads")
    sp_list.add_argument("--properties", nargs="+", help="Property names to fetch (default: common set)")
    sp_list.add_argument("--portal-id", help="HubSpot portal ID — included in result URLs if provided")
    sp_list.set_defaults(func=cmd_list)

    sp_get = sub.add_parser("get", help="Get one Lead by ID")
    sp_get.add_argument("--id", required=True, help="Lead ID")
    sp_get.add_argument("--properties", nargs="+", help="Property names to fetch")
    sp_get.set_defaults(func=cmd_get)

    sp_update = sub.add_parser("update", help="Update one Lead's Status / Next Step")
    sp_update.add_argument("--id", required=True, help="Lead ID")
    sp_update.add_argument("--status", help="New value for cyvore_weekly_status")
    sp_update.add_argument("--next-step", dest="next_step", help="New value for cyvore_next_step (Lead-side; Deals use built-in hs_next_step)")
    sp_update.add_argument("--dry-run", action="store_true", help="Print the request without sending")
    sp_update.set_defaults(func=cmd_update)

    sp_batch = sub.add_parser(
        "batch",
        help="Batch update many Leads from a JSON plan: [{id, properties: {...}}, ...]",
    )
    sp_batch.add_argument("--plan", required=True, help="Path to JSON plan file")
    sp_batch.add_argument("--dry-run", action="store_true", help="Print the request without sending")
    sp_batch.set_defaults(func=cmd_batch)

    sp_init = sub.add_parser(
        "init-properties",
        help="One-time: create cyvore_weekly_status + cyvore_next_step custom properties on the Lead object (idempotent)",
    )
    sp_init.set_defaults(func=cmd_init_properties)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
