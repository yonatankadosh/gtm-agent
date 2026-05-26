# Exec Comms (owned by Chief of Staff)

## Purpose

Generate audience-specific executive communications by composing the live state of the business from upstream agents. Replaces the manual work of pulling pipeline numbers, recent wins, and qualitative context into a clean weekly digest, monthly investor letter, quarterly board update, or all-hands script.

This skill is owned by the Chief of Staff agent. CoS is a pure composer: it reads upstream artifacts but never queries HubSpot directly and never writes to HubSpot.

## Inputs

- **Cyvore GTM Weekly Sync Google Sheet** — Yonatan's live weekly customer sync workbook. **Required for `audience=weekly`.** One tab per week, named `DD.MM.YYYY`. Each tab carries 8 columns: `Tier | Company/Lead Name | Deal/Lead Stage | Status | Next Step | Assignee | Done? | moving status`. Read via `python3 tools/sheets/read-weekly-sync.py [--week YYYY-WW] [--prior]` (the tool reads the Sheet via service-account auth — no file uploads). Replaces the deprecated `state/weekly-customer-sync.xlsx`, which was archived during the 2026-W22 migration.
- `output/pipeline/{YYYY-WW}/snapshot.md` — latest weekly pipeline snapshot (written by the Sales agent's pipeline-maintenance skill)
- `output/pipeline/{YYYY-WW}/sync-log.md` — this week's HubSpot sync audit log (written by Sales' hubspot-status-sync skill the same morning). Contains every CRM write applied today: updates, kills, creates, notes — with HubSpot IDs. **This is the canonical source for the digest's "CRM cleanup this week — killed deals & leads" section.** If absent, the digest's killed-records section must say `(no sync log available — counts deferred to next week)` rather than guess.
- `state/weekly-context.md` — qualitative state (written by the weekly-context interview skill, also under CoS)
- `output/outreach-learnings.md` — signal-to-outcome calibration log (if present)
- `output/research/{icp}/{slug}.md` and `output/meeting-prep/{slug}-{date}.md` — for specific account references (read on demand by exact path; never glob)
- `state/okrs.md` — current quarter objectives (if maintained)

CoS does NOT call HubSpot. If a number is needed and the latest pipeline snapshot does not contain it, surface a `[needs verification]` placeholder and ask the user — or route to Sales (via the orchestrator) to refresh the snapshot first.

## Dependencies

- For `audience=weekly`: the Cyvore GTM Weekly Sync Sheet contains a tab whose date falls in the current ISO week. The Mon 06:00 cron (`tools/sheets/generate-weekly-tab.py`) creates this tab automatically. If it's missing (cron failed, off-cycle digest), the orchestrator should run `python3 tools/sheets/generate-weekly-tab.py` before this skill, or the user can edit the Sheet directly.
- A current-week pipeline snapshot exists at `output/pipeline/{YYYY-WW}/snapshot.md` (the orchestrator runs Sales' pipeline-maintenance first if missing)
- A recent `state/weekly-context.md` entry exists (the orchestrator runs the weekly-context interview first if stale or missing)
- `tools/sheets/google-sheets-config.json` and `tools/sheets/google-sheets-credentials.json` are populated (one-time setup; see `tools/sheets/google-sheets-config.template.json`)

## Output

Write to:
- `output/exec-comms/weekly/{YYYY-WW}.md`
- `output/exec-comms/board/{YYYY-Q[1-4]}.md`
- `output/exec-comms/investor/{YYYY-MM}.md`
- `output/exec-comms/all-hands/{YYYY-MM-DD}.md`

Never overwrite prior outputs.

---

## Methodology

### Step 1: Confirm audience and template

Ask the user (or infer from the request) which template to use:

- `weekly` — internal weekly digest
- `board` — quarterly board update
- `investor` — monthly investor letter
- `all-hands` — team-facing update

Load the matching template from `agents/chief-of-staff/templates/{audience}.md`.

### Step 2: Check freshness of inputs

Before composing, verify:

- For `audience=weekly`: the Cyvore GTM Weekly Sync Sheet has a tab whose date falls in the current ISO week. Run `python3 tools/sheets/read-weekly-sync.py --list` to inspect available tabs. If no tab matches, run `python3 tools/sheets/generate-weekly-tab.py` to create it from current HubSpot state, or ask the user to add the tab manually — never invent a tab.
- A current-week pipeline snapshot exists at `output/pipeline/{YYYY-WW}/snapshot.md`. If not, return to the orchestrator and ask it to run Sales' pipeline-maintenance first.
- A weekly context entry exists for this week. If not, return to the orchestrator and ask it to run the weekly-context interview first.
- A current-week sync log exists at `output/pipeline/{YYYY-WW}/sync-log.md` (only present if Sales' hubspot-status-sync ran this week). Used for the "CRM cleanup this week" section.

**Synthesize-from-meeting fast path.** If the user is running `weekly-customer-sync` (Sales) and `weekly digest` (CoS) back-to-back in the same chat — i.e. the meeting just happened — both `state/weekly-context.md` and the kill list are already in flight. Don't bounce back to the orchestrator demanding a separate weekly-context interview run. Instead:
1. Synthesize this week's `state/weekly-context.md` entry directly from the conversation (wins / losses / people / product / leadership flags surfaced during the meeting), prepend it to the file, and surface the new entry to the user for confirmation.
2. Pull the kills from the sync log written minutes ago.
3. Compose the digest.

This collapses three orchestrator hops into one and was the working pattern in the 2026-W21 run. Use it whenever both skills are run in the same chat. When the user runs the digest cold (no sync meeting today), fall back to the strict orchestrator-driven sequencing.

If any input is stale (>7 days old) and not being synthesized in this chat, surface it to the user and ask whether to proceed with stale data or refresh first.

### Step 3: Pull numbers from the snapshot, not HubSpot

The board and investor templates may need:
- ARR (closed-won deals annualized) — read from the latest pipeline snapshot's "Pipeline Math" section. If absent, mark `[needs verification]` and ask the user, or route back to Sales for a refreshed snapshot that includes it.
- Pipeline coverage vs. target — read from snapshot + user-stated target
- Closed-won deals this quarter / month — read from snapshot's "Movers" history (across multiple weeks if needed)
- Hiring counts — read from `state/weekly-context.md` history

CoS does NOT call HubSpot. Only Sales' pipeline-maintenance skill queries HubSpot directly.

### Step 3.5: Reconcile sync sheet vs. prior tab (audience=weekly only)

Run the reader with `--prior` to get both this week's and last week's tabs in one JSON:

```
python3 tools/sheets/read-weekly-sync.py --prior
```

From the combined output, derive:

- **Stage breakdown for this week.** Use the sync sheet's stage labels verbatim — they are the canonical taxonomy: `New → Attempting → Connected → In meetings/conversations → Finalizing the POC → Running POC → Closed Won → CS`.
- **Tier A vs. Tier B counts** from the `Tier` column.
- **Done? scorecard.** The reader returns `done_scorecard: { completed, total, percent }` — total = prior week's rows that had a `Next Step`; completed = those whose `Done?` cell was `V` (or any truthy value). This is the headline accountability number for the digest.
- **Movers this week** by joining `Company/Lead Name` between the two tabs:
  - Stage advanced (e.g. Attempting → Connected, Running POC → Closed Won)
  - Stage regressed or row marked `kill?` in `Next Step`
  - Newly added rows (in this week, not in prior)
  - Rows whose `moving status` is non-empty — Yonatan uses this column for progression notes (`yoav spoke with kfir`, `waiting for her to respond`, etc.). Treat these as candidate "wins" for the digest.
- **Stale rows** — rows where `Status` and `Next Step` are unchanged vs. prior tab. These are candidates for the Top 3 risks section.

Cross-check against the HubSpot pipeline snapshot at `output/pipeline/{YYYY-WW}/snapshot.md`. Any account in the sync sheet that doesn't appear in the snapshot, or vice versa, is a reconciliation gap — note it but don't block the digest.

### Step 4: Compose the output

Fill the template, following these rules:

- **Pull facts, never invent.** Every number must come from HubSpot, `output/`, or `state/`. If a section needs a number we don't have, mark it `[needs verification]` and surface it in a "Gaps" section.
- **Apply the "So what" rule.** Every section ends with one sentence on what it means or what action it implies.
- **Owner-tag every action.** For weekly digest in particular, every actionable bullet (in Risks, Asks, Current customers, Waiting list) ends with `(Owner: {name})`. No anonymous TODOs. This was a hard learning from 2026-W21 — rework cycles cost the user 4-5 messages otherwise.
- **No redundancy across sections.** If "AT&T scheduling" lands in TL;DR, Top 3 risks, AND Asks for the team, decide which section it actually belongs in. Each material item lives in one place. The risk section's right column is "action this week" — that line implicitly handles the ask, no need to repeat it 30 lines later.
- **Sections that always belong in the weekly digest** (per the template): TL;DR, Pipeline state, Top 3 wins, Top 3 risks/asks, **Current customers and live POCs**, **CRM cleanup this week — killed deals & leads**, **Waiting on customer**, What changed (weekly context), Asks for the team. The three bolded ones were missing from the original template and were added in 2026-W21 after user feedback.
- **Keep the audience in mind.**
  - Weekly digest → action-oriented, internal voice. Sections kept short.
  - Board update → structured, KPI-led, asks at the end
  - Investor letter → narrative, traction + headwinds + asks
  - All-hands → motivational + transparent, shoutouts included
- **Preserve voice.** If the user has prior artifacts in the same folder, scan one for tone reference.

### Step 5: Present and confirm

Show the user the full draft in chat before writing the file. Offer two options: (a) save as-is, (b) edit specific sections. Only write on confirmation.

### Step 6: Write the file

Output to the right folder per audience. Filename uses the date convention above.

### Step 6.5: Generate per-assignee task lists (audience=weekly only)

After the digest is confirmed and written, run:

```
python3 tools/sheets/read-weekly-sync.py --by-assignee
```

This writes one markdown file per unique `Assignee` to `output/exec-comms/weekly-tasks/{YYYY-WW}/{owner-slug}.md`. Each file contains:

- That owner's rows from this week's tab (Tier, Account, Stage, Next Step, Status)
- Carry-over rows from last week's tab where `Done?` was empty and a `Next Step` was set (the owner's unfinished commitments)
- A pre-formatted `tools/email/send-email.py` snippet at the bottom

Multi-owner cells like `Yoav, Ori` are split — each owner's file gets the row.

After generation, surface the list of owner files to the user and ask whether to email them. Do NOT auto-send — the user confirms each send.

### Step 7: Send the digest (audience=weekly)

Use the dedicated digest sender — not the generic `tools/email/send-email.py`:

```bash
python3 tools/email/send-digest.py --week {YYYY-WW}
```

What it handles automatically:
- Recipient: `default_recipient` from `tools/email/email-config.json` (override with `--to`).
- Subject: the digest's H1 (override with `--subject`).
- Auto-attaches: the digest `.md`, a CSV export of the current week's tab from the Cyvore GTM Weekly Sync Sheet (was xlsx pre-2026-W22), and `output/pipeline/{YYYY-WW}/sync-log.md` if it exists.
- Renders a "Live sync sheet" banner at the top of the email body with a clickable link straight to that week's Sheet tab — so recipients can open the source data on phone or laptop without needing the attachment.
- Embeds `tools/assets/cyvore-logo-mark.png` inline at the top (path unchanged after the tools/ restructure).
- Strips `[label](relative-path.md)` hyperlinks from the email body — they don't resolve in mail clients — but keeps `http(s)://` and `mailto:` links and **does not modify the source file on disk**.

Common modifiers: `--cc`, `--attach FILE` (repeatable), `--no-csv` (alias `--no-xlsx` retained for muscle memory), `--no-sheet-link`, `--no-logo`, `--dry-run`.

Always run with `--dry-run` first if the digest structure changed materially this week — it prints the recipient, subject, full attachment list, whether the Sheet-link banner resolved a tab, and the count of stripped local-md links so the user can sanity-check before the real send.

Degraded mode: if `tools/sheets/google-sheets-config.json` is not configured, the email still sends — just without the CSV attachment and without the Sheet-link banner. The digest content itself never depends on the Sheet being available at send time.

Why a dedicated tool: `tools/email/send-email.py` only supports a single attachment and no inline image. The weekly digest reliably needs the markdown + the raw weekly-sync data + the sync log + the logo + a live link to the Sheet. This was rebuilt three times in `/tmp/` on 2026-W21 before being promoted here. Use this tool — don't rebuild in `/tmp/`.

---

## Templates

Stored in `agents/chief-of-staff/templates/`:

- `weekly-digest.md`
- `board-update.md`
- `investor-letter.md`
- `all-hands.md`

Each template is a generic best-practice frame. Iterate them after the first 1-2 real runs.

---

## Quality Checklist

- [ ] Every number traces to HubSpot, `output/`, or `state/` — no invented metrics
- [ ] Every section ends with a "so what" line tied to a decision
- [ ] Tone matches the audience (internal vs. board vs. investor vs. team)
- [ ] User saw and confirmed the draft before the file was written
- [ ] Output filename matches the convention and does not overwrite prior artifacts
- [ ] If any input was stale, that's surfaced to the user (not silently used)
- [ ] **Audience=weekly only:** stage labels in the digest match the sync sheet verbatim (no HubSpot defaults bleeding through)
- [ ] **Audience=weekly only:** Done? scorecard is computed from the prior tab, not estimated
- [ ] **Audience=weekly only:** per-assignee task files were generated and the list of paths was surfaced to the user
- [ ] **Audience=weekly only:** every actionable bullet ends with `(Owner: {name})` — no anonymous TODOs
- [ ] **Audience=weekly only:** the three template-mandatory sections are present — Current customers and live POCs, CRM cleanup this week — killed deals & leads, Waiting on customer
- [ ] **Audience=weekly only:** killed-records counts match `output/pipeline/{YYYY-WW}/sync-log.md` exactly (no estimates)
- [ ] **Audience=weekly only:** sent via `tools/email/send-digest.py` (not `send-email.py`, not an ad-hoc `/tmp/` script) so the xlsx + sync-log + logo + link-stripping are all consistent

## Relationship to Other Skills

```
agents/chief-of-staff/skills/exec-comms (this skill)        →  audience-specific composition
agents/sales/skills/pipeline-maintenance                    →  upstream input (pipeline snapshot)
agents/chief-of-staff/skills/weekly-context                 →  upstream input (qualitative state)
agents/orchestrator                                         →  sequences pipeline-maintenance + weekly-context + exec-comms in the "run weekly" flow
```
