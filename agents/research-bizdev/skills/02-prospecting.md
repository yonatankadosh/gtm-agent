# Skill 02: Prospecting

## Purpose

Find, qualify, and prioritize net-new accounts that match the ICP. Prospecting is not list-building — it is the disciplined process of identifying companies that have the right characteristics, in the right moment, to become customers. The output is a prioritized, qualified prospect list with enough context on each account to know why it belongs there and what the first move is.

## Inputs

- `context/product-overview.md` (required)
- `output/icp.md` (required — run Skill 01 first)
- `context/customers.md` (helpful — for lookalike expansion)

## Dependencies

- Skill 01: ICP Definition must be complete

## Output

Write to `output/target-accounts.md`

---

## Methodology

### Step 1: Sharpen the Targeting Criteria

Before searching, translate the ICP into a precise, filterable profile. Broad targeting wastes time. The best prospecting lists are small and accurate, not large and approximate.

**Firmographic criteria (who they are):**
- Industry / sub-vertical
- Headcount range
- Revenue range (if known)
- Geography
- Ownership type (VC-backed, PE-backed, public, bootstrap)
- Business model

**Technographic criteria (what they use):**
- Platforms and tools that indicate fit (e.g., "uses Slack + Zoom + Jira")
- Tools that indicate they have the problem you solve
- Tools that indicate they're solving it with a competitor (decide: displacing or disqualifying?)

**Situational criteria (where they are):**
- Funding stage and recency
- Growth rate signals (headcount change over 6-12 months)
- Hiring patterns (what roles are they hiring for?)
- Recent events (launches, expansions, leadership changes)

**Behavioral criteria (what they're doing):**
- Content consumption or engagement in your category
- Job postings that signal a problem you solve
- Conference attendance or speaker presence in your space
- Public statements from leadership about relevant priorities

> Separate must-haves from nice-to-haves. A must-have disqualifies a company if absent. A nice-to-have raises or lowers priority.

### Step 2: Source Identification

Use multiple sources — no single source is complete.

| Source Type | Best For | Watch Out For |
|-------------|----------|---------------|
| Company databases (Apollo, Clay, ZoomInfo) | Firmographic filtering at scale | Data staleness, headcount inflation |
| LinkedIn Sales Navigator | Title + company filters, recent activity | Limited to what's on LinkedIn |
| G2 / Capterra / review sites | Companies evaluating or using competitor tools | Only captures companies that write reviews |
| Job boards (LinkedIn Jobs, Comeet, Greenhouse) | Companies hiring for roles that signal pain or fit | Lags real hiring decisions by weeks |
| News & PR (Calcalist, Globes, TechCrunch) | Funding, M&A, expansion, leadership changes | Requires ongoing monitoring |
| Conference attendee lists | Concentrated ICP density | Requires access or research |
| Your CRM / existing network | Churned accounts, cold leads, previously lost deals | Often underutilized |
| Customer referrals | Warm introductions into lookalike accounts | Requires asking |
| Web search | Companies similar to best customers, competitor case studies | Manual effort, not scalable |

For each source, note: what filter criteria were applied, how many raw results returned, and estimated yield after qualification.

### Step 3: Web Research for Target Identification

Use web search to find companies matching the ICP. Search strategies:

1. **Direct search:** "[industry] companies [location] [size indicator]"
2. **Competitor customers:** "companies using [competitor name]" or "[competitor] case studies"
3. **Funding-based:** "Series [X] [industry] [year]"
4. **Community-based:** Companies active in relevant communities, events, directories
5. **Lookalike search:** "companies similar to [best customer name]"

For each company found, capture: company name, domain, why they match (which ICP criteria), and any known signals.

### Step 4: Qualification Pass

Raw lists from any source contain noise. Run every account through qualification before adding to the working list.

**Pass 1 — Hard disqualifiers (remove immediately):**
- Outside target geography
- Outside headcount/revenue range
- Wrong industry
- Already a customer, active opportunity, or blacklisted
- Competitor

**Pass 2 — ICP scoring:**

| Criterion | Weight | Score (1-3) |
|-----------|--------|-------------|
| Industry fit | High | |
| Company size fit | High | |
| Growth stage fit | Medium | |
| Tech stack fit | Medium | |
| Trigger / timing signal | High | |
| Persona presence confirmed | Medium | |

**Tier the output:**
- **Tier 1 — High priority:** Strong fit on must-haves + at least one timing signal. Move to active outreach.
- **Tier 2 — Medium priority:** Strong on firmographics, no clear trigger yet. Monitor and warm up.
- **Tier 3 — Low priority / watch list:** Partial fit. Don't invest now; revisit in 90 days.

### Step 5: Lookalike Expansion

Use existing Tier A customers as templates for finding more accounts.

For each reference customer, identify:
- What industry sub-vertical are they in exactly?
- What was their headcount and stage when they bought?
- What triggered the deal?
- What tech were they using alongside your product?
- What persona initiated the conversation?

Search for companies matching that precise pattern — not the broad ICP, the specific archetype that has already proven to buy.

> Cluster best customers into 2-3 archetypes if they're diverse. Prospect each archetype as a separate motion.

### Step 6: Contact Identification

For each prioritized account:

1. **Find the primary persona** — search for people matching target titles. Confirm they're active (LinkedIn activity, recent posts, current role tenure).
2. **Assess multi-thread opportunity** — who else is worth knowing? Map the buying committee even before outreach starts.
3. **Verify contact info** — for email outreach, confirm addresses are valid before sending. Bounces damage sender reputation.
4. **Document gaps** — note any account where you can't find the right contact. These may need a different entry approach.

### Step 7: Prioritization Logic

| Fit + Timing Combination | Action |
|--------------------------|--------|
| High fit + clear trigger | Move now — windows close |
| High fit + no trigger | Build awareness — stay close until trigger fires |
| Partial fit + clear trigger | Investigate before committing |
| Partial fit + no trigger | Deprioritize — don't manufacture urgency |

Stack-rank the Tier 1 list using this logic. The top accounts get the most personalized, highest-effort outreach.

### Step 8: Prospecting Cadence

Prospecting is not a one-time event. Build a rhythm:

| Activity | Frequency |
|----------|-----------|
| New account sourcing | Weekly or bi-weekly |
| Trigger monitoring on Tier 2 accounts | Weekly |
| Tier 3 review and re-qualification | Monthly |
| Lookalike refresh from new customer wins | After every closed deal |
| List hygiene (remove dead accounts, update data) | Monthly |

---

## Output Schema

Deliver one record per account for Tier 1:

```
ACCOUNT NAME:
Domain:
Industry:
Headcount:
Location:
Funding stage & last round:
ICP tier: [1 / 2 / 3]
Fit summary: [2 sentences — why this account fits]
Trigger: [specific signal and when it occurred, or "none identified"]
Primary contact: [name, title, LinkedIn — or "needs manual lookup"]
Secondary contact (optional): [name, title]
Recommended first move: [outreach / monitor / research deeper / skip]
Open questions: [what you still need to know before outreach]
```

For Tier 2 and 3, use the summary table format:

```
## Tier [2/3] Accounts
| # | Company | Domain | Industry | Size | Signal | Why They Fit | Next Review |
|---|---------|--------|----------|------|--------|-------------|-------------|
```

## Quality Checklist

- [ ] Every account passed the hard disqualifier filter — no exceptions
- [ ] Tier 1 accounts have at least one specific, recent trigger identified
- [ ] Each Tier 1 account has a named contact or a flagged gap
- [ ] The list has been stack-ranked — the top account is there for a clear reason
- [ ] You can articulate in one sentence why each Tier 1 account belongs there right now
- [ ] Every account has a defined next move
- [ ] Search criteria are documented so the list can be reproduced and refreshed
- [ ] No "spray and pray" — if Tier 1 has > 50 accounts, filters aren't tight enough

## Relationship to Other Skills

```
02-prospecting            →  find and tier accounts
01-icp-definition         →  provides the targeting criteria (run first)
04-account-research       →  deep-dive on Tier 1 accounts before outreach
03-outreach-strategy      →  execute outreach against the prioritized list
05-qualification-scoring  →  score inbound or identified accounts
06-signal-outbound        →  act on triggers as they fire on monitored accounts
```
