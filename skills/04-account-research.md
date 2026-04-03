# Skill 04: Account Research

## Purpose

Build a deep, actionable commercial picture of a target account before outreach, a sales meeting, or strategic planning. The output answers: who they are, what's happening in their world right now, how well they fit the ICP, who the right people are, and what your angle should be. Always run this before Outreach Strategy (Skill 03). Works best when paired with Qualification & Scoring (Skill 05).

## Inputs

- `context/product-overview.md` (required)
- `context/competitive-landscape.md` (required — read the relevant ICP section before Step 7)
- `output/icp.md` (required)
- **Account identifier** — company name and/or domain provided by the user

## Dependencies

- Skill 01: ICP Definition must be complete
- `context/competitive-landscape.md` must exist (for Step 7)

## Output

Write to `output/research/{company-slug}.md`

---

## Methodology

Work through the following areas in order. Synthesize as you go — don't just list facts. At each step, ask: **"So what — what does this mean for us?"**

### Step 1: Company Foundation

Understand what this company actually does and where it stands.

- **Business model:** What do they sell, to whom, and how?
- **Size & scale:** Headcount, revenue (if known), number of offices, geographic footprint.
- **Growth trajectory:** Scaling fast, plateauing, or contracting? Look at headcount trend, funding history, expansion signals.
- **Funding:** Total raised, last round, lead investors, and when. Series stage signals urgency and budget availability.
- **Ownership:** Public, private, VC-backed, PE-backed, bootstrapped? Affects buying behavior and budget cycles.

**So what:** Is this company in a phase where they'd be spending or saving? Are they scaling into problems your product solves?

### Step 2: Strategic Moment

Identify what's happening right now that creates relevance. Look for changes in the last 90 days.

- Recent funding announcements
- Leadership changes (new CISO, VP Security, CTO)
- Acquisitions or being acquired
- Product launches or market expansion
- Hiring surges in specific functions
- Layoffs or restructuring
- Press coverage or earnings commentary
- Industry headwinds/tailwinds affecting their business
- Security incidents or breaches (public or inferred)

**So what:** What's the most relevant "why now" for reaching out? What's changed recently that creates a window?

### Step 3: ICP Assessment

Evaluate how well this company matches the ICP. Go through each criterion explicitly:

| Criterion | What You See | Fit (Strong / Partial / Weak) |
|-----------|-------------|-------------------------------|
| Industry | | |
| Company size | | |
| Growth stage | | |
| Tech stack / infrastructure | | |
| Business model | | |
| Personas present | | |
| Pain signals | | |

**Overall ICP verdict:** Strong fit / Partial fit / Weak fit — and why in one sentence.

> If fit is weak, flag it clearly. Don't manufacture a pitch.

### Step 4: Technology & Operations

Research their tech stack and operational setup.

- **Known tech stack:** What tools/platforms do they use? Check job postings, BuiltWith, G2 reviews they've left, integration pages.
- **Relevant tools:** Do they use tools your product integrates with or replaces?
- **Collaboration stack:** Which communication/collaboration platforms? (Slack, Teams, Zoom, Google Meet, WhatsApp Business, Jira, CRM)
- **Operational maturity:** Scrappy or process-heavy? Inferred from company stage, job descriptions, blog posts.

**So what:** Are you displacing something, filling a gap, or pioneering? This shapes the angle.

### Step 5: The Buying Committee

Map the people involved in a decision like yours.

- **Economic buyer:** Who controls budget? (Usually CISO or VP-level in the relevant function)
- **Champion candidate:** Who feels the pain most and would advocate internally?
- **Influencer:** Who else touches this decision? (IT, legal, procurement, a consulted peer)
- **Blocker risk:** Anyone likely to resist or own the incumbent solution?

For each key person, note: name, title, tenure, LinkedIn activity or recent posts, and any signals of pain or initiative relevant to your product.

**So what:** Who is the right first contact? What's their likely priority right now?

### Step 6: Pain & Opportunity Mapping

Connect what you know about this company to the problems your product solves.

- What symptoms of the problem can you observe externally? (job postings, tech stack, company stage, public statements, security incidents)
- What are they likely doing today to solve this? (manual work, a competitor, nothing)
- What's the cost of inaction — what gets worse if they don't address this?

Map to the value proposition:

> *"They are likely experiencing [specific pain], which costs them [impact]. We solve this by [approach], which would specifically help them [concrete outcome]."*

### Step 7: Competitive Context

Read `context/competitive-landscape.md` for the relevant ICP before completing this step.

**7a. Identify what they're using today.**

Research which competitors or approaches this account currently uses:
- Check job postings for vendor names (e.g., "Proofpoint experience required," "Mimecast admin")
- Check tech stack databases (BuiltWith, Wappalyzer, G2 Stack)
- Look for vendor partnership announcements, case studies, or press mentions
- Check LinkedIn profiles of security team members for vendor certifications or experience
- Look for G2/Capterra reviews the company has left

**7b. Classify the competitive situation.**

| Situation | What It Means | Urgency |
|-----------|---------------|---------|
| **Displacing an incumbent** | They have a tool in the same space. You need to prove superiority or a gap the incumbent doesn't fill. | Medium — requires clear differentiation and possibly a trigger event (contract renewal, dissatisfaction, incident). |
| **Supplementing existing tools** | They have adjacent tools (e.g., email security) but nothing covering the specific gap Cyvore fills. | High — no switching cost, additive value, easier budget justification. |
| **Pioneering (no solution)** | They have nothing — manual review, keyword filters, or simply unaware of the gap. | Variable — if they feel the pain, urgency is high. If they don't know the gap exists, you need to create awareness. |

**7c. Build the competitive table.**

For each relevant competitor (from the landscape file or discovered through research), produce:

| Competitor | What They Cover | What They Miss (Cyvore's Gap) | Account-Specific Angle |
|---|---|---|---|
| [Name] | [Their coverage for this account] | [The gap Cyvore fills] | [Why this matters for THIS account specifically] |

**7d. Write 2-3 discovery questions that expose the gap.**

These are questions to ask in the first call that reveal whether the competitive gap exists. Pull from the landscape file's trap questions and tailor to this account's situation.

**7e. Flag competitive risks.**

- Is the account locked into a multi-year contract with a competitor?
- Does the security team have strong personal relationships with incumbent vendors?
- Does this account have a "build vs. buy" tendency (especially relevant for ICP C marketplaces)?
- Is there a recent vendor evaluation or RFP that Cyvore missed?

**So what:** Clearly state whether you're displacing, supplementing, or pioneering — and what that means for the outreach angle and objection profile.

### Step 8: Account Summary

Synthesize everything into a single commercial picture. 150-250 words, readable in 60 seconds.

Structure:
1. Who they are (1-2 sentences)
2. Where they are right now — strategic moment, growth stage
3. ICP fit verdict — and the key reason
4. The angle — the most credible reason to reach out, tied to a specific signal
5. Recommended first contact — who, why them, what to lead with
6. Open questions — what you still don't know that would change your approach

### Step 9: Next Actions

Based on the research, recommend the single best next step:

- **Initiate outreach** — specify: email, LinkedIn, or call — and to whom
- **Escalate for review** — weak ICP, complex situation, or existing relationship
- **Deprioritize** — poor fit, explain why
- **Monitor** — good fit but wrong timing, set a trigger for when to revisit

---

## Output Schema

```
# Account Research: [Company Name]

**Researched:** [date]
**Domain:** [url]
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

## Next Action
[One specific recommended step]

## Research Gaps
- [ ] ...
```

## Quality Checklist

- [ ] You have a clear "why now" — not just "this company looks interesting"
- [ ] The ICP assessment is honest, not optimistic
- [ ] Every fact comes from web search, not fabricated
- [ ] The recommended contact is a real person, not a generic title
- [ ] The next action is specific and actionable
- [ ] You haven't reported facts without interpreting what they mean commercially ("So what")
- [ ] Research gaps are listed so the user knows what to verify manually

## Relationship to Other Skills

```
04-account-research       →  understand the account (run first for any specific company)
01-icp-definition         →  provides the criteria to assess fit
02-prospecting            →  find accounts like this one
03-outreach-strategy      →  execute outreach based on this research
05-qualification-scoring  →  score this account's priority
07-meeting-prep           →  prepare for the call once it's booked
```
