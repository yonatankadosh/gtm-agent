# Skill 05: Qualification & Scoring

## Purpose

Score any company across four dimensions — Fit, Timing, Access, Intent — and produce a clear, data-backed priority decision with a specific next action. Eliminates gut-feel prioritization. Use for evaluating prospected accounts, scoring inbound leads, or re-qualifying pipeline accounts.

## Inputs

- `output/icp.md` (required)
- `output/research/{company-slug}.md` (required — run Skill 04 first)

## Dependencies

- Skill 01: ICP Definition
- Skill 04: Account Research (for the specific account)

## Output

Append the score to the existing research file: `output/research/{company-slug}.md`

---

## Methodology

### Step 1: Collect the Raw Data

Before scoring anything, gather what's knowable. Don't score on assumptions.

**Minimum required to score:**
- Company name and website
- Headcount (or range)
- Industry / vertical
- Geography
- What triggered this evaluation (inbound, signal, outbound, manual review)

**Better scoring requires:**
- Revenue or funding stage
- Tech stack
- Growth signals (hiring trends, funding, expansion news)
- Current contact — who specifically, their role and seniority
- Prior relationship — have we spoken before? What happened?

> If minimum data isn't available, enrich before scoring. Scoring on incomplete data produces misleading scores.

### Step 2: Score Across Four Dimensions

Score each dimension **1-3**. No halves. Forced precision.

---

#### Dimension 1 — Fit (Does this company match the ICP?)

| Score | Criteria |
|-------|---------|
| **3** | Matches on all major ICP criteria (industry, size, geography, use case). Looks like existing best customers. |
| **2** | Matches on most criteria. One or two gaps that aren't disqualifying. |
| **1** | Significant gaps. Could work but would require adapting the product, process, or pitch. |
| **0** | Hard disqualifier present — stop evaluation. |

**Hard disqualifiers (score = 0, stop all scoring):**
- Explicitly blocked industry or geography
- Competitor
- Company size far outside viable range
- Known bad history (churned badly, legal issue, do-not-contact)

> If score = 0 on Fit, stop. Do not continue scoring. Log the disqualifier and move on.

---

#### Dimension 2 — Timing (Is there a reason to buy now?)

Timing is the hardest dimension to fake. A perfect ICP fit with no timing signal is a future deal, not a current one.

| Score | Criteria |
|-------|---------|
| **3** | Clear forcing function present. |
| **2** | Soft timing indicators. Growing team, relevant hiring, prior interest that went cold. |
| **1** | No visible timing signal. Good company, wrong moment. |

**What counts as a forcing function (score = 3):**
- New budget (funding, new fiscal year, budget approved)
- New mandate (leadership change, new hire with a specific brief)
- External pressure (regulatory change, competitor move, market shift)
- Active pain (they're clearly feeling the problem right now — incident, breach, audit finding)
- Inbound or self-initiated contact (they came to you — that IS the timing signal)

---

#### Dimension 3 — Access (Can we reach the right people?)

A qualified company you can't get to is not a qualified opportunity.

| Score | Criteria |
|-------|---------|
| **3** | Decision maker or strong champion identified, reachable, and engaged or likely to engage. |
| **2** | Right company, but only peripheral contacts (wrong seniority, wrong department) or no warm path in. |
| **1** | No contact identified, no warm intro path, cold outreach unlikely to land. |

**Access accelerators (upgrade by 1 if any apply):**
- Mutual connection or warm intro available
- Contact already in CRM with prior positive interaction
- Contact engaged with your content or visited your site
- You've worked with this person at a previous company
- Met at an event (CyberWeek, SecureConnect, etc.)

**Access killers (downgrade by 1 if any apply):**
- Only contact is a gatekeeper or procurement
- Company has "no cold outreach" policy or explicit opt-out
- Prior outreach was rejected or marked spam

---

#### Dimension 4 — Intent (Do they show signs of actively looking?)

Intent is distinct from timing. Timing = they have a reason to buy. Intent = they're showing behavioral signals of evaluation.

| Score | Criteria |
|-------|---------|
| **3** | Direct behavioral signal: visited pricing/demo pages, requested a demo, downloaded evaluation content, mentioned competitors, asked specific product questions. |
| **2** | Indirect signal: engaged with thought leadership, attended a webinar, LinkedIn activity on relevant topics, intent data showing research in your category. |
| **1** | No detectable intent signal. Outbound-initiated with no response or engagement yet. |

> If you have no intent signal access (no website tracking, no intent tool), score this dimension as 2 for all accounts and note the data gap. Absence of data is not the same as absence of intent.

---

### Step 3: Calculate the Composite Score

Add the four dimension scores. Maximum = 12.

| Score | Band | Action |
|-------|------|--------|
| 10-12 | **Priority** | Act immediately. Engage within 24 hours, multi-thread if possible. |
| 7-9 | **Active** | Worth pursuing now. Build a sequence, personalize outreach, move into active pipeline. |
| 4-6 | **Nurture** | Not the right moment. Low-touch track, review trigger in 60-90 days. |
| 1-3 | **Deprioritize** | Poor fit or too early. Log it, don't spend cycles. Revisit only if a strong new signal appears. |
| 0 | **Disqualified** | Disqualifier hit. Log the reason. Do not requeue. |

### Step 4: Validate Before Acting

A score is a starting point, not a final answer.

**Recency check:** Is the data current? Funding from 18 months ago, a contact who left the company, or a filled job posting all produce stale scores. Flag data points older than 6 months.

**Consistency check:** Does the score feel right holistically? If a company scores 10 but something feels off, flag it for review rather than auto-acting.

**Competing signals check:** Are there positive and negative signals that cancel each other out? Note conflicts explicitly.

### Step 5: Recommend a Next Action

Every scored company leaves this process with one clear next step.

**Priority (10-12):**
- Identify the best contact and outreach angle immediately
- If inbound: respond within the hour
- If outbound-identified: trigger signal-based outreach today

**Active (7-9):**
- Determine the right sequence (channel, length, angle)
- Personalize based on the highest-scoring dimension
- Set a follow-up checkpoint at 2 weeks

**Nurture (4-6):**
- Add to a relevant monitor list
- Identify what would upgrade this account (what signal would make it Priority?)
- Set a review date — don't let it sit indefinitely

**Deprioritize (1-3):**
- Log the score and reason
- No outreach
- Set a 90-day review trigger tied to new signal activity only

**Disqualified (0):**
- Log the disqualifier
- Remove from active pipeline
- Tag to prevent re-entry

### Step 6: Log the Score

Record for every evaluated company:
- Date scored
- Score per dimension and total
- Data sources used
- Key reasoning (1-2 sentences)
- Recommended next action

> Calibrate the model every quarter against actual outcomes. If your 7-9 band closes at the same rate as your 10-12 band, scoring is too generous at the top.

---

## Output Schema

Append this to the end of the existing research file:

```
---

## Qualification Score

**Scored:** [date]
**Total: [X]/12 — Band: [Priority / Active / Nurture / Deprioritize / Disqualified]**

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Fit | .../3 | ... |
| Timing | .../3 | ... |
| Access | .../3 | ... |
| Intent | .../3 | ... |

### Assessment
- **Biggest risk:** [the single most likely reason this deal doesn't happen]
- **Key unlock:** [the one thing that would move this up one band]
- **Recommended next action:** [specific — which person, which channel, what angle, or why to wait]
- **Review date:** [when to re-score if not acting now]
```

## Quick Reference — Scoring Cheatsheet

| Dimension | 3 | 2 | 1 | 0 |
|-----------|---|---|---|---|
| **Fit** | Perfect ICP match | Most criteria met | Significant gaps | Disqualifier |
| **Timing** | Clear forcing function | Soft indicators | No signal | — |
| **Access** | DM identified + reachable | Wrong contact or no path | No contact, no path | — |
| **Intent** | Direct behavioral signal | Indirect engagement | No signal detected | — |

| Total | Band | Action |
|-------|------|--------|
| 10-12 | Priority | Act within 24h |
| 7-9 | Active | Build sequence now |
| 4-6 | Nurture | Low-touch, review in 60-90d |
| 1-3 | Deprioritize | Log, no outreach |
| 0 | Disqualified | Remove and tag |

## Quality Checklist

- [ ] Every score has a one-sentence justification grounded in data, not vibes
- [ ] "No data" is scored honestly and flagged, not defaulted to 0
- [ ] The overall band passes the gut check
- [ ] Biggest risk is specific to this account, not generic
- [ ] Key unlock is actionable — something you can actually go do
- [ ] Recommended next action names a specific person, channel, and angle (or a specific reason to wait)
- [ ] Stale data is flagged

## Relationship to Other Skills

```
05-qualification-scoring  →  score and tier accounts
04-account-research       →  enrichment input for scoring; deep-dive on Priority accounts
02-prospecting            →  qualification pass on a list of candidates
03-outreach-strategy      →  execute against Priority and Active accounts
06-signal-outbound        →  when a new signal fires and upgrades a Nurture account
```
