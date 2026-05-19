# Weekly Digest — Week {YYYY-WW}

**Date:** {YYYY-MM-DD}
**Audience:** internal (founders, ops, leadership)
**Read time:** 1 minute

**Sources:**
- Weekly Customer Sync — tab `{DD.MM.YYYY}` of the [Cyvore GTM Weekly Sync Google Sheet]({SHEET_TAB_URL}) (live edit surface; replaces the deprecated xlsx as of 2026-W22)
- Pipeline snapshot — `output/pipeline/{YYYY-WW}.md`
- HubSpot sync log (this week's CRM writes) — `output/pipeline/{YYYY-WW}-sync-log.md`
- Weekly context — entry of `{YYYY-MM-DD}` in `state/weekly-context.md`

**Authoring rules** (apply to every section below):
- **Owner-tag every action.** Bullet must end with `(Owner: {name})` whenever it's a thing somebody has to do this week. No anonymous TODOs.
- **No redundancy.** If a record appears in TL;DR + Wins + Risks + Asks, decide which section it actually belongs in. Each material item lives in one place.
- **Numbers come from the sources, not the writer's gut.** If you don't have a count, say so — never invent.

---

## TL;DR

- {Headline #1 — typically the most material movement, win, or risk}
- {Headline #2}
- {Headline #3}

---

## Pipeline state

- **Total open:** {N} accounts ({Tier A: n} / {Tier B: m})
- **Stage breakdown:** New {n} → Attempting {n} → Connected {n} → In meetings/conversations {n} → Finalizing the POC {n} → Running POC {n} → Closed Won {n} → CS {n}
- **Net change vs. last week:** +{n_new}, +{n_advanced}, +{n_closed_won}, -{n_killed_or_regressed}
- **Done? scorecard:** {n}/{N} of last week's Next Steps were completed ({percent}%)

**So what:** {1-2 sentences on whether the pipeline is healthy or thin, where the energy is, and what the next move is}

---

## Top 3 wins

Pulled from rows where `Deal/Lead Stage` advanced vs. last week, `moving status` shows progression, or stage = `Closed Won`.

1. **{Account}** — {one-line what happened, who drove it}
2. **{Account}** — ...
3. **{Account}** — ...

---

## Top 3 risks / asks

Pulled from rows flagged `kill?`, stale rows (no `Status` change vs. last week), and last week's `Next Step` rows where `Done?` is empty.

1. **{Account / situation}** — {risk in one line} → {action this week to defuse} (Owner: {name})
2. ...
3. ...

---

## Current customers and live POCs

Pulled from HubSpot deals in `Closed Won`, `Running POC`, and `Finalizing the POC` (read via the most recent pipeline snapshot, falls back to last week's snapshot if today's hasn't been generated). One row per active commercial relationship — including expansion conversations, renewal moments, and POCs in flight. If we don't have any in a stage, write `(none)`.

| Account | Stage | This week's update | Next move (Owner) |
|---|---|---|---|
| {Account} | Closed Won / Running POC / Finalizing | {one-liner from `cyvore_weekly_status` or last note} | {next-step + (Owner: name)} |

**So what:** {1-2 sentences — is the post-sale book healthy? any churn / renewal flags? any POC stalled past the typical X-week window?}

---

## CRM cleanup this week — killed deals & leads

Pulled directly from `output/pipeline/{YYYY-WW}-sync-log.md` Phase 4 (kills). Counts must match the sync-log exactly — no manual recount.

- **Deals → Closed Lost ({n}):** {Account A}, {Account B}, ... ({reason theme: e.g. "no internal sponsor / no progression"})
- **Leads → Disqualified ({n}):** {Lead A}, {Lead B}, ... ({reason theme})

Full audit trail with HubSpot IDs and reason-note IDs in `output/pipeline/{YYYY-WW}-sync-log.md` (attached to the email send).

**So what:** {1-2 sentences — net pipeline cleanup picture. Are kills concentrated in one ICP / one origin? Anything we'd resurrect with a stronger angle?}

---

## Waiting on customer (not stalled — actively waiting)

Pulled from rows where `Next Step` semantically means "wait" (e.g. "wait for him to respond", "follow up next week", "they want to close one deal first"). These are NOT kills — they're explicit hold positions where we shouldn't push further this week.

| Account | What we're waiting for | Re-touch trigger / date (Owner) |
|---|---|---|
| {Account} | {what they need to do / say} | {trigger: e.g. "after their Q2 close" / explicit date} (Owner: {name}) |

**So what:** {1-2 sentences — is the waiting list bloated? any account that's been "waiting" 3+ weeks and probably needs a kill / new angle decision?}

---

## What changed (weekly context)

The 5 questions from `state/weekly-context.md` for the week of `{YYYY-MM-DD}`:

- **Win:** {answer}
- **Loss / stall:** {answer}
- **People:** {answer}
- **Product / pricing / positioning:** {answer}
- **Flag for leadership:** {answer}

---

## Asks for the team

Aggregated from the sync sheet's `Next Step` + `Assignee` columns. Each owner has a full task file linked below. Top-1-2 priorities here must each carry a 1-line "why this matters this week."

- **Yonatan ({n} items):** {top 1-2 priorities — 1-line each} → [full list](../weekly-tasks/{YYYY-WW}/yonatan.md)
- **Yoav ({n} items):** {top 1-2 priorities} → [full list](../weekly-tasks/{YYYY-WW}/yoav.md)
- **Ori ({n} items):** {top 1-2 priorities} → [full list](../weekly-tasks/{YYYY-WW}/ori.md)
- **Peter ({n} items):** {top 1-2 priorities} → [full list](../weekly-tasks/{YYYY-WW}/peter.md)
- **Ella ({n} items):** {top 1-2 priorities} → [full list](../weekly-tasks/{YYYY-WW}/ella.md)
- **Mike ({n} items):** {top 1-2 priorities} → [full list](../weekly-tasks/{YYYY-WW}/mike.md)

To send each owner their list: `python tools/send-email.py --to "{email}" --subject "Weekly tasks — Week {YYYY-WW}" --file "output/exec-comms/weekly-tasks/{YYYY-WW}/{owner}.md"`

---

## Send

Use the dedicated digest sender — auto-attaches the raw weekly customer sync xlsx and this week's HubSpot sync log, embeds the Cyvore logo header, and strips local `.md` links from the email body (since they don't resolve in mail clients) without modifying the source file:

```bash
python3 tools/send-digest.py --week {YYYY-WW}
```

Defaults: recipient = `default_recipient` from `tools/email-config.json`; subject = the digest's H1. Override with `--to`, `--cc`, `--subject`, `--attach`, `--no-xlsx`, `--no-logo`. Always `--dry-run` first if you've changed the structure.

---

*Generated by Chief of Staff (exec-comms). Sources: Cyvore GTM Weekly Sync Sheet (tab `{DD.MM.YYYY}`), `output/pipeline/{YYYY-WW}.md`, `output/pipeline/{YYYY-WW}-sync-log.md`, `state/weekly-context.md`.*
