# Skill 01: ICP Definition

## Purpose

Build or pressure-test your Ideal Customer Profile from actual customer data. The ICP is the foundation everything else in GTM is built on — if it's wrong, everything downstream is wrong faster, at scale, with more confidence. Rerun this skill every 6 months or after any significant product, pricing, or market change.

## Inputs

- `context/product-overview.md` (required)
- `context/customers.md` (required — even 2-3 customers are enough to start. If zero customers, identify 5-10 dream-fit companies and explain why)

## Dependencies

None. This is the starting skill.

## Output

Write to `output/icp.md`

---

## Methodology

### Step 1: Establish the Purpose

An ICP is not a wish list. It is a pattern extracted from reality.

An ICP is used to:
- Prioritize which companies to pursue (and which to ignore)
- Guide outbound targeting and list building
- Score and qualify inbound leads quickly
- Align the full GTM motion on who the customer is
- Make resource allocation decisions — where to spend time and money

An ICP is NOT:
- A persona (that is a person, not a company)
- A TAM exercise (ICP is about fit quality, not market size)
- A permanent document (it should evolve as you learn)

### Step 2: Tier Existing Customers

The fastest path to an accurate ICP is backward — look at who already bought and succeeded.

For each current or past customer, collect: company size, industry, geography, business model, tech stack, how they found you, time to close, expansion or contraction since signing, health/satisfaction, and why they churned (if applicable).

Sort into three tiers:

**Tier A — Best customers.** Bought fast, adopted fully, expanded, refer others, easy to support, clearly get value.
**Tier B — Average customers.** Fine. Paid. Not churned. Not excited. Require normal effort.
**Tier C — Bad customers.** Churned, struggling, never adopted, required disproportionate support, or the relationship is difficult.

Build the ICP from Tier A only. Not from the average of all customers. Optimizing for the average means optimizing for mediocrity.

> If fewer than 5 Tier A customers exist, acknowledge that the ICP is a hypothesis — not a validated pattern.

### Step 3: Find the Pattern in Tier A

Look across Tier A customers and identify what they have in common. Look for signal, not coincidence.

**Firmographic patterns (the "who"):**
- Consistent size range? (headcount and/or revenue)
- Concentrated in specific industries?
- Shared geography or market?
- Same business model or revenue structure?

**Situational patterns (the "when"):**
- What was happening at the company when they bought? (rapid growth, leadership change, new initiative, scaling pains)
- Specific stage of their own lifecycle?
- Consistent purchase trigger/catalyst?

**Behavioral patterns (the "how they buy"):**
- How did they find you? (inbound, outbound, referral, event)
- How long did they take to buy?
- Who was involved in the decision?
- What made them choose you over alternatives?

**Value patterns (the "why it works"):**
- What outcome did they hire you to achieve?
- What metric improved as a result?
- How do they describe the value to colleagues?

Look for 3-5 attributes that appear in 80%+ of Tier A customers. Those are ICP criteria. Attributes appearing in less than half are nice-to-haves, not requirements.

### Step 4: Define the Negative ICP

Knowing who is NOT your ICP is as important as knowing who is. It prevents wasted cycles.

From Tier C customers, extract:
- What firmographic traits did bad customers share?
- What was their situation when they bought? (oversold to, wrong use case, too early, too late)
- What was the tell that was visible before the sale — that was ignored?
- What objections or concerns should have been disqualifying?

Document the negative ICP explicitly. "We do not sell to X" is a policy, not a failure.

### Step 5: Define Buying Triggers

A company that fits the ICP perfectly but has no reason to buy right now is not a prospect — they are a future prospect. The buying trigger separates the two.

**Types of buying triggers:**

| Trigger Type | Description |
|-------------|-------------|
| Growth trigger | Scaling faster than current tools/processes can handle |
| Pain trigger | Specific problem has become acute enough that status quo is unacceptable |
| Event trigger | Funding, acquisition, leadership change, product launch, market expansion |
| Competitive trigger | Competitor gaining ground, need to respond |
| Compliance trigger | Regulatory or legal deadline forcing action |
| Budget trigger | New fiscal year, budget approved, or previous tool contract expiring |

For the ICP, identify:
- The primary buying trigger (the one that appears most often in Tier A)
- 1-2 secondary triggers
- What the trigger looks like from the outside — the observable signal that tells you the trigger has fired

> The observable signal is what turns the ICP into a targetable list. "Series B cybersecurity company that just had a phishing incident via Slack" is actionable. "Series B cybersecurity company" is a list.

### Step 6: Define the Buying Committee

Even with a perfect ICP company and a live trigger, you need to reach the right people.

**Economic buyer** — who approves the budget? What business outcome do they care about?

**Champion** — who wants this to happen internally? What is their role, their motivation, their ability to influence?

**End user / evaluator** — who will use the product day-to-day? What does success look like in their workflow?

**Influencer** — who has input but not final authority? (IT, legal, procurement, a consulted peer)

**Blocker** — who might slow or kill the deal? What is their concern and what would resolve it?

For each role, document:
- Typical title(s) at ICP companies
- What they care about (their job-to-be-done)
- What messaging resonates with them
- How they typically behave in an evaluation

The buying committee should reflect Tier A customer reality — not org chart theory. If the CFO never shows up in your deals, do not build a CFO strategy.

### Step 7: Pressure-Test the ICP

Before committing, validate:

**Test 1 — The exclusion test.** Apply the ICP criteria to your current pipeline. Does it cleanly separate deals you're excited about from the ones you're grinding on? If not, criteria aren't sharp enough.

**Test 2 — The prediction test.** Pick 10 companies you haven't sold to. Apply the ICP and predict which would be Tier A. Can you articulate clearly why? If criteria don't produce confident predictions, they're too vague.

**Test 3 — The list test.** Try to build a prospect list using only ICP criteria. Can you find 50-100 companies that match? If yes, the ICP is specific enough to be useful and broad enough to be a real market. If you find 10,000, criteria are too loose. If 12, market is too narrow.

### Step 8: Connect ICP to Every GTM Function

An ICP that lives in a folder is worthless. It must be operationalized.

| GTM Function | How ICP Connects |
|-------------|-----------------|
| Scoring (Skill 05) | Use ICP criteria as the Fit dimension in qualification scoring |
| Targeting (Skill 02) | Build prospect lists using ICP firmographics + observable trigger signals |
| Outreach (Skill 03) | Use buying triggers and committee roles to personalize messaging angle |
| Account Research (Skill 04) | Use ICP criteria as a checklist to validate fit for specific accounts |
| Signal Outbound (Skill 06) | Use trigger definitions to classify and act on signals |
| Meeting Prep (Skill 07) | Use buying committee roles to prepare contact strategy |

---

## Output Schema

Write the output as a structured markdown document:

```
# Ideal Customer Profile

LAST UPDATED: [date]
NEXT REVIEW: [date — 6 months out]
CONFIDENCE LEVEL: [Low (<5 Tier A) / Medium (5-15) / High (15+)]

## Profile: [Name — e.g., "Mid-market tech scale-up"]

### Firmographic Criteria
- Industry: ...
- Company size: ...
- Geography: ...
- Business model: ...
- Tech stack signals: ...

### Situational Criteria
- Stage / lifecycle: ...
- Primary buying trigger: ...
- Secondary triggers: ...
- Observable signals (what the trigger looks like from outside): ...

### Buying Committee
- Economic buyer: [title, priorities, messaging angle]
- Champion: [title, motivation, where they hang out]
- End user / evaluator: [title, what they care about]
- Influencer: [title, role in the decision]
- Blocker: [who, their concern, how to resolve]

### Value Proposition for This Segment
[Why PMF is strongest here. 2-3 sentences.]

### Negative ICP / Disqualifiers
| Segment | Why Exclude | Visible Before Sale? |
|---------|-------------|---------------------|
| ... | ... | ... |

## [Repeat for additional ICP profiles if needed]

## Validation Questions
1. ...
2. ...
3. ...

## Confidence & Gaps
[What are you most/least confident about? What data is missing?]
```

## Quality Checklist

- [ ] ICP is built from Tier A customers only — not the average of all customers
- [ ] Firmographic criteria are concrete and searchable (usable in Apollo/LinkedIn filters)
- [ ] Buying triggers have observable signals — not just theoretical situations
- [ ] Buying committee reflects actual deal patterns, not org chart assumptions
- [ ] Negative ICP is explicit with visible pre-sale tells
- [ ] ICP passes the exclusion test, prediction test, and list test
- [ ] Every claim is grounded in customer data or clearly flagged as a hypothesis
- [ ] Validation questions test the weakest assumptions, not confirm the strongest

## Relationship to Other Skills

```
01-icp-definition         →  run first. Everything downstream depends on this.
02-prospecting            →  uses ICP firmographics + triggers to build targeted lists
03-outreach-strategy      →  uses buying triggers and committee roles for messaging
04-account-research       →  validates ICP fit for a specific account before outreach
05-qualification-scoring  →  uses ICP criteria as the Fit dimension
06-signal-outbound        →  uses trigger definitions to classify and act on signals
07-meeting-prep           →  uses buying committee roles to prepare contact strategy
```
