# Health Check Skill (owned by Customer Success)

## Purpose

Score one customer's health across four axes (Usage, Sentiment, Stakeholder, Contract) and produce a Green/Yellow/Red verdict with a concrete next action. Used proactively at a regular cadence (monthly), and reactively when there's a signal (ticket spike, executive change, missed QBR).

## Inputs

- `context/product-overview.md`
- `context/customers.md` (confirms the customer is in scope)
- `output/icp.md`
- `output/research/{icp-folder}/{slug}.md` — for history continuity (original pain, champion, competitive context). Read by exact path.
- HubSpot via MCP (read-only) — last 90 days of activity, ticket history, contact list, deal/contract dates
- Prior `output/cs/{customer-slug}/health.md` — for trend (is the score moving?)

## Output

Write to `output/cs/{customer-slug}/health.md` (overwrites prior, keeping a "Score history" section at the top with date-stamped prior verdicts).

---

## Methodology

### Step 1: Pull the data (read-only)

From HubSpot via MCP:

- Last activity date on the account (any engagement: call, email, meeting, note)
- Ticket count and severity in the last 90 days
- Contact list — how many active contacts, any departures, any new joiners (especially in security / IT / leadership)
- Contract: start date, end date, ARR, last renewal date

From the original research file (`output/research/{icp}/{slug}.md`):

- Original pain
- Original champion
- Original economic buyer
- Original competitive context

If the research file doesn't exist for this customer, surface to the Orchestrator and ask whether to dispatch Research & BizDev to create one (post-sale research is still valuable for renewal/expansion).

### Step 2: Score the four axes

Each axis: **Green / Yellow / Red** with a one-sentence justification anchored to the data.

#### Usage
- Green: active product engagement in the last 14 days, no critical drops
- Yellow: low engagement (no activity 14-30 days) OR usage trending down
- Red: no engagement 30+ days OR usage cliff

#### Sentiment
- Green: recent positive signal (NPS reply, public reference, "this is working" in a meeting note)
- Yellow: neutral or no recent signal
- Red: ticket spike, complaint, escalation, or competitor mentioned

#### Stakeholder
- Green: champion is in seat, engaged, and economic buyer is reachable
- Yellow: champion is quiet OR has changed roles OR economic buyer has changed
- Red: champion left the company OR the team that bought us was reorged

#### Contract
- Green: renewal > 6 months out OR recently renewed
- Yellow: renewal 3-6 months out
- Red: renewal < 3 months out and no renewal conversation started

### Step 3: Verdict

Aggregate to a single Green/Yellow/Red:

- All four Green → Green
- One Yellow → Yellow
- Two Yellows OR any Red → Red
- Use judgment — Red on Stakeholder almost always overrides everything else

### Step 4: Recommended next action

Tie verdict to a specific, named, time-bound action:

- **Green** → Schedule the next standard touchpoint (QBR, check-in). Optionally trigger expansion-plan skill if usage is strong.
- **Yellow** → Specific intervention named (re-engage champion, schedule executive sync, run a usage workshop). Owner + date.
- **Red** → Save play required (see churn-risk skill). Recommend escalation. Owner + date.

### Step 5: HubSpot write recommendations (for Sales)

You are read-only on HubSpot. If the health check surfaces actions that should be logged in HubSpot (CSM call notes, deal-stage updates for upcoming renewal, contact field updates), do NOT call MCP writes. Instead, list them at the end of the file under "HubSpot updates recommended (route to Sales)" so the Orchestrator can dispatch Sales with explicit user confirmation.

---

## Output Schema

```
# Health Check: {Customer Name}

**Date:** {YYYY-MM-DD}
**Customer slug:** {slug}
**Verdict:** {Green | Yellow | Red}
**Score history:** {Green 2026-03-30 → Yellow 2026-04-30 (this run)}

## Score by axis

| Axis | Status | Justification |
|---|---|---|
| Usage | G/Y/R | ... |
| Sentiment | G/Y/R | ... |
| Stakeholder | G/Y/R | ... |
| Contract | G/Y/R | ... |

## Signals (raw data this run was based on)

- Last HubSpot activity: {date, type}
- Tickets last 90d: {count, severity breakdown}
- Active contacts: {N, with role mix}
- Contract: {ARR, end date, days to renewal}
- Original champion: {name, current status}

## Trend

{1-2 sentences on direction vs. last check}

## So what

{1-2 sentences interpreting the verdict — what does this mean we need to do}

## Recommended next action

**{Specific action}** — owner: {name}, by: {date}, success looks like: {outcome}

## HubSpot updates recommended (route to Sales)

- [ ] {action — e.g., "log a CSM call note", "update last-touch field"}
- [ ] ...

## Research Gaps

- [ ] ...
```

---

## Quality Checklist

- [ ] All four axes scored with one-sentence justifications anchored to actual data
- [ ] Verdict is one of {Green, Yellow, Red} — no in-between
- [ ] Score history shows the trend across runs
- [ ] Recommended action is specific (named owner + date + success criterion)
- [ ] No fabricated usage numbers, ticket counts, or sentiment quotes
- [ ] HubSpot writes are listed as recommendations for Sales, not performed by CS
- [ ] Original research file was consulted for history continuity (or its absence flagged)
