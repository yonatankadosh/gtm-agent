# Skill 07: Meeting Prep

## Purpose

Prepare a comprehensive pre-meeting brief for any sales or discovery call. The brief ensures you walk in with a clear objective, deep context on the people and the company, prepared questions that drive the conversation forward, and anticipated objections with responses ready. No one should ever walk into a meeting wondering what to say first.

## Inputs

- `context/product-overview.md` (required)
- `output/icp.md` (required)
- `output/research/{company-slug}.md` (required — run Skill 04 first)
- **Meeting details** — who's attending, what type of meeting (discovery, demo, follow-up, proposal), any prior conversation context

## Dependencies

- Skill 04: Account Research (must have research on the account)
- Helpful: Skill 05 (Qualification Score), prior outreach history

## Output

Write to `output/meeting-prep/{company-slug}-{date}.md`

---

## Methodology

### Step 1: Define the Meeting Objective

Before preparing anything, answer three questions:

1. **What type of meeting is this?**
   - Discovery — understand their situation, qualify the opportunity
   - Demo — show specific capabilities mapped to their pain
   - Follow-up — advance the deal, resolve open questions
   - Proposal / pricing — present a commercial offer
   - Partnership discussion — explore channel or integration opportunity

2. **What's the single most important outcome?**
   State it in one sentence: *"After this meeting, I want [specific outcome]."*

   Examples:
   - "After this meeting, I want to confirm the CISO is the budget holder and understand their current security stack gaps."
   - "After this meeting, I want agreement to run a 30-day POC with their security team."
   - "After this meeting, I want to understand their evaluation timeline and who else needs to be involved."

3. **What's the minimum acceptable outcome?**
   Even if the call doesn't go perfectly, what must you leave with?
   - A next step with a date
   - Answers to 2-3 key qualification questions
   - Access to a new stakeholder

> If you can't clearly state the objective, you're not ready for the meeting.

### Step 2: Profile Every Attendee

For each person on the call, research and document:

**Professional context:**
- Name, title, role, reporting line
- Tenure at the company (new hires behave differently than lifers)
- Career trajectory — where did they come from? Where are they likely headed?
- LinkedIn activity — recent posts, comments, articles shared
- Speaking engagements, published content, podcast appearances

**What they care about (role-based inference + research):**
- What are the top 3 priorities for someone in their role right now?
- What are they likely measured on?
- What would make them look good internally?
- What keeps them up at night?

**Relationship to the deal:**
- Are they the economic buyer, champion, evaluator, influencer, or blocker?
- What's their likely stance? (Excited, neutral, skeptical, hostile)
- Have they interacted with your company before? (Prior outreach, event, content)

**Personal connection points:**
- Shared connections, shared alma mater, shared previous employers
- Interests visible from social media (hobbies, causes, communities)
- Recent personal milestones (promotion, publication, award)

> Use these for rapport-building, not for manipulation. People know when you're being genuine.

### Step 3: Refresh Account Context

Pull the latest on the company. Research may be outdated.

- Any new developments since the account research was done?
- Changes in leadership, funding, product, or market position?
- Recent press, social media activity, or public statements?
- Any signals from their online activity? (job posts pulled, new postings, G2 reviews)

Update the account research file if anything significant has changed.

### Step 4: Prepare Discovery Questions

Prepare questions organized by what you need to learn. Tailor to the meeting type.

**Situation questions (understand their world):**
- "How does your team currently handle [specific problem area]?"
- "Walk me through what happens when [trigger event] occurs today."
- "What tools are involved in [specific workflow] right now?"

**Pain questions (find and size the problem):**
- "What's the biggest gap in your current approach to [domain]?"
- "When [specific incident] happened, how did your team respond? What was the impact?"
- "What does it cost you — in time, money, or risk — when [problem] happens?"

**Implication questions (make pain urgent):**
- "If this doesn't get solved in the next [timeframe], what happens?"
- "How does this affect your ability to [strategic priority]?"
- "What's the board / leadership asking you about in this area?"

**Need-payoff questions (tie to your solution):**
- "If you could [desired outcome], what would that change for your team?"
- "How would you measure success if you solved this?"
- "What would it mean for your [metric] if [specific capability] were available?"

**Process questions (understand how they buy):**
- "Who else would need to be involved in evaluating something like this?"
- "What does your evaluation process typically look like?"
- "Is there a timeline or event driving this?"
- "Have you looked at other solutions?"

> Prepare 8-10 questions. You won't ask all of them. Prioritize based on what you most need to learn. Let the conversation flow naturally — don't interrogate.

### Step 5: Map Your Value to Their World

Based on account research and ICP analysis, pre-map the value propositions most likely to resonate.

**For each potential pain point:**
- The symptom they'd describe
- The root cause your product addresses
- The specific capability that maps to it
- A proof point (customer name + result) from a similar company
- How to explain it without jargon in 2 sentences

> If demoing: prepare a demo flow that follows their pain narrative, not your product's feature list. Show the 2-3 things that matter to them, not the full platform tour.

### Step 6: Anticipate Objections

Based on the account profile, predict the 3-5 most likely objections and prepare responses.

**Common objections and response frameworks:**

| Objection | Response Approach |
|-----------|------------------|
| "We already have a solution for this." | Acknowledge. Ask what it covers and what gaps remain. Position as complementary or show the blind spots. |
| "We're not looking at this right now." | Understand why. Ask what would need to change. Offer to stay in touch with a specific trigger. |
| "It's too expensive." | Reframe as cost of the problem vs. cost of the solution. Use ACV math against their risk surface. |
| "We need to involve more people." | Welcome it. Ask who and offer to help structure the next conversation. |
| "You're a young / small company." | Lead with proof — named customers, patent, specific results. Position maturity of the technology, not the company age. |
| "How is this different from [competitor]?" | Don't trash the competitor. Explain the specific capability gap your product fills that they don't. |
| "We need to think about it." | Respect it. But get specifics: "What specifically do you need to think through? Happy to provide anything that helps." |
| "Can you just send me materials?" | "Of course. Before I do — what specifically would be most useful? I want to send you the right thing, not a generic deck." |

For account-specific objections, tie the response to their specific situation, not generic talking points.

### Step 7: Plan the Meeting Flow

Structure the conversation. Every good meeting has a shape.

**Discovery call flow (~30 min):**
1. Opener (2 min) — thank them, confirm the agenda, set expectations
2. Context (3 min) — "Here's what I understand about your situation — correct me where I'm wrong"
3. Discovery (15 min) — questions, listen, probe deeper
4. Bridge (5 min) — connect their pain to your solution briefly, without a full pitch
5. Next steps (5 min) — agree on what happens next, who's involved, by when

**Demo flow (~45 min):**
1. Recap + confirm priorities (5 min) — "Last time we discussed X, Y, Z. Is that still accurate?"
2. Demo mapped to their pain (20 min) — show 2-3 scenarios, not features
3. Discussion + questions (10 min) — let them react
4. Competitive context (5 min) — only if they ask or if it's relevant
5. Next steps (5 min) — POC terms, timeline, who else to involve

**Follow-up / Proposal flow:**
1. Recap what's been discussed and agreed (5 min)
2. Address open questions from last meeting
3. Present the proposal or next phase
4. Handle objections
5. Confirm timeline and process

### Step 8: Prepare Opening and Closing Statements

**Opening statement** — earn the right to ask questions:
- Thank them for the time
- Show you've done your homework (reference something specific — a recent news item, their LinkedIn post, a company milestone)
- State the purpose of the meeting clearly
- Ask permission to structure the conversation: *"I'd love to start by understanding your current setup, then share some relevant examples. Would that work?"*

**Closing statement** — lock in the next step:
- Summarize what you heard (reflect their words back)
- Confirm mutual interest (or acknowledge if not a fit — better to know now)
- Propose a specific next step with a date: *"How about we set up a 30-min session with [colleague] next Tuesday to walk through the technical integration?"*
- If they need to think: *"Completely understand. Can I suggest we reconnect on [date]? I'll send over [specific thing] in the meantime."*

---

## Output Schema

```
# Meeting Prep: [Company Name]

**Date:** [meeting date]
**Type:** [Discovery / Demo / Follow-up / Proposal / Partnership]
**Duration:** [expected length]

## Meeting Objective
**Primary outcome:** [one sentence]
**Minimum acceptable outcome:** [one sentence]

## Attendees

### [Name 1]
- **Title:** ...
- **Role in deal:** [Economic buyer / Champion / Evaluator / Influencer / Blocker]
- **Tenure:** ...
- **Background:** [career trajectory, prior companies]
- **LinkedIn activity:** [recent relevant posts or engagement]
- **What they care about:** [top priorities for their role]
- **Likely stance:** [Excited / Neutral / Skeptical / Unknown]
- **Connection points:** [shared connections, interests, or context]

### [Name 2]
[Same structure]

## Account Context Refresh
- [Any updates since last research]
- **ICP fit:** [from qualification score]
- **Current moment:** [what's happening at the company right now]

## Prepared Questions (prioritized)
1. [Most important question]
2. ...
3. ...
4. ...
5. ...

## Value Mapping
| Their Likely Pain | Our Capability | Proof Point |
|-------------------|---------------|-------------|
| ... | ... | [Customer] achieved [result] |
| ... | ... | ... |

## Anticipated Objections
| Objection | Response |
|-----------|----------|
| ... | ... |
| ... | ... |

## Meeting Flow
1. [Phase] — [duration] — [what happens]
2. ...
3. ...

## Opening Statement
[2-3 sentences — written out, ready to use]

## Closing / Next Step Plan
[What to propose as the next step, with a fallback if they need time]

## Internal Notes
- Key risk in this meeting: ...
- What I'm most uncertain about: ...
- If the meeting goes well, the next step is: ...
- If the meeting goes poorly, the fallback is: ...
```

## Quality Checklist

- [ ] Meeting objective is specific and measurable — not "have a good conversation"
- [ ] Every attendee is profiled with role, priorities, and likely stance
- [ ] Questions are open-ended and prioritized — not a generic list
- [ ] Value propositions are mapped to their specific situation, not generic capabilities
- [ ] Objections are account-specific, not boilerplate
- [ ] Opening statement references something specific about them
- [ ] Closing statement includes a concrete next step with a date
- [ ] The meeting flow has a structure — not "we'll see how it goes"
- [ ] No fabricated facts about the attendees or the company

## Relationship to Other Skills

```
07-meeting-prep           →  prepare for any sales meeting
04-account-research       →  provides the account context (run first)
05-qualification-scoring  →  provides the fit and priority assessment
03-outreach-strategy      →  the outreach that got the meeting booked
01-icp-definition         →  provides the ICP criteria for fit assessment
```
