# Expansion Plan Skill (owned by Customer Success)

## Purpose

Identify a specific, time-bound expansion opportunity inside an existing customer — additional seats, new modules, new business unit, multi-year commit, or reference partnership — and lay out the play to land it. Distinct from a renewal; expansion is net-new revenue, not retention.

## Inputs

- `context/product-overview.md` (especially pricing tiers, modules, packaging)
- `output/research/{icp-folder}/{slug}.md` — original deal context (read by exact path)
- `output/cs/{customer-slug}/health.md` — current health score (must be Green or Yellow with a clear path back; do not pursue expansion when Red)
- HubSpot via MCP (read-only) — current contract, deals, contacts
- Prior `output/cs/{customer-slug}/expansion.md` — if a prior plan exists, was it executed? What worked / didn't?

## Output

Write to `output/cs/{customer-slug}/expansion.md` (overwrites prior; keep a "Plan history" section).

---

## Methodology

### Step 1: Confirm health

Open `output/cs/{customer-slug}/health.md`. If the verdict is **Red**, stop. Return to the Orchestrator with: "Customer health is Red. Run churn-risk before expansion." Expansion plays into a Red account waste credibility.

If health is **Yellow**, proceed but note the Yellow risk in the plan and add a precondition step (e.g., "fix the [yellow signal] before pitching expansion").

### Step 2: Identify the opportunity

Three flavors of expansion:

- **Seats / volume** — same product, more users, more API calls, more data. Easiest to land if usage is healthy.
- **Modules / cross-sell** — different product line. Requires fresh stakeholder mapping (the seats buyer often isn't the modules buyer).
- **Term / commit** — multi-year, prepaid annual, larger commit in exchange for discount. Lowest friction, requires aligning with renewal date.

Pick the one with the strongest signal. Justify in one sentence.

### Step 3: Stakeholder mapping (refresh, don't assume)

The original buying committee may have changed. Re-map:

- **Champion (current):** who is using the product today and has the political capital to push for more? (Often, but not always, the original champion.)
- **Economic buyer (current):** whose budget pays for the expansion? May differ from the original deal if the expansion crosses a department line.
- **Coach (potential):** who else inside has used the product and would advocate?
- **Blocker (potential):** is there anyone who would slow this down — procurement, security, a peer team that prefers a different vendor?

If the original champion has left the company, that's a flag — surface it before continuing.

### Step 4: Build the play

A play is a specific, ordered sequence of moves with named owners and dates:

1. **Trigger event** — what creates the window (renewal date approaching, new use case emerging, an executive change that helps us, a competitor stumble)
2. **Discovery move** — the meeting / artifact that confirms the opportunity is real (e.g., usage workshop, executive sync, ROI conversation)
3. **Proposal move** — the specific deliverable to land the expansion (revised quote, business case, pilot plan, joint roadmap conversation)
4. **Close move** — the conversation / artifact that closes (final pricing, commercial terms, execution plan)
5. **Risk hedge** — the one thing most likely to break this, and the action to prevent it

### Step 5: HubSpot write recommendations (for Sales)

You are read-only on HubSpot. If the play involves logging activities, creating an expansion deal record, or updating contact fields, do NOT call MCP writes. List them at the end under "HubSpot updates recommended (route to Sales)" — Orchestrator dispatches Sales with user confirmation.

---

## Output Schema

```
# Expansion Plan: {Customer Name}

**Date:** {YYYY-MM-DD}
**Customer slug:** {slug}
**Health at time of plan:** {Green / Yellow with caveat}
**Plan history:** {brief notes on prior plans and outcomes}

## Opportunity

**Type:** {seats / modules / term}
**Size estimate:** ${X} ARR uplift (or {N} seats / {modules})
**Why now:** {1-2 sentences on the trigger}

## Stakeholder map (current)

| Role | Name | Title | Engagement | Notes |
|---|---|---|---|---|
| Champion | ... | ... | ... | ... |
| Economic buyer | ... | ... | ... | ... |
| Coach | ... | ... | ... | ... |
| Potential blocker | ... | ... | ... | ... |

**Change vs. original deal:** {what's different about who's involved}

## The play

1. **Trigger:** {event that opens the window, with date}
2. **Discovery move:** {meeting / artifact} — owner: {name}, by: {date}
3. **Proposal move:** {deliverable} — owner: {name}, by: {date}
4. **Close move:** {final step} — owner: {name}, by: {date}
5. **Risk hedge:** {biggest risk + action to prevent it}

## Success criteria

- {Specific outcome — "$X ARR booked by date Y" / "expansion deal at stage Z by date W"}

## HubSpot updates recommended (route to Sales)

- [ ] {e.g., "create expansion deal record on the Acme account"}
- [ ] {e.g., "log discovery-move call note"}

## Research Gaps

- [ ] ...
```

---

## Quality Checklist

- [ ] Health was confirmed Green or Yellow with caveat before this plan was produced
- [ ] Opportunity type is one of {seats, modules, term} — not a vague "more business"
- [ ] Stakeholder map is current (refresh from HubSpot, not copied from original deal)
- [ ] Each step in the play has a named owner and a date
- [ ] Risk hedge identifies the single most likely failure mode
- [ ] Success criterion is a specific number or stage with a date
- [ ] HubSpot writes are listed as recommendations for Sales, not performed by CS
