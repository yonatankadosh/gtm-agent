# Co-sell Plan Skill (owned by Partnerships)

## Purpose

Build a joint motion with a named partner against named target accounts. The output is a specific, executable plan: which accounts, who at the partner brings the relationship, the joint message, who runs the first meeting, and the success metric. Distinct from partner mapping — that's the universe; this is one motion against one partner.

## Inputs

- `context/product-overview.md`
- `output/icp.md`
- `output/target-accounts.md`
- `output/partnerships/landscape.md` (must have run the partner-mapping skill first; partner must be Tier 1 or Tier 2)
- `output/research/{icp-folder}/{slug}.md` for any target account that gets named in the plan (read by exact path)
- The partner name (provided by the user via the Orchestrator)

## Output

Write to `output/partnerships/{partner-slug}.md`.

---

## Methodology

### Step 1: Confirm partner readiness

Open `output/partnerships/landscape.md`. Confirm:

- Partner is Tier 1 or Tier 2 in the landscape
- A partner-side contact is named (or explicit "needs verification")
- ICP overlap is 2 or 3

If the partner isn't in the landscape file, return to the Orchestrator with: "I need partner mapping context for {partner}. Should I run partner-mapping first?"

### Step 2: Identify joint targets

Cross-reference `output/target-accounts.md` against the partner's known customers (from the partner's website, case studies, or the user's knowledge). For each candidate joint target, ask:

- Is this account in our `target-accounts.md` Tier 1 or Tier 2?
- Is there a known relationship (the partner is a vendor / partner / integrator at this account)?
- Would the partner have a credible reason to introduce us?

Pick **3-7 named accounts**. More than 7 dilutes focus; fewer than 3 isn't a motion.

For each chosen account, read `output/research/{icp}/{slug}.md` by exact path. If a research file is missing, surface to the Orchestrator and ask whether to dispatch Research & BizDev first.

### Step 3: Build the joint message

The single sentence both we and the partner can say to a target customer. Three components:

- **What we jointly deliver** that neither does alone
- **The pain it solves** for this customer profile specifically
- **The proof** — joint customer, joint demo, joint case study (or "to be built" if it's a new motion)

Write the message in plain language. Test it: would a CISO at one of the joint targets read it and want to take a meeting?

### Step 4: Map the meeting flow

Per joint account:

1. **Who at the partner brings it** — named person, their role, their relationship to the target
2. **Who at us joins** — named person on our side
3. **First meeting type** — joint discovery, joint demo, executive sync
4. **Pre-meeting prep** — what artifact each side brings (often a joint one-pager or short joint POC scope)
5. **Success criterion** — what counts as a successful first meeting (next meeting booked, joint POC scoped, intro to economic buyer)

### Step 5: Operational mechanics

Once per partner, lock the operational rhythm:

- Cadence — weekly partner sync, monthly joint pipeline review, quarterly executive sync?
- Joint pipeline tracking — where does it live? (we recommend `output/partnerships/joint-pipeline.md`, refreshed by us; partner may have their own CRM)
- Attribution rule — when a deal closes, who gets credit? (Often: partner-sourced gets full referral fee; us-sourced with partner-influenced gets a smaller fee. Lock this up front.)
- Escalation path — when something goes wrong (partner stops responding, lead goes cold), who calls whom?

### Step 6: HubSpot updates (route to Sales)

You don't write to HubSpot. List recommendations at the end of the file under "HubSpot updates recommended (route to Sales)" — typically: tag joint deals with the partner name, create deal records for partner-sourced leads, log joint-meeting notes.

---

## Output Schema

```
# Co-sell Plan: {Partner Name}

**Date:** {YYYY-MM-DD}
**Partner slug:** {partner-slug}
**Partner-side owner:** {name + role}
**Our owner:** {name + role}
**Partner tier (from landscape):** {Tier 1 / 2}

## Joint message
{Single sentence — what we deliver together, the pain it solves, the proof}

## Joint targets

| Account | ICP | Why this partner unlocks it | Their contact at the account | Our recommended first meeting |
|---|---|---|---|---|
| {company} | {icp} | ... | ... | ... |
| ... | ... | ... | ... | ... |

## Per-account meeting plan

### {Account 1}
- **Partner brings:** {named person, role, relationship}
- **We join:** {named person}
- **First meeting:** {type} — by {date}
- **Pre-meeting artifact:** {joint one-pager / POC scope / case study}
- **Success criterion:** {what makes the first meeting a win}

### {Account 2}
...

## Operational mechanics
- **Cadence:** {weekly partner sync / monthly pipeline review / etc.}
- **Joint pipeline tracking:** {where it lives}
- **Attribution rule:** {who gets credit when a deal closes}
- **Escalation path:** {who calls whom when something stalls}

## Success metric for the motion
{One specific number with a date — e.g., "2 joint POCs scoped by Q3, $X joint pipeline by Q4"}

## HubSpot updates recommended (route to Sales)
- [ ] Tag joint deals with `partner: {partner-slug}`
- [ ] Create deal record for {partner-sourced lead, if any}
- [ ] Log joint-meeting note on {account}

## Research gaps
- [ ] ...
```

---

## Quality Checklist

- [ ] Partner is Tier 1 or Tier 2 in `output/partnerships/landscape.md`
- [ ] 3-7 joint target accounts named, every one in our `target-accounts.md`
- [ ] Joint message is one sentence, testable on a real CISO
- [ ] Each joint account has a partner-side contact (or explicit "needs verification") and a defined first meeting
- [ ] Operational mechanics locked: cadence, tracking, attribution, escalation
- [ ] Success metric is specific (number + date)
- [ ] No fabricated partner contacts, joint deals, or imaginary integrations
- [ ] HubSpot writes are listed as recommendations for Sales, not performed by Partnerships
