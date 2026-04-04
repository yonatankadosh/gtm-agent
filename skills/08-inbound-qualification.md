# Skill 08: Inbound Qualification

## Purpose

Qualify an unknown account — inbound lead, referral, event contact, or any company not yet in `target-accounts.md`. Determines which ICP the account fits, runs a full Skill 04-depth research, scores it, and routes it into the pipeline (Tier 1, Tier 2, or Pass) with a clear next action. Unlike running Skill 04 directly, this skill handles ICP classification and automatic pipeline routing in one motion.

## When to Use

- Someone referred a company to you
- A company approached you (inbound, event, demo request)
- You heard about a company and want to evaluate it fully
- Any account not yet in `target-accounts.md` that you want to research

**When NOT to use:** If the account is already in `target-accounts.md` and has a known ICP, use Skill 04 directly.

## Inputs

- `context/product-overview.md` (required)
- `context/competitive-landscape.md` (required)
- `context/customers.md` (required)
- `output/icp.md` (required)
- **Account identifier** — company name and/or domain provided by the user
- **Source** — how this account appeared (inbound, referral, event, manual research)

## Dependencies

- Skill 01: ICP Definition must be complete
- `context/competitive-landscape.md` must exist

## Output

Write to `output/research/{icp-folder}/{company-slug}.md`

The ICP folder is determined in Step 1. If no ICP fits, write to `output/research/{company-slug}.md` (root research folder).

If the score reaches Tier 1 or Tier 2 threshold, also update `output/target-accounts.md`.

---

## Methodology

### Step 1: ICP Classification

Before researching anything, answer one question: **which ICP does this account fit?**

Do a quick web search for the company basics (industry, business model, size, geography). Then match against the four ICPs:

| ICP | Quick Filter |
|---|---|
| **A: Full Suite** | Tech/SaaS company, 200-2,000+ employees, uses collaboration tools (Slack/Teams/Zoom), CISO likely present |
| **B: Intel Feed** | Bank, insurer, government, defense, critical infrastructure. 1,000+ employees. Runs a SOC with SIEM. |
| **C: Marketplace Chat** | Two-sided marketplace or platform with internal user-to-user messaging. 500+ employees. Trust & Safety function exists. |
| **D: Telecom** | Mobile network operator or MVNO. 1M+ subscribers. Carrier-level messaging infrastructure. |

**Classification rules:**
- If the account clearly fits one ICP, proceed with that classification.
- If the account could fit multiple ICPs (like Bezeq fits D and B), note both but pick the **primary** — the higher-value or more differentiated play.
- If the account fits **none** of the four ICPs, flag it as "No ICP fit" and skip to Step 3 (score Fit as 1, complete the scoring, and the account will likely route to Pass).

**Output of this step:** One sentence: "[Company] fits **ICP [X]** because [reason]." or "[Company] does not clearly fit any current ICP because [reason]."

### Step 2: Full Account Research

Run the complete Skill 04 methodology for this account. Use the ICP classification from Step 1 to guide which competitive landscape section to reference and which buyer personas to prioritize.

Execute all nine Skill 04 steps in order:

1. **Company Foundation** — business model, size, growth trajectory, funding, ownership
2. **Strategic Moment** — what's changed in the last 90 days that creates relevance
3. **ICP Assessment** — evaluate against the ICP identified in Step 1, criterion by criterion
4. **Technology & Operations** — tech stack, collaboration tools, operational maturity
5. **The Buying Committee** — economic buyer, champion candidate, influencer, blocker risk (includes Skill 04 Step **5b**: agent runs `apollo-enrich.py` for emails — not the user)
6. **Pain & Opportunity Mapping** — connect observable symptoms to the problems Cyvore solves
7. **Competitive Context** — read `context/competitive-landscape.md` for the matched ICP, identify what they use today, classify as displacing/supplementing/pioneering, build the competitive table, write discovery questions, flag risks
8. **Account Summary** — 150-250 word synthesis readable in 60 seconds
9. **Next Actions** — best next step based on the research

Follow the full Skill 04 methodology file (`skills/04-account-research.md`) for detailed instructions on each step. The output should be identical in depth and quality to any other account research file.

### Step 3: Score

Apply the same 4-dimension model as Skill 05. Score each 1-3 with a one-sentence justification.

| Dimension | What to Evaluate | Score |
|---|---|---|
| **Fit** | Does this company match the ICP criteria from Step 1? Use the ICP Assessment table from Step 2. | 1-3 |
| **Timing** | Is there a forcing function from the Strategic Moment section? Inbound/referral contact counts as a timing signal (score 2 minimum). | 1-3 |
| **Access** | Did the Buying Committee mapping find a reachable buyer? Is there a warm intro path (referral source, mutual connection, event)? | 1-3 |
| **Intent** | Did the account come inbound (score 3)? Were they referred (score 2)? Is there any behavioral signal? | 1-3 |

**Intent scoring for inbound accounts:**
- They requested a demo or contacted you directly → Intent = 3
- They were referred by a mutual connection → Intent = 2
- You found them yourself (event, news, manual research) → Intent = 1

### Step 4: Route

Apply the routing thresholds:

| Score | Tier | Action |
|---|---|---|
| **9-12** | **Tier 1** | Add to `target-accounts.md` under the matched ICP's Tier 1 section. Write research to `output/research/{icp-folder}/{company-slug}.md`. Recommend immediate outreach. |
| **7-8** | **Tier 2 (Monitor)** | Add to `target-accounts.md` under the matched ICP's Tier 2 table. Write research file. Set a review date (30-60 days). Identify the signal that would upgrade them. |
| **Below 7** | **Pass** | Write a brief research file with "why not" explanation. Do NOT add to `target-accounts.md`. |

**When adding to `target-accounts.md`:**

For Tier 1, use the standard account entry format:

```
ACCOUNT NAME: [Company]
Domain: [url]
Industry: [industry]
Headcount: [size]
Location: [HQ]
Funding stage & last round: [details]
ICP tier: 1
Fit summary: [2-3 sentences from the account research]
Trigger: [timing signal from Strategic Moment]
Primary contact: [champion or economic buyer from Buying Committee]
Secondary contact: Needs manual lookup
Recommended first move: [from Step 5]
Open questions: [key unknowns]
```

For Tier 2, add a row to the Tier 2 monitoring table in the relevant ICP section.

### Step 5: Recommend Next Action

Based on the routing decision:

**Tier 1 (score 9+):**
> "Run Skill 03 (Outreach Strategy) to draft outreach to [specific contact name]." Full research is already complete — no need for a separate Skill 04 run.
> If the account came inbound: "Respond within 24 hours. Run Skill 07 (Meeting Prep) if a meeting is already scheduled."

**Tier 2 (score 7-8):**
> "Monitor for [specific signal that would upgrade this account]. Re-evaluate on [date, 30-60 days out]. The upgrade trigger is: [what needs to change]."

**Pass (score below 7):**
> "Not a fit because [one-sentence reason]. Do not pursue. [Optional: 'Could revisit if [specific condition changes].']"

---

## Output Schema

Uses the full Skill 04 output schema with three additions at the top (source, ICP classification) and a qualification section appended at the end.

```
# Account Research: [Company Name]

**Researched:** [date]
**Domain:** [url]
**Source:** [inbound / referral from X / event / manual research]
**ICP Classification:** [A / B / C / D / None] — [one-sentence justification]
**ICP Fit:** [Strong / Partial / Weak]

## Company Foundation
- **What they do:** ...
- **Industry:** ...
- **Size:** ... employees
- **Revenue (est.):** ...
- **Funding:** [last round, amount, date, investors]
- **Growth trajectory:** ...

**So what:** [1-2 sentences on what this means for us]

## Strategic Moment
- [Bullet list of what's changed in the last 90 days]

**So what:** [The most relevant "why now"]

## ICP Assessment
| Criterion | What You See | Fit |
|-----------|-------------|-----|
| Industry | ... | Strong/Partial/Weak |
| Size | ... | ... |
| Growth stage | ... | ... |
| Tech stack | ... | ... |
| Personas | ... | ... |
| Pain signals | ... | ... |

**Verdict:** [Strong/Partial/Weak] — [one sentence why]

## Technology
- **Collaboration stack:** ...
- **Relevant tools:** ...
- **Competitive tools:** ...

## Key People
| Role | Name | Title | Signal | LinkedIn |
|------|------|-------|--------|----------|
| Champion candidate | ... | ... | ... | ... |
| Economic buyer | ... | ... | ... | ... |
| Influencer | ... | ... | ... | ... |

## Pain & Opportunity
[Value proposition mapping paragraph]

## Competitive Context
**Situation:** [Displacing / Supplementing / Pioneering]

| Competitor | What They Cover | What They Miss | Our Angle |
|---|---|---|---|
| ... | ... | ... | ... |

**Discovery questions:**
1. ...
2. ...

**Risks:** [Contract lock-in, vendor relationships, build-vs-buy tendency]

## Account Summary (60-second read)
[150-250 word synthesis]

---

## Qualification Score

**Total: [X]/12 — Routing: [Tier 1 / Tier 2 / Pass]**

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Fit | .../3 | ... |
| Timing | .../3 | ... |
| Access | .../3 | ... |
| Intent | .../3 | ... |

### Assessment
- **Biggest risk:** [the single most likely reason this deal doesn't happen]
- **Key unlock:** [the one thing that would move this up one band]

## Routing Decision

**[Tier 1 / Tier 2 / Pass]**

[One paragraph: what this means and why]

## Next Action

[Specific recommendation — who to contact, what to do, or why to wait]

## Research Gaps
- [ ] ...
```

---

## Quality Checklist

- [ ] ICP classification has a one-sentence justification grounded in the account's industry, size, and business model
- [ ] Full Skill 04 methodology was followed — all nine steps completed with "So what" interpretation
- [ ] Every score dimension has a one-sentence justification based on data from the research
- [ ] No company data is fabricated — everything comes from web search or is flagged as "needs verification"
- [ ] The routing decision matches the score threshold (9+ = Tier 1, 7-8 = Tier 2, <7 = Pass)
- [ ] If Tier 1 or Tier 2: `target-accounts.md` has been updated
- [ ] Next action is specific — names a person, a skill to run, or a signal to monitor
- [ ] Research gaps are listed so the user knows what to verify manually
- [ ] Apollo enrichment was attempted for named contacts per Skill 04 Step 5b, or documented if skipped

---

## Relationship to Other Skills

```
08-inbound-qualification →  full research + qualification of unknown accounts
01-icp-definition        →  provides the ICP criteria for classification
04-account-research      →  same research methodology, used inline (no separate run needed)
05-qualification-scoring →  same scoring model, embedded inline
03-outreach-strategy     →  run AFTER Skill 08 for Tier 1 accounts (outreach drafts)
07-meeting-prep          →  run if a meeting is already scheduled (inbound)
```

**Typical sequence for an inbound lead:**
```
Skill 08 (research + qualify + route) → if Tier 1 → Skill 03 (outreach)
                                      → if meeting scheduled → Skill 07 (meeting prep)
                                      → if Tier 2 → monitor, re-evaluate later
                                      → if Pass → log and move on
```
