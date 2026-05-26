# HubSpot Quick Update (owned by Sales)

## Purpose

Mid-week, single-record edits to HubSpot. Free-form natural-language trigger ("update Cato — install done, sign next week"); single-row scope; explicit per-record confirmation. The xlsx is no longer the edit surface — HubSpot is the live source of truth, and the Cyvore GTM Weekly Sync Google Sheet (the Monday meeting tab) is regenerated weekly from HubSpot state by `tools/sheets/generate-weekly-tab.py`.

This is the **primary write path** for ad-hoc updates. The sibling skill [hubspot-status-sync.md](hubspot-status-sync.md) is the **catch-up path** — used after the Monday meeting if anyone hand-edited the xlsx during review.

**Never silent.** Every HubSpot write goes through the explicit confirmation flow defined in `agents/sales/AGENT.md` ("HubSpot write rule"). Show the proposed write in plain language. Wait for an affirmative ("yes" / "apply" / "go"). Only then call the MCP / REST write tool.

## Inputs

- The user's free-form message (one of the four trigger phrases below)
- `state/hubspot-mapping.json` — xlsx-name → HubSpot record IDs (deals + leads)
- HubSpot CRM via the MCP (deals) and REST (leads, via `tools/hubspot/hubspot-leads.py`)

## Trigger phrases

The Orchestrator routes any of these to Sales (this skill). All four share the same lookup → confirm → write → log loop.

| Trigger paraphrase | Operation | HubSpot fields touched |
|---|---|---|
| `update {account}: status X, next Y` (also: `quick update`, `set X for {account}`) | Write Status + Next Step on the resolved record(s) | `cyvore_weekly_status`, `hs_next_step` (deal) / `cyvore_next_step` (lead) |
| `log note on {account}: {text}` (also: `note for {account}`, `log call/email on {account}`) | Create a HubSpot Note (engagement) and associate to the record | new `notes` object via `manage_crm_objects` (deals); via REST for leads |
| `move {account} to {stage}` (also: `promote/demote {account} to {stage}`) | Change deal stage / lead pipeline stage | `dealstage` (deal) / `hs_pipeline_stage` (lead) |
| `kill {account} reason: X` (also: `close lost {account}`, `disqualify {account}`) | Move record to Closed Lost (deal) or Disqualified (lead) and log a note with the reason | `dealstage`=closedlost or `hs_pipeline_stage`=`unqualified-stage-id` + a Note for the reason |

Variants of any trigger should still route here — the agent is responsible for normalizing the user's intent.

## Methodology

### Step 1: Resolve `{account}` to a HubSpot record

Load `state/hubspot-mapping.json`. Resolve the user's `{account}` string in this order:

1. **Exact key match** in the mapping (case-sensitive — xlsx names are verbatim, including Hebrew + special chars).
2. **Case-insensitive substring match** — e.g. user says "cato" → resolves to `Cato Networks`. If multiple keys match, ask which.
3. **Fuzzy match (≥0.7 ratio)** as last resort. Always confirm the resolved name back to the user before writing.

If the resolved entry has multiple deals (Cato Networks → Feed + Suite), the default is **write to all** (matches the multi-deal policy from `hubspot-status-sync.md`). The user can override per command: "update Cato Suite only: status X" → match by label.

If the resolved entry has both `deals[]` and `leads[]`: prefer the deal (deal beats lead — deals represent active commercial conversations). Surface the duplication as a warning.

If no match: do NOT silently fail. Reply: "I don't have `{account}` in `state/hubspot-mapping.json`. Did you mean one of: <closest 3 fuzzy matches>? Or should I create a new record?" The "create a new record" path uses the same flow as the [Phase 2 lead bootstrap pattern from 2026-05-13](../../output/pipeline/2026-19/sync-log.md) — search HubSpot Companies/Contacts first, then create what's missing, then create the Lead.

### Step 2: Build the proposed write

For each operation:

**Update Status + Next Step:**
- Field: `cyvore_weekly_status` ← `{X}` (xlsx Status)
- Field: `hs_next_step` (deal) or `cyvore_next_step` (lead) ← `{Y}` (xlsx Next Step)
- Empty values are written as empty strings (intentionally clears prior values).
- Optional: also append a HubSpot Note with the same `{X} / {Y}` text and the date — useful for full audit trail beyond just the property history.

**Log a note:**
- Create a HubSpot `notes` engagement with `hs_note_body` = `{text}`, `hs_timestamp` = now.
- Associate to the deal/lead (and through it, to the company/contact).

**Move to stage:**
- Map the user's stage label ("Running POC", "Finalizing the POC", "Closed Won", etc.) to the canonical HubSpot stage ID. Use the canonical mapping table below (mirrors `agents/sales/skills/pipeline-maintenance.md`).
- For deals: write `dealstage` = `<stage-id>`.
- For leads: write `hs_pipeline_stage` = `<stage-id>`.
- Reject unknown stage labels — show the user the canonical list.

**Kill:**
- For deals: write `dealstage` = `closedlost` (or pipeline `2845272281`'s closed-lost stage ID `3889241322`) + create a HubSpot Note with `hs_note_body` = `Closed Lost — {reason}`.
- For leads: write `hs_pipeline_stage` = `unqualified-stage-id` + Note with the reason.
- The reason note is mandatory — if the user didn't supply one, ask before proceeding.

### Step 3: Show the proposed write in chat

Single-record edit, so the confirmation is one short paragraph (not a multi-row table):

```
About to update Cato Networks (deals: Feed + Suite, ids 462791538890 + 383681402097):
  cyvore_weekly_status = "install done"
  hs_next_step         = "sign next week"
Reply "apply" to write to both deals.
```

For multi-deal companies, the confirmation explicitly lists each deal that will be written. The user can override with "Suite only" / "Feed only" before saying apply.

### Step 4: Wait for an explicit affirmative

Acceptable affirmatives: `apply`, `yes`, `go`, `do it`, `confirm`. Anything else is treated as a redirect — re-parse and present a new proposal, or stop.

### Step 5: Apply the write

Two equivalent paths — pick MCP if available, REST otherwise. Both produce identical HubSpot state.

**MCP path (preferred when available):**
- **Deals:** call `manage_crm_objects.updateRequest` with `confirmationStatus: "CONFIRMED"`. The MCP enforces its own confirmation table — treat it as a second-line guard.
- **Leads:** run `python3 tools/hubspot/hubspot-leads.py update --id N --status "X" --next-step "Y"` (or `batch --plan PATH` for multi-lead writes).
- **Note creation:** call `manage_crm_objects.createRequest` with `objectType: "notes"` + association block to the deal/lead. For leads, fall back to the REST `/crm/v3/objects/notes` endpoint.

**REST path (when MCP is errored / for any operation MCP doesn't expose):** use `tools/hubspot/hubspot-batch.py` — one CLI for every single-record operation:

```bash
python3 tools/hubspot/hubspot-batch.py update     --type {deal|lead} --id N --prop hs_next_step="..." [--prop ...]
python3 tools/hubspot/hubspot-batch.py move       --type {deal|lead} --id N --to {stage-alias}
python3 tools/hubspot/hubspot-batch.py note       --type {deal|lead} --id N --body "..."
python3 tools/hubspot/hubspot-batch.py kill       --type {deal|lead} --id N --reason "..."   # move + note in one call
python3 tools/hubspot/hubspot-batch.py create-deal --name "..." --stage in-meetings [--prop ...]
python3 tools/hubspot/hubspot-batch.py create-lead --name "..." --stage connected --status "..." --next-step "..." [--company-domain ...]
```

Stage aliases: `in-meetings / finalizing / running-poc / closed-won / closed-lost` (deals) and `new / attempting / connected / qualified / disqualified` (leads). The tool resolves them to canonical HubSpot stage IDs internally.

If the write fails, surface the HubSpot error verbatim and stop. Do not retry silently. For batch ops > 1 record, switch to [hubspot-status-sync.md](hubspot-status-sync.md) and use `tools/hubspot/hubspot-batch.py batch --plan PATH`.

### Step 6: Log the edit to the weekly sync log

Append a one-line entry to [output/pipeline/{YYYY-WW}/sync-log.md](../../output/pipeline/) — use the current ISO week. Format:

```
- {timestamp IDT}: quick-update on {account} ({deal_id|lead_id}): cyvore_weekly_status="X", hs_next_step="Y" — applied. https://app.hubspot.com/contacts/.../record/0-3/{id}
```

If the file doesn't exist for this week yet, create it with a minimal header:

```
# HubSpot Sync Log — Week {YYYY-WW}

**Type:** Quick-updates (mid-week, single-record edits via hubspot-quick-update skill).
The Monday batch sync log (if any) is appended to this same file.

## Quick-update entries

(entries appended below by each invocation)
```

This keeps the audit trail in one place per week — quick-updates and Monday batch syncs share the file. The file is the source of truth for "what changed in HubSpot this week."

## Stage label canonical map

The user's natural-language stage labels map to HubSpot stage IDs as follows (verified 2026-05-13 against pipeline `2845272281`):

**Deal stages:**

| Yonatan label | HubSpot dealstage ID |
|---|---|
| `In meetings/conversations` | `3886559469` |
| `Finalizing the POC` | `3886559471` |
| `Running POC` | `3886559472` |
| `Closed Won` | `3886559473` |
| `Closed Lost` | `3889241322` |

**Lead stages (Cyvore BD & Leads pipeline):**

| Yonatan label | HubSpot hs_pipeline_stage |
|---|---|
| `New` | `new-stage-id` |
| `Attempting` | `attempting-stage-id` |
| `Connected` | `connected-stage-id` |
| `Qualified` | `qualified-stage-id_233247981` (rare — used when graduating to Deal) |
| `Disqualified` / `kill` | `unqualified-stage-id` |

Aliases: "lost" / "closed lost" / "killed" / "dead" all → Closed Lost (deal) or Disqualified (lead). "Won" / "closed won" / "signed" → Closed Won.

## Quality Checklist

- [ ] Account name was resolved (or surfaced as "not found" with fuzzy suggestions — never silently picked the wrong record)
- [ ] For multi-deal companies, the confirmation listed every deal that will be touched
- [ ] No write was issued before the user said "apply" / "yes" / equivalent
- [ ] Stage labels were normalized to canonical HubSpot IDs (rejecting unknown labels)
- [ ] Kill operations included a reason — either provided by user or asked-and-received
- [ ] Sync log entry was appended to `output/pipeline/{YYYY-WW}/sync-log.md`
- [ ] HubSpot record link in the log is clickable

## Relationship to other skills

```
agents/sales/skills/hubspot-quick-update.md   →  PRIMARY write path. Mid-week, free-form, single-record. (this skill)
agents/sales/skills/hubspot-status-sync.md    →  MONDAY MEETING write path. Batch sync from the Cyvore GTM Weekly Sync Sheet → HubSpot.
tools/sheets/generate-weekly-tab.py           →  REVERSE direction: HubSpot → Sheet (Monday morning, regenerates the team's weekly tab).
agents/sales/skills/pipeline-maintenance.md   →  READ-ONLY weekly snapshot. Reflects whatever this skill (and the Monday meeting skill) wrote during the week.
```

When in doubt about which write path to use:

- **Single record, ad-hoc, "I just talked to X"** → quick-update (this skill)
- **Whole batch from the Sheet, post-Monday-meeting** → hubspot-status-sync (sibling skill)
- **Need to know what changed this week** → read `output/pipeline/{YYYY-WW}/sync-log.md`
- **Need to refresh this week's tab in the Sheet from HubSpot** → run `python3 tools/sheets/generate-weekly-tab.py`

## Examples

### Example 1: Status + Next Step

User: `update Cato: status install complete, next sign next week`

Agent:
```
About to update Cato Networks (2 deals: Cyvore Feed id 462791538890 + Cyvore Suite id 383681402097):
  cyvore_weekly_status = "install complete"
  hs_next_step         = "sign next week"

Reply "apply" to write to both deals, or "Feed only" / "Suite only" to scope.
```

User: `apply`

Agent: writes both deals via MCP, confirms success with HubSpot links, appends to sync log.

### Example 2: Log a note

User: `log note on AT&T: had a 30-min call with Sarah today, confirmed Q3 POC kickoff, 2 stakeholders on their side need to approve before Aug 15`

Agent:
```
About to log a HubSpot Note on AT&T - Suite & ScanMySMS (id 389301822705):
  body: "had a 30-min call with Sarah today, confirmed Q3 POC kickoff, 2 stakeholders on their side need to approve before Aug 15"
  timestamp: 2026-05-14 11:23 IDT

Reply "apply" to log it.
```

### Example 3: Kill

User: `kill Mekorot reason: 53 days untouched, no internal sponsor, blocked indefinitely`

Agent:
```
About to:
  1. Move Mekorot - Cyvore Suite (id 381006235888) to dealstage = Closed Lost (3889241322)
  2. Log a HubSpot Note with body: "Closed Lost — 53 days untouched, no internal sponsor, blocked indefinitely"

Reply "apply" to do both.
```

### Example 4: Account not in mapping

User: `update Bank Hapoalim: status got intro via Lior, next set up first call`

Agent: looks up `Bank Hapoalim` — not in mapping (but is in HubSpot Leads as id 1135192023230 from the bot run earlier). Replies:

```
"Bank Hapoalim" isn't in state/hubspot-mapping.json yet, but I found a matching HubSpot Lead: "Bank Hapoalim" (id 1135192023230, stage New).

Want me to:
  a) Add it to the mapping AND apply the update (both in one shot), or
  b) Just create the mapping and you'll re-run the update separately?
```
