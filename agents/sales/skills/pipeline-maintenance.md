# Pipeline Maintenance (owned by Sales)

## Purpose

Produce a weekly state-of-pipeline snapshot that reflects the live HubSpot reality, reconciled with the work done in `output/research/` and `output/outreach/`. Optimized for a startup with sparse pipeline and a single CRM admin: the value is reconciliation + hygiene + narrative, not forecasting.

This skill is owned by the Sales agent. Sales is the only agent with HubSpot write access and the only writer of `output/pipeline/{YYYY-WW}.md`. Other agents (especially Chief of Staff) read the snapshot file — they do not query HubSpot directly.

## Inputs

- HubSpot CRM (live, via the official Remote MCP server at `https://mcp.hubspot.com`)
- `output/research/**/*.md` — account research files
- `output/outreach/**/*.md` — outreach drafts and sequences
- `output/meeting-prep/**/*.md` — pre-meeting briefs
- `output/target-accounts.md` — prioritized target list (legacy source of truth before HubSpot)

## Dependencies

- HubSpot Remote MCP server connected in Cursor settings
- Skills 02 (Prospecting) and 04 (Account Research) have been used at least once so there's reconciliation surface

## Output

Write to `output/pipeline/{YYYY-WW}.md` (ISO week, e.g. `output/pipeline/2026-18.md`).

Never overwrite a prior week's file — each weekly run creates a new dated file so the history is auditable.

---

## Methodology

Run these steps in order. Synthesize as you go. At every step, ask "**so what?**" — don't list facts without commercial interpretation.

### Step 1: Pull HubSpot state

Use the HubSpot MCP server to fetch:

- All open deals (any stage that is not Closed Won / Closed Lost). For each: name, stage, amount, expected close date, owner, last modified timestamp, primary contact, associated company.
- All contacts associated with those deals: name, title, email, last engagement date.
- All companies associated with those deals: name, domain, industry, employee count.
- Activities in the last 14 days against those deals: calls, emails, meetings, notes, tasks.

If HubSpot is empty or sparse, that is a finding to surface in the report — do NOT invent deals.

**Canonical pipeline stages.** The HubSpot pipeline uses Yonatan's labels — the same labels he uses in the Cyvore GTM Weekly Sync Google Sheet (the live Monday meeting surface). Always use these strings verbatim when reporting; do not translate to HubSpot defaults like `appointmentscheduled` or `qualifiedtobuy`:

```
New → Attempting → Connected → In meetings/conversations → Finalizing the POC → Running POC → Closed Won → CS
```

(`CS` covers post-close customer success / live-customer state.) This taxonomy is shared with Chief of Staff's exec-comms skill — the weekly digest's stage breakdown lines up 1:1 with this snapshot.

### Step 2: Reconcile against `output/`

For each open HubSpot deal:

- Find the matching research file by company domain or slug (e.g., HubSpot deal "Deutsche Telekom" → `output/research/icp-d-telecom/deutsche-telekom.md`). The slug is the lowercase company name with spaces replaced by hyphens.
- Find the matching outreach file under `output/outreach/{icp}/{slug}.md`.
- Find any meeting prep under `output/meeting-prep/{slug}-{date}.md`.

Build the **Active Conversations** table:

| Account | ICP | Stage | Amount | Last touch | Days since | Research | Outreach | Next step | Risk |
|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | link or "missing" | link or "missing" | from HubSpot or research file | one line |

### Step 3: Reconciliation findings

Surface mismatches in three buckets:

**a) Research without HubSpot deal** — files in `output/research/` whose company has no open deal in HubSpot. List them. For each: is it work-in-progress that should become a deal? Was it disqualified? Hygiene action: either create the HubSpot deal or move the research to an archive.

**b) HubSpot deal without research** — open deals where there's no research file. List them. Hygiene action: run Skill 04 (Account Research) before the next touch.

**c) Stale deals** — open deals with no activity for 14+ days. List them with the last touch date. For each: is the deal real? Is the next step blocked? Hygiene action: log a current next step in HubSpot or close as Lost.

### Step 4: Pipeline math (honest, not optimistic)

Even with sparse data, compute and present:

- Total open pipeline (sum of deal amounts; flag deals missing amount)
- Stage breakdown (count + sum per stage)
- Weighted pipeline if HubSpot has stage probabilities; otherwise skip
- Number of deals missing each of: amount, expected close date, next step, primary contact

Do not project ARR or forecast unless the user has explicitly populated stage probabilities and close dates.

### Step 5: Movers (last 7 days)

From HubSpot activity history:

- Deals that changed stage in the last 7 days (forward or backward)
- Deals newly created
- Deals closed Won
- Deals closed Lost (and reason if logged)

For each, one-line "so what" — what does this mean for next week's actions?

### Step 6: Top 3 risks for the week ahead

Based on stale deals, missing next steps, blocked deals, or deals where the research flagged a known risk (e.g., legal compliance, vendor lock-in, champion turnover). Each risk gets:

- One-line description
- Concrete action you should take this week to defuse it

### Step 7: Hygiene actions checklist

A bullet list of concrete edits the user should make in HubSpot before next week's run. Examples:

- [ ] Add a `Next step` to deal "Acme Corp"
- [ ] Set an `Amount` on deal "Globex" (currently blank)
- [ ] Move deal "Initech" to Closed Lost (no activity 45 days)
- [ ] Create a HubSpot deal for "Hooli" (research file exists, no deal)

This section is the agent's main output for solo operators — every item is a 30-second fix that materially improves data quality for the next run.

---

## Output Schema

```
# Pipeline Review — Week {YYYY-WW}

**Date generated:** {date}
**HubSpot snapshot:** {N open deals, $X pipeline, last activity {date}}

## Active Conversations
| Account | ICP | Stage | Amount | Last touch | Days since | Research | Outreach | Next step | Risk |
|---|---|---|---|---|---|---|---|---|---|

**So what:** {1-2 sentences on the shape of pipeline this week}

## Reconciliation
### Research without HubSpot deal
- ...

### HubSpot deal without research
- ...

### Stale deals (no activity 14+ days)
- ...

## Pipeline Math
- Total open: $X across N deals
- Stage breakdown: ...
- Hygiene gaps: N deals missing amount, M missing close date, ...

## Movers (last 7 days)
- ...

## Top 3 Risks
1. **{Risk}** — {action}
2. ...
3. ...

## Hygiene Actions for You
- [ ] ...
- [ ] ...
```

---

## Quality Checklist

- [ ] Every deal in the Active Conversations table is real (came from HubSpot, not invented)
- [ ] Every "missing research" / "missing deal" entry has a concrete recommended action
- [ ] Stale deals (14+ days) are listed with the actual last activity date
- [ ] No forecast number is given unless HubSpot has the underlying data (probability + close date)
- [ ] Hygiene Actions checklist contains at least 3 concrete, 30-second-fix items
- [ ] Output filename uses ISO week (`{YYYY-WW}.md`) and does not overwrite prior weeks

## Relationship to Other Skills

```
agents/sales (this skill)                          →  produces weekly state-of-pipeline snapshot
agents/chief-of-staff/skills/exec-comms            →  consumes the snapshot to write digests / board update
agents/research-bizdev/skills/04-account-research  →  fills the "missing research" gap surfaced by this skill
agents/research-bizdev/skills/05-qualification     →  scores deals once research is in place
```
