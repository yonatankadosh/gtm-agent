# HubSpot Status Sync (owned by Sales)

## Role: the weekly outer-join consolidator — Sheet ∪ HubSpot → HubSpot

**This is the standard Monday flow for keeping the Cyvore GTM Weekly Sync Google Sheet and HubSpot in sync.** The Sheet is the live edit surface (laptop or phone, multi-person, real-time) — the user edits Sheet rows during the week to add new accounts, update stages, edit Status / Next Step, etc. **HubSpot is the system of record** — it never loses anything just because the Sheet changes. The primary write path for mid-week single-record edits direct from chat is [hubspot-quick-update.md](hubspot-quick-update.md).

The skill is implemented as a 3-step weekly cadence:

1. **All week:** user edits the current Sheet tab (mostly), and sometimes HubSpot directly (mid-week chat updates, etc.).
2. **Monday morning (or any time you want to consolidate):** run `tools/sheet-hubspot-merge.py` — the outer-join consolidator. It does a 3-way merge between (a) the Sheet at generation time = the snapshot in `state/sheet-snapshots/{tab}.json`, (b) the current Sheet, and (c) current HubSpot. It writes a plan + report and applies the plan via `tools/hubspot-batch.py`.
3. **Monday morning, after step 2:** run `tools/generate-weekly-tab.py` — generates the new week's tab from now-current HubSpot. Closed Lost / Disqualified records are filtered out. Tier / Assignee / moving-status are carried forward from the prior tab. A fresh snapshot is written to seed step 2 for next week.

**Outer-join discipline:** the consolidator never deletes from HubSpot. Removing a row from the Sheet is interpreted as "I don't want this on the meeting view this week," not "kill it." Hard kills still go through the explicit kill flow (`tools/hubspot-batch.py kill` or the Phase 4 batch path below).

## The 3-way merge model

For each row in the current Sheet, the consolidator classifies the row into one of:

| Classification | Meaning | Action |
|---|---|---|
| **NEW** | Row not in the prior snapshot, not in `state/hubspot-mapping.json`. | Propose `create-deal` or `create-lead` based on the row's Stage column (see *New row → object type / pipeline mapping* below). After apply, the new HubSpot ID is written back into the mapping. |
| **SHEET_EDIT_ONLY** | Sheet differs from snapshot, HubSpot's `hs_lastmodifieddate` ≤ snapshot's `generated_at`. | Push Sheet → HubSpot (`update` or `move`). |
| **HUBSPOT_EDIT_ONLY** | Sheet matches snapshot, HubSpot was modified mid-week. | No-op. HubSpot wins. The next generated tab will reflect HubSpot's current values (so the user sees the mid-week change next Monday). |
| **CONFLICT** | Both sides edited the same field differently. | **Sheet wins** (the user's chosen default). Logged in the report so the user sees what was overwritten and can correct it next week if needed. |
| **NO_CHANGE** | Neither side moved. | No-op. |
| **DELETED_FROM_SHEET** | Row was in the snapshot but is missing from the current Sheet. | **Preserve in HubSpot.** Outer-join rule. Surfaced in the report as a notice; hard kills go through the explicit kill flow. |
| **EXCLUDED_STAGE** | Sheet stage is `Closed Lost` / `Disqualified`. | Skipped. Use `tools/hubspot-batch.py kill` (or the Phase 4 batch path below) for explicit kills with audit-trail notes. |

The merge tool also handles four lower-priority diagnostic classes — `MAPPING_STALE` (mapping points to an archived/deleted HubSpot record), `STAGE_DRIFT_UNRESOLVED` (Sheet stage label can't be resolved in HubSpot's pipeline), `NEW_AMBIGUOUS` / `NEW_NO_PIPELINE` / `NEW_NO_STAGE` (a NEW row whose Stage column doesn't map to a HubSpot pipeline). All show up in `output/pipeline/{YYYY-WW}-merge-report.md`.

### New row → object type / pipeline mapping

The consolidator infers what to create from the row's **Stage** column (the dropdown values in column C):

| Stage in Sheet | Object type | Pipeline (substring match against HubSpot pipeline labels) |
|---|---|---|
| `New`, `Attempting`, `Connected`, `Qualified` | Lead | `BD & Leads` |
| `In meetings/conversations`, `Running POC`, `Finalizing the POC`, `Closed Won`, `CS` | Deal | `Sales` |
| `Negotiations`, `Collaborating` | Deal | `Collaborations & Partnerships` |

Stage IDs are resolved at runtime by querying HubSpot's pipelines API (so renames in HubSpot don't break the consolidator). If the Stage value isn't in the table above, the row is logged as `NEW_AMBIGUOUS` and skipped — fix it manually with `tools/hubspot-batch.py create-deal/create-lead` and then add the mapping entry.

## When to use which write path

Use this skill (the consolidator) when:

- Running the Monday weekly customer sync — outer-join the past week's edits.
- A batch of mid-week edits has accumulated in the Sheet.
- The HubSpot MCP is unavailable / errored — this skill's REST path (via `tools/hubspot-batch.py`) is the canonical recovery path.

For a single ad-hoc edit, prefer **hubspot-quick-update** — it's faster, the audit trail lands in the same `output/pipeline/{YYYY-WW}-sync-log.md` file.

The Monday meeting reliably involves **four operation types**, all covered by this skill (the consolidator emits the right plan items automatically; you can also build the plan by hand for unusual cases):

1. **Status / Next Step updates** on existing deals + leads
2. **Stage changes** — including kills (Closed Lost / Disqualified) and resurrections (e.g. Disqualified → Connected after re-engagement)
3. **New record creation** — leads from new meetings + deals when an account graduates from lead
4. **Note creation** — every kill carries a reason note as audit trail

### When to run this vs hubspot-quick-update

| Situation | Skill to run |
|---|---|
| Monday weekly customer sync meeting (full flow: updates + kills + creates + notes) | this skill |
| User edited the Sheet on Monday during the team meeting → push to HubSpot | this skill |
| User says "agent, update Cato: status X, next Y" mid-week | hubspot-quick-update |
| User says "log note on AT&T: ..." | hubspot-quick-update |
| User says "kill Mekorot reason: ..." or "move X to Running POC" (single record) | hubspot-quick-update |
| Killing > 5 records in a batch (e.g. CRM hygiene push) | this skill |
| First-time bootstrap of a new Sheet tab into HubSpot (rare) | this skill |
| Drift check: "is HubSpot in sync with the Sheet?" | this skill (read-only diff plan, then user decides whether to apply) |
| HubSpot MCP errored / disconnected | this skill — REST fallback via `tools/hubspot-batch.py` |

The two skills share the same write primitives and the same audit log file. Switching between them per request is cheap.

### Write paths: MCP-first, REST fallback

This skill has two equivalent write paths that produce identical HubSpot writes:

| Operation | MCP path (preferred when available) | REST fallback (always available) |
|---|---|---|
| Update deal/lead Status + Next Step | `manage_crm_objects.updateRequest` (deals) / `tools/hubspot-leads.py update\|batch` (leads) | `tools/hubspot-batch.py update --type {deal\|lead} --id N --prop K=V` |
| Move stage / kill | `manage_crm_objects.updateRequest` with new dealstage / hs_pipeline_stage | `tools/hubspot-batch.py {move\|kill}` |
| Create new deal | `manage_crm_objects.createRequest` | `tools/hubspot-batch.py create-deal --name "..." --stage in-meetings` |
| Create new lead (with primary Company association) | `manage_crm_objects.createRequest` with associations block | `tools/hubspot-batch.py create-lead --name "..." --stage connected` (auto-resolves company) |
| Log a Note | `manage_crm_objects.createRequest` with `objectType: "notes"` | `tools/hubspot-batch.py note --type {deal\|lead} --id N --body "..."` |
| Mixed batch | One `manage_crm_objects` call per object type | `tools/hubspot-batch.py batch --plan plan.json` |

**Always check MCP availability first.** If the HubSpot MCP `STATUS.md` shows "errored" / "Not connected", fall back to `tools/hubspot-batch.py` immediately — do NOT spend time debugging MCP during a live meeting. The REST tool uses the same Private App token (`tools/hubspot-config.json`), runs through the same audit-log discipline, and produces the same HubSpot record state.

## Purpose

Make the Cyvore GTM Weekly Sync Google Sheet a valid catch-up edit surface for `Status`, `Next Step`, kills, and creates, and push those changes into HubSpot in bulk so the team doesn't maintain parallel sources of truth.

This skill is owned by Sales (the only agent with HubSpot write access). It is run on demand — typically right after Yonatan's weekly customer sync meeting on Monday — when the user says "sync this week's tab to HubSpot" (or similar).

**Never silent.** Every HubSpot write goes through the explicit confirmation flow defined in `agents/sales/AGENT.md` ("HubSpot write rule"). The agent shows the full diff plan; the user replies "apply" before any MCP/REST write tool is invoked.

## Inputs

- **Cyvore GTM Weekly Sync Google Sheet** — the user-curated weekly tabs (one tab per `DD.MM.YYYY`). Configured at `tools/google-sheets-config.json` (sheet_id + service-account credentials). Read via `python3 tools/read-weekly-sync.py`. Replaces the deprecated `state/weekly-customer-sync.xlsx` archived under `state/archive/` after the 2026-W22 migration.
- **Sheet snapshot** at `state/sheet-snapshots/{tab-name}.json` — the post-generation BASE for the 3-way merge. Written automatically by `tools/generate-weekly-tab.py` on every successful run. If missing, the consolidator stops and asks you to regenerate the tab; fallback is the legacy manual flow.
- `state/hubspot-mapping.json` — hand-curated map from `Company/Lead Name` → HubSpot record IDs (deals + leads). The consolidator appends to this file on successful `create-deal` / `create-lead` ops.
- HubSpot CRM via the official Remote MCP server (`https://mcp.hubspot.com`) — for **Deals**
- HubSpot CRM via REST API (`/crm/v3/objects/0-136`) using a Private App token — for **Leads**

## Dependencies

### Required Private App scopes (verified 2026-05-18)

For the FULL set of operations (updates + kills + creates + notes), the Private App at `tools/hubspot-config.json` must have ALL of these scopes:

- `crm.objects.deals.read` + `crm.objects.deals.write`
- `crm.objects.leads.read` + `crm.objects.leads.write` (object `0-136` — MCP doesn't expose Leads, REST does)
- `crm.objects.contacts.write` (Lead-create needs primary Contact OR Company association)
- `crm.objects.companies.read` + `crm.objects.companies.write` (Lead-create's primary-company resolution needs both)
- `crm.schemas.leads.read` (read Lead pipeline definitions)

Earlier versions of this skill listed only the first two. The full list above is required for create flows. If a scope is missing, `tools/hubspot-batch.py` will surface a 403 with `MISSING_SCOPES` and the exact scope name — add it in HubSpot Settings → Integrations → Private Apps → your app → Auth tab → Save → re-run. No restart of Cursor needed for REST flows.

### Association typeIds (used by create + note flows)

Hard-coded in `tools/hubspot-batch.py`. Documented here so they're visible to the skill:

- Lead → Company (Primary): **580** (`labels` GET /crm/v4/associations/0-136/companies/labels confirms)
- Note → Deal: **214**
- Note → Lead (0-136): **855**

If HubSpot ever changes these, the tool prints the HTTP error verbatim and the fix is one-line.

### Field setup (one-time, manual)

The HubSpot MCP cannot create custom properties — `manage_crm_objects` is record CRUD only, not schema CRUD. So the Status property must be created in the HubSpot UI before the first run.

**Phase 1 (Deals — required before first run):**

1. HubSpot UI → Settings → Properties → select object **Deal** → **Create property**
2. Property name: `Cyvore Weekly Status` (internal name auto-derives to `cyvore_weekly_status`)
3. Field type: **Multi-line text**
4. Property group: `Deal Information`
5. Toggle **Track property history** = ON (so prior weekly values are preserved on the deal — this is the "audit trail" since we overwrite weekly)
6. Save

The built-in `hs_next_step` property already exists on Deal — no setup needed for Next Step.

**Phase 2 (Leads — required for syncing the early-funnel rows):**

The Lead object needs **two** custom properties because it has no built-in `hs_next_step` (that's Deal-only). Plus a Private App for REST access (the official HubSpot MCP doesn't expose Leads).

1. HubSpot UI → Settings → Integrations → Private Apps → **Create**. Scopes: `crm.objects.leads.read`, `crm.objects.leads.write`, `crm.objects.contacts.read`. (Note: `crm.schemas.leads.read` is not a real HubSpot scope — earlier plan was wrong.) Copy the access token.
2. Save the token at `tools/hubspot-config.json` (gitignored — same pattern as `tools/email-config.json`):

   ```json
   { "private_app_token": "pat-eu1-..." }
   ```

3. Create **two** custom properties on the Lead object via the HubSpot UI (Settings → Properties → Lead → Create property):
   - `cyvore_weekly_status` — Multi-line text, group "Lead Information", track property history ON. Holds xlsx Status.
   - `cyvore_next_step` — Multi-line text, group "Lead Information", track property history ON. Holds xlsx Next Step. (Symmetric to the Deal object's built-in `hs_next_step`.)

   These must be created in the UI because the Private App lacks `crm.schemas.*.write` scopes (HubSpot doesn't expose a Leads-schema scope to Private Apps as of 2026-05). `tools/hubspot-leads.py init-properties` is provided as a fallback for when/if HubSpot expands the scope set — it's idempotent.

### Mapping

`state/hubspot-mapping.json` (gitignored) keys every Sheet `Company/Lead Name` to its HubSpot record IDs. Format documented in the file's `_meta` block. Maintenance:

- When a new Sheet row is added → add a new entry (deals: [], leads: []) and fill IDs once the HubSpot record exists
- When a HubSpot deal name changes → no-op, IDs are stable
- When a deal goes Closed Won / Closed Lost → leave the mapping in place; the sync still writes Status + Next Step for post-close tracking (CS state)

## Field mapping

| Sheet column | HubSpot Deal property | HubSpot Lead property | Behavior |
|---|---|---|---|
| `Status` | `cyvore_weekly_status` (custom, multi-line text) | `cyvore_weekly_status` (custom, multi-line text) | Overwritten each weekly run; HubSpot's "Track property history" preserves prior values |
| `Next Step` | `hs_next_step` (built-in, ≤500 chars) | `cyvore_next_step` (custom, multi-line text — Lead object has no built-in next_step) | Overwritten each weekly run |
| `Deal/Lead Stage` | (read-only — `dealstage` for sanity check) | (read-only — `hs_pipeline_stage` for sanity check) | Sync flags drift, never auto-overwrites stage |
| `Tier`, `Done?`, `Assignee`, `moving status` | (not synced) | (not synced) | Out of scope for now |

**Why the asymmetry on Next Step:** the Deal object has a built-in `hs_next_step` property that HubSpot's UI surfaces natively in the deal sidebar. The Lead object has no equivalent — its only "next" properties are read-only calculation rollups tied to associated activities. So for Leads we add a custom `cyvore_next_step` to hold the same value. The sync skill knows which property to write per object type.

## Methodology — the consolidator path (preferred)

This is the new outer-join flow. It compresses the older manual 4-phase categorization into a single command, with the same explicit "show plan, wait for apply" gate.

### Step 1: Run the consolidator (dry-run by default)

```bash
python3 tools/sheet-hubspot-merge.py
```

This:
1. Picks the latest dated tab in the Sheet (or `--tab DD.MM.YYYY` to pick a specific one).
2. Reads its snapshot at `state/sheet-snapshots/{tab}.json` (the post-generation base, written by `generate-weekly-tab.py`).
3. Pulls current HubSpot deals + leads (with `hs_lastmodifieddate`) and pipelines.
4. For each Sheet row, applies the 3-way merge classification table above.
5. Writes:
   - `output/pipeline/{YYYY-WW}-merge-plan.json` — `hubspot-batch.py`-compatible plan.
   - `output/pipeline/{YYYY-WW}-merge-report.md` — per-row diff with classifications + the exact props that will be pushed.
6. Emits a JSON summary on stdout (counts per classification + paths).

**No HubSpot writes happen in step 1.** The consolidator is read-only by default.

### Step 2: Confirm with the user

Show the report's summary table (counts per classification) and the conflict / new-record sections. Ask the user to reply "apply" before proceeding. If the user wants to drop or edit specific rows from the plan, they edit `output/pipeline/{YYYY-WW}-merge-plan.json` by hand — then re-run with `--apply`.

### Step 3: Apply

```bash
python3 tools/sheet-hubspot-merge.py --apply
```

This re-runs the merge (in case the Sheet changed between steps 1 and 3), then invokes `tools/hubspot-batch.py batch --plan output/pipeline/{YYYY-WW}-merge-plan.json`. Per-op outcomes are written to `/tmp/hubspot-batch-result-<timestamp>.json`. After successful creates, the consolidator appends new HubSpot IDs to `state/hubspot-mapping.json` so the same accounts match by mapping key on subsequent runs.

### Step 4: Generate next week's tab

After the apply succeeds:

```bash
python3 tools/generate-weekly-tab.py
```

This pulls the (now updated) HubSpot state into a fresh tab, excludes Closed Lost / Disqualified, carries Tier / Assignee / moving-status forward from the prior tab, applies dropdowns + colors, and writes a new snapshot for the next consolidator cycle.

### Step 5: Append the apply result to the audit log

Append to `output/pipeline/{YYYY-WW}-sync-log.md`:

- `Applied at: {timestamp}` (from the consolidator summary)
- `Plan file: output/pipeline/{YYYY-WW}-merge-plan.json`
- `Report file: output/pipeline/{YYYY-WW}-merge-report.md`
- `Batch result: /tmp/hubspot-batch-result-<timestamp>.json` (link, with the per-row outcomes embedded so the file is self-contained even if `/tmp` is wiped)
- HubSpot record links for newly-created records.

The Sheet tab + this sync log + the merge report together form the per-week record of what was synced, which side won on each conflict, and what new records were created.

---

## Methodology — the legacy manual flow (fallback)

Use this only when the consolidator doesn't apply (e.g. no snapshot exists yet because this is the first run after the migration, or you're running against a dry-run sandbox without a snapshot). The 4-phase manual categorization below produces the same plan shape as the consolidator.

Run these steps in order. At every step, ask "**so what?**" — don't list facts without commercial interpretation.

### Step 0: Confirm scope (production vs dry-run)

The Sheet is the live edit surface — there's no upload step to disambiguate, so this only checks production vs sandbox:

> "Scope of this run — production (real HubSpot writes from the live Sheet) or dry-run (mock data, no HubSpot calls)?"

Resolutions:
- **Production** → read from the configured Sheet, apply to HubSpot.
- **Dry-run** → switch every read/write root to `dry-run/` per the gtm-agent rule; do not call HubSpot.

If the Mon 06:00 `generate-weekly-tab.py` cron has not fired yet (the team is meeting earlier than usual), the user can run it manually from chat: `python3 tools/generate-weekly-tab.py` — that materializes today's tab in the Sheet from current HubSpot state. This is purely additive; it never overwrites a tab the team has already edited (the `--force` flag is opt-in).

### Step 1: Read the latest Sheet tab

Run `python3 tools/read-weekly-sync.py` (no flags) — emits the latest tab as JSON to stdout. The user can also pass `--week YYYY-WW` to pin a specific week.

If the Sheet has no current-week tab or the tab schema doesn't match the 8 expected columns, stop and surface the error to the user. (The Sheet schema is unchanged from the xlsx era: `Tier | Company/Lead Name | Deal/Lead Stage | Status | Next Step | Assignee | Done? | moving status`.)

### Step 2: Read HubSpot state

**Deals (via MCP):** call `search_crm_objects` with `objectType: "deals"` and properties `["dealname", "dealstage", "hs_next_step", "cyvore_weekly_status", "hs_lastmodifieddate"]`. Filter to open + recently-closed (the same set the weekly pipeline review uses).

**Leads (via REST, Phase 2 only):** run `python3 tools/hubspot-leads.py list` — emits all Leads as JSON with `id`, `hs_lead_name`, `hs_pipeline_stage`, `cyvore_next_step`, `cyvore_weekly_status`.

If the Deal object is missing the `cyvore_weekly_status` property (i.e. the one-time setup hasn't been done), the MCP returns the deal without that field. Detect this and stop with a clear message — do not write to a property that doesn't exist; the MCP will reject it.

### Step 3: Match Sheet rows to HubSpot records

Load `state/hubspot-mapping.json`. For each Sheet row:

- Look up the row's `Company/Lead Name` as a key in the mapping
- Collect the list of `deals[]` and `leads[]` IDs
- If the row name is not in the mapping → flag as "unmapped" (don't fail the run; surface in the log so the user can add the mapping)
- If the row maps to one or more deals AND one or more leads → unusual, log a warning (a row should normally be in deals OR leads, not both)

### Step 4: Categorize every Sheet row into one of 4 phases

The Monday meeting always sorts Sheet rows into the same 4 phases. Build the plan in this order:

**Phase 1 — Status / Next Step updates** (existing mapped records):
- For each (Sheet row, HubSpot record) pair, compute the proposed write:
  - `cyvore_weekly_status` ← Sheet `Status` (skip if Sheet Status is empty AND HubSpot is empty; otherwise write — including writing empty to clear stale values)
  - For Deals: `hs_next_step` ← Sheet `Next Step`. For Leads: `cyvore_next_step` ← Sheet `Next Step`. (Same skip rule.)
- Skip rows where HubSpot already matches the Sheet (no-change rows surfaced in the log but not pushed).

**Phase 2 — New record creation** (Sheet rows NOT in mapping AND Sheet stage is not a kill):
- Decide deal vs. lead by stage:
  - Lead pipeline (`New / Attempting / Connected / Qualified`) → create Lead via `tools/hubspot-batch.py create-lead --name "..." --stage {stage}` (auto-resolves primary Company; passes `--company-domain` if known).
  - Deal pipeline (`In meetings/conversations` and beyond) → create Deal via `tools/hubspot-batch.py create-deal --name "..." --stage {stage}`.
- For each new record, also draft a `state/hubspot-mapping.json` entry (deal id, label, stage) to add after creation.

**Phase 3 — Stage changes / resurrections** (rows where Sheet stage differs from HubSpot stage AND it's not a kill):
- Most common: a Disqualified lead that came back to life after a meeting. Use `tools/hubspot-batch.py move --type lead --id N --to connected` (with optional `--prop cyvore_weekly_status=...`).

**Phase 4 — Kills** (rows whose `Next Step` cell is `kill` / `kill?`):
- Per row, derive a kill reason. Either ask the user once for a uniform reason ("Closed Lost at weekly customer sync 2026-WNN — no progression") or draft per-record reasons from the Sheet context.
- Apply via `tools/hubspot-batch.py kill --type {deal|lead} --id N --reason "..."` — this moves stage AND logs a Note in one call.

Also compute drift checks (read-only, not written):

- **Stage drift on existing rows:** Sheet `Deal/Lead Stage` vs HubSpot `dealstage` / `hs_pipeline_stage`. If different and NOT in Phase 3 (intentional resurrection), flag in the log.
- **Mapping freshness:** if a HubSpot deal exists with a name that fuzzy-matches an unmapped Sheet row, surface as "candidate mapping" suggestion before creating a duplicate.

Write the categorized plan to `output/pipeline/{YYYY-WW}-sync-log.md` using the schema below — one section per phase, one row per HubSpot operation, with current → new values for updates / proposed reason for kills / target stage for moves.

### Step 5: Confirm with the user

Summarize the diff in chat:

- N deals will be updated, M leads will be updated
- X stage-drift warnings
- Y unmapped xlsx rows

Show the per-row table from the log file. Ask the user to reply "apply" to proceed, or to edit specific rows.

### Step 6: Apply the writes

**Preferred path: one batch plan via `tools/hubspot-batch.py`.** Materialize the categorized phases (step 4) as a JSON plan and apply in one call:

```bash
python3 tools/hubspot-batch.py batch --plan /tmp/sync-plan-2026-WNN.json
```

Plan format (mixed ops, applied in order):

```json
[
  {"op": "update",      "type": "deal", "id": 412482110712, "props": {"hs_next_step": "..."}},
  {"op": "update",      "type": "lead", "id": 1198471582955, "props": {"cyvore_next_step": "..."}},
  {"op": "create-deal", "name": "WWT - Cyvore Suite", "stage": "in-meetings",
                        "props": {"cyvore_weekly_status": "...", "hs_next_step": "..."}},
  {"op": "create-lead", "name": "Microsoft", "stage": "connected",
                        "status": "...", "next_step": "...", "company_domain": "microsoft.com"},
  {"op": "move",        "type": "lead", "id": 1133614826738, "to": "connected",
                        "props": {"cyvore_weekly_status": "met again at axis"}},
  {"op": "kill",        "type": "deal", "id": 381006235888, "reason": "..."},
  {"op": "kill",        "type": "lead", "id": 1135197806819, "reason": "..."}
]
```

Order matters: do updates first, then creates, then moves, then kills (kills are irreversible — running them last gives the user one more confirmation point). Pass `--dry-run` first to preview every operation; then re-run without to apply.

**MCP path (when available):** the `tools/hubspot-batch.py` operations map 1:1 onto `manage_crm_objects.updateRequest` / `createRequest` calls. If the user prefers the MCP confirmation table, swap the tool calls and keep the same plan structure — the audit log section below is identical either way.

**Single-record fallbacks:** all CLI subcommands (`update / kill / move / note / create-deal / create-lead`) work standalone for ad-hoc fixes mid-run.

If any individual write fails, log the error in the sync log and continue with the rest — don't abort the whole run. The tool writes a per-run outcome JSON to `/tmp/hubspot-batch-result-<timestamp>.json` containing every operation's success / failure / HubSpot record link.

### Step 7: Append the apply result

Append to `output/pipeline/{YYYY-WW}-sync-log.md`:

- `Applied at: {timestamp}`
- Per-row outcome: success / failure (with HubSpot error message)
- HubSpot record links for each updated record

This is the audit trail. The Sheet tab + this sync log together form the per-week record of what was synced.

## Multi-deal company policy

Some companies have multiple HubSpot deals (Cato has Feed + Suite). Default behavior: the same Sheet Status + Next Step writes to **all** deals in the mapping's `deals[]` array. This is correct for paired/coupled efforts (Cato Feed and Suite share install effort).

If a company's deals diverge in trajectory (e.g. AT&T's Suite goes Q3 while ScanMySMS closes Q2), split the Sheet row into two during the next weekly meeting (e.g. "AT&T - Suite" and "AT&T - ScanMySMS") and update `state/hubspot-mapping.json` to map each row to its specific deal. The sync handles this transparently.

## Output Schema

`output/pipeline/{YYYY-WW}-sync-log.md`:

```
# HubSpot Sync Log — Week {YYYY-WW}

**Generated:** {date}
**Source tab:** {DD.MM.YYYY} (Cyvore GTM Weekly Sync Sheet)
**Mapping file:** state/hubspot-mapping.json
**Status:** {DRAFT — awaiting "apply" | APPLIED at {timestamp} | FAILED}

## Summary
- {N} deals will be updated (Status + Next Step)
- {M} leads will be updated
- {X} stage-drift warnings
- {Y} unmapped Sheet rows

## Proposed deal writes

| Sheet row | Deal | HubSpot ID | Field | Current | New |
|---|---|---|---|---|---|
| ... | ... | ... | cyvore_weekly_status | ... | ... |
| ... | ... | ... | hs_next_step | ... | ... |

## Proposed lead writes
(same schema)

## Stage drift warnings
- {Account}: Sheet says "Running POC", HubSpot says "Finalizing the POC". Action: align manually before next sync.

## Unmapped Sheet rows
- {Row}: not in state/hubspot-mapping.json. Add a HubSpot record (deal or lead) and update the mapping.

## Apply result
(populated in step 7 after user confirms)
- {Account}: success — https://app.hubspot.com/contacts/.../record/0-3/{id}
- {Account}: FAILED — {error message}
```

## Quality Checklist

- [ ] Snapshot at `state/sheet-snapshots/{tab}.json` exists for the tab being consolidated; if not, fall back to the legacy manual flow OR regenerate the tab
- [ ] Every Sheet row resolved to one of the eight classifications (NEW / SHEET_EDIT_ONLY / HUBSPOT_EDIT_ONLY / CONFLICT / NO_CHANGE / DELETED_FROM_SHEET / EXCLUDED_STAGE / MAPPING_STALE / *_NO_PIPELINE / *_NO_STAGE) — no silent drops
- [ ] No HubSpot write was issued before the user said "apply"
- [ ] CONFLICT rows are listed in the report with both the Sheet and HubSpot values — the user can see what got overwritten
- [ ] DELETED_FROM_SHEET rows were preserved in HubSpot (outer-join rule)
- [ ] If the `cyvore_weekly_status` property doesn't exist on the target object yet, the run halted with a clear setup-required message instead of failing silently
- [ ] After successful applies, `state/hubspot-mapping.json` was updated with new HubSpot IDs from `create-deal` / `create-lead` ops
- [ ] After the consolidator applied, `tools/generate-weekly-tab.py` was run to materialize the next week's tab + a fresh snapshot
- [ ] Sync log has both the proposed diff (pre-apply) AND the apply result (post-apply); filename uses ISO week (`{YYYY-WW}-sync-log.md`) and does not overwrite prior weeks
- [ ] HubSpot record links in the apply result are clickable

## Relationship to other skills

```
agents/sales/skills/hubspot-quick-update.md   →  PRIMARY write path. Single-record, free-form, mid-week.
agents/sales/skills/hubspot-status-sync.md    →  CONSOLIDATOR (this skill). Outer-join Sheet ∪ HubSpot → HubSpot, Monday morning.
tools/sheet-hubspot-merge.py                  →  the consolidator implementation (read+plan; --apply to push).
tools/generate-weekly-tab.py                  →  REVERSE direction. HubSpot → Sheet. Run after the consolidator on Monday.
agents/sales/skills/pipeline-maintenance.md   →  READ-ONLY. Reads HubSpot → weekly state-of-pipeline snapshot.
agents/chief-of-staff/skills/exec-comms.md    →  reads the pipeline snapshot for the weekly digest
agents/chief-of-staff/skills/weekly-context.md →  populates state/weekly-context.md (separate input, not synced to HubSpot)
```

### Snapshot files (the merge base)

`generate-weekly-tab.py` writes `state/sheet-snapshots/{tab-name}.json` after every successful tab generation. This file is the BASE for the 3-way merge in the consolidator:

- `sheet_rows[]` — exactly what was written into the tab (Company name, mapping key, type, id, pipeline label, stage label, status, next step). The consolidator compares the live Sheet against this to detect Sheet-side edits.
- `hubspot_records[]` — every open deal + non-archived lead at generation time, with `hs_lastmodifieddate`. The consolidator compares HubSpot's current `hs_lastmodifieddate` against `generated_at` to detect HubSpot-side mid-week edits.

`state/sheet-snapshots/` is gitignored (under `state/`). If the snapshot is missing for a given tab, the consolidator stops and asks you to regenerate the tab. The fallback is the *legacy manual flow* above (no 3-way merge — just push everything from the Sheet).

### The new weekly cadence (post-2026-W22 Sheet migration, post-bidirectional refactor)

1. **All week:** user edits the current Sheet tab (the laptop/phone artifact for the team). Adds new accounts as new rows (Stage column drives the Lead-vs-Deal classification on next consolidate). Updates Status / Next Step / Stage on existing rows. Optionally edits HubSpot directly via `hubspot-quick-update` or Telegram.
2. **Monday morning, before the team meeting:** run `tools/sheet-hubspot-merge.py` (dry-run). Show the user the report. After confirmation, re-run with `--apply`.
3. **Monday morning, after the consolidator:** run `tools/generate-weekly-tab.py`. New tab + fresh snapshot are written. The team reads this tab during the meeting.
4. **Mid-week:** all updates flow through `hubspot-quick-update` (Cursor chat) or the Telegram bot's `/update` / `/note` / `/stage` / `/kill` commands — OR directly in the Sheet (the consolidator picks them up next Monday).
5. **Anytime:** "run pipeline review" → pipeline-maintenance reads HubSpot → snapshot is always consistent with the live source.

Note on the previous Mon 06:00 cron (`com.cyvore.weekly-tab.plist`): retired. The consolidator must run BEFORE the next-tab generator, and that ordering is best driven from chat (the user reviews the merge report between steps 2 and 3). If a cron is later wanted, schedule the consolidator in `--dry-run` mode (no writes) to email the report to the user, then they ack and the agent runs `--apply` + the generator.
