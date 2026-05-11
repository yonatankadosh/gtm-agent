# Exec Comms (owned by Chief of Staff)

## Purpose

Generate audience-specific executive communications by composing the live state of the business from upstream agents. Replaces the manual work of pulling pipeline numbers, recent wins, and qualitative context into a clean weekly digest, monthly investor letter, quarterly board update, or all-hands script.

This skill is owned by the Chief of Staff agent. CoS is a pure composer: it reads upstream artifacts but never queries HubSpot directly and never writes to HubSpot.

## Inputs

- `output/pipeline/{YYYY-WW}.md` — latest weekly pipeline snapshot (written by the Sales agent's pipeline-maintenance skill)
- `state/weekly-context.md` — qualitative state (written by the weekly-context interview skill, also under CoS)
- `output/outreach-learnings.md` — signal-to-outcome calibration log (if present)
- `output/research/{icp}/{slug}.md` and `output/meeting-prep/{slug}-{date}.md` — for specific account references (read on demand by exact path; never glob)
- `state/okrs.md` — current quarter objectives (if maintained)

CoS does NOT call HubSpot. If a number is needed and the latest pipeline snapshot does not contain it, surface a `[needs verification]` placeholder and ask the user — or route to Sales (via the orchestrator) to refresh the snapshot first.

## Dependencies

- A current-week pipeline snapshot exists at `output/pipeline/{YYYY-WW}.md` (the orchestrator runs Sales' pipeline-maintenance first if missing)
- A recent `state/weekly-context.md` entry exists (the orchestrator runs the weekly-context interview first if stale or missing)

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

- A current-week pipeline snapshot exists at `output/pipeline/{YYYY-WW}.md`. If not, return to the orchestrator and ask it to run Sales' pipeline-maintenance first.
- A weekly context entry exists for this week. If not, return to the orchestrator and ask it to run the weekly-context interview first.

If either is stale (>7 days old), surface it to the user and ask whether to proceed with stale data or refresh first.

### Step 3: Pull numbers from the snapshot, not HubSpot

The board and investor templates may need:
- ARR (closed-won deals annualized) — read from the latest pipeline snapshot's "Pipeline Math" section. If absent, mark `[needs verification]` and ask the user, or route back to Sales for a refreshed snapshot that includes it.
- Pipeline coverage vs. target — read from snapshot + user-stated target
- Closed-won deals this quarter / month — read from snapshot's "Movers" history (across multiple weeks if needed)
- Hiring counts — read from `state/weekly-context.md` history

CoS does NOT call HubSpot. Only Sales' pipeline-maintenance skill queries HubSpot directly.

### Step 4: Compose the output

Fill the template, following these rules:

- **Pull facts, never invent.** Every number must come from HubSpot, `output/`, or `state/`. If a section needs a number we don't have, mark it `[needs verification]` and surface it in a "Gaps" section.
- **Apply the "So what" rule.** Every section ends with one sentence on what it means or what action it implies.
- **Keep the audience in mind.**
  - Weekly digest → 15 lines, action-oriented, internal voice
  - Board update → structured, KPI-led, asks at the end
  - Investor letter → narrative, traction + headwinds + asks
  - All-hands → motivational + transparent, shoutouts included
- **Preserve voice.** If the user has prior artifacts in the same folder, scan one for tone reference.

### Step 5: Present and confirm

Show the user the full draft in chat before writing the file. Offer two options: (a) save as-is, (b) edit specific sections. Only write on confirmation.

### Step 6: Write the file

Output to the right folder per audience. Filename uses the date convention above.

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

## Relationship to Other Skills

```
agents/chief-of-staff/skills/exec-comms (this skill)        →  audience-specific composition
agents/sales/skills/pipeline-maintenance                    →  upstream input (pipeline snapshot)
agents/chief-of-staff/skills/weekly-context                 →  upstream input (qualitative state)
agents/orchestrator                                         →  sequences pipeline-maintenance + weekly-context + exec-comms in the "run weekly" flow
```
