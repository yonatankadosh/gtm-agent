# Skill 06: Signal-Based Outbound

## Purpose

Turn a buying signal into a personalized, timed outreach sequence. This skill handles reactive, signal-driven outbound where timing is the competitive advantage. Distinct from Outreach Strategy (Skill 03), which handles planned outreach — this skill fires when a specific signal creates a window.

## Inputs

- `context/product-overview.md` (required)
- `output/icp.md` (required)
- `output/outreach-strategy.md` (helpful — for messaging alignment)
- **The signal** — what was detected and when, provided by the user

## Dependencies

- Skill 01: ICP Definition

## Output

Write to `output/outreach/{company-slug}.md`

---

## Methodology

### Step 1: Classify the Signal

Before doing anything, identify signal type and tier. Signal tier determines urgency, research depth, and effort.

**Tier 1 — High-intent (act within 24 hours):**
- Website visit to pricing, product, or demo pages
- Inbound form fill or demo request
- Direct reply to any prior outreach
- Review site activity (G2, Capterra, etc.)
- Re-engagement from a previously cold or lost account
- Security incident or breach made public

**Tier 2 — Moderate-intent (act within 72 hours):**
- Job change — a known contact or ICP persona joined a new company
- New relevant hire at a target company (e.g., new CISO or VP Security)
- Funding round announced
- Company expansion into a new market or geography
- Former champion or customer moved to a new company

**Tier 3 — Weak-intent (act within 1 week, lower priority):**
- LinkedIn content engagement (likes, comments on relevant posts)
- News mention without clear buying signal
- Technology install or removal detected
- Hiring volume increase in a relevant department
- Conference or event attendance

> If the signal type is unclear, default to Tier 2 handling.

### Step 2: Research Before Writing

Never write outreach before researching. The research determines whether to reach out at all.

**For the company:**
- What do they do, how big are they, what's their current moment?
- Does this company fit the ICP? If not, stop.
- Is there an existing relationship (current customer, past deal, prior outreach)?

**For the signal:**
- What specifically happened? Get the details — not just "they got funding" but the amount, stage, stated use of funds.
- How recent is it? Signals older than 30 days lose relevance fast.
- Is there a clear connection between this signal and what you sell?

**For the contact:**
- Who is the right person to reach out to given this signal? (Not always the person who triggered it.)
- What is their role, seniority, likely priorities?
- Shared context — mutual connections, past interaction, content they've published?

> If you cannot establish a clear connection between the signal and a specific pain or priority, do not reach out. A weak hook is worse than no outreach.

### Step 3: Determine the Angle

The signal is the reason you're reaching out. The angle is the insight or value you bring. These are different things.

**Map signal type to angle:**

| Signal | Angle |
|--------|-------|
| Funding | They have budget and a mandate to move fast. Connect your solution to what they said they'd do with the money. |
| New hire (CISO, VP Security) | The new hire has a fresh mandate. Position yourself as a tool that helps them succeed in their new role early. |
| Hiring spree in security/IT | They're scaling something. Identify the friction that comes with scale and address it. |
| Website visit | They already know you exist. Remove friction, don't re-introduce yourself. Reference the specific area they looked at. |
| Job change (contact moved) | Congratulate without being hollow. Reference what you achieved together or what you know about their situation. |
| Security incident / breach | They're in pain right now. Be helpful, not vulture-like. Lead with empathy and a specific capability. |
| LinkedIn engagement | They're thinking about this topic. Extend the conversation they started. |
| Conference attendance | Shared experience. Reference the event, a specific talk, or a shared takeaway. |

**Angle quality test** — finish this sentence honestly:

> *"I'm reaching out because [signal], which tells me you might be dealing with [specific problem], and we help with that specifically by [specific capability]."*

If the sentence feels forced or vague, rethink the angle or don't reach out.

### Step 4: Write the Outreach

**Principles (channel-agnostic):**
- Lead with the signal, not with yourself
- One idea per message. No feature lists, no company overviews
- Make the ask small and specific (a reply, a quick call — not "let me know if you want to chat")
- Subject lines: specific, not clever. Reflect the actual content.
- LinkedIn messages: 50-80 words max, 3-5 sentences
- Email: 75-120 words max
- Sequence length: 2-3 touches max per signal. If they don't respond, the signal wasn't strong enough — find a new one.

**Message structure:**

```
Signal hook — what you noticed and why it matters (1 sentence)

Connection — why that's relevant to what you do (1-2 sentences)

Specific ask — one clear, low-friction next step (1 sentence)
```

**Personalization check before sending:**
- Does this message work if you remove the company name and contact name? If yes, it's not personalized enough.
- Would the recipient feel like you did your homework? If not, do more research or don't send.

### Step 5: Sequence Logic

**Single-signal, single contact:**

| Touch | Purpose | Timing |
|-------|---------|--------|
| Touch 1 | Signal-driven message | Day 0-1 |
| Touch 2 | Value-add follow-up — share something relevant (article, insight, case study). Don't just bump. | Day 5-7 |
| Touch 3 | Break-up or pivot — acknowledge they're busy, offer a different framing or ask if it's not a priority. | Day 12-14 |

**Multi-signal or high-priority account:**
- If multiple signals fire on the same account within 30 days, treat as high-priority and consider multi-threaded outreach (different contacts, different angles)
- Do not send the same message to multiple contacts at the same company

**After 3 touches with no response:**
- Stop. Archive the sequence.
- Set a reminder to revisit if a new signal fires.
- Do not add them to generic nurture without a fresh reason.

### Step 6: Log and Learn

After outreach is sent, record:
- Which signal triggered it
- What angle was used
- Channel and sequence used
- Outcome (reply, meeting, no response, unsubscribe)

Over time, this data reveals which signals convert for your ICP and which are noise. Prune signals that consistently produce no replies after 20+ attempts.

Store learnings in `output/outreach-learnings.md` (create if it doesn't exist).

---

## Output Schema

```
# Signal Outreach: [Company Name]

**Signal:** [what happened]
**Signal tier:** [1 / 2 / 3]
**Detected:** [date]
**Act by:** [deadline based on tier]

## Research Summary
- **Company:** [1-2 sentences]
- **ICP fit:** [Strong / Partial / Weak]
- **Signal detail:** [specific facts — amount, date, stated plans]
- **Connection to our product:** [why this signal is relevant to what we sell]

## Target Contact
- **Name:** ...
- **Title:** ...
- **Why them:** [why this person given this signal]
- **LinkedIn:** ...

## Angle
Signal → Bridge → Stakes:
[One sentence mapping]

## Outreach Sequence

### Touch 1 — Day 0 [Channel]
**Subject:** [if email]
[Message — 75-120 words]

### Touch 2 — Day 5 [Channel]
[Message — value-add, not a bump]

### Touch 3 — Day 12 [Channel]
[Message — break-up or pivot]

## Log
- Signal type: ...
- Angle used: ...
- Channel: ...
- Outcome: [fill in after sending]
```

## Quick Reference — Signal-to-Action Cheatsheet

| Signal | Tier | Angle | Channel | Act By |
|--------|------|-------|---------|--------|
| Pricing page visit | 1 | Remove friction, they know you | Email or DM | Same day |
| Demo request / inbound | 1 | Direct — they came to you | Email | Within 1 hour |
| Security incident | 1 | Empathy + specific capability | Email | Within 24h |
| Funding announced | 2 | Connect to stated use of funds | Email | Within 48h |
| New CISO/security hire | 2 | Help the new hire win early | LinkedIn first | Within 72h |
| Contact changed jobs | 2 | Build on prior relationship | LinkedIn + Email | Within 48h |
| Hiring surge (security/IT) | 3 | Scale-related pain | Email | Within 1 week |
| LinkedIn content engagement | 3 | Extend their conversation | LinkedIn | Within 1 week |
| Conference attendance | 3 | Shared experience | LinkedIn or Email | Within 1 week |

## Quality Checklist

- [ ] Signal is recent (< 30 days) and verified
- [ ] Clear connection between signal and what you sell — not forced
- [ ] ICP fit confirmed before writing any outreach
- [ ] Message leads with the signal, not with you
- [ ] Each touch has exactly one ask
- [ ] Max 3 touches per signal — then archive
- [ ] Personalization check passed: remove names, message breaks
- [ ] Outcome logged for calibration

## Relationship to Other Skills

```
06-signal-outbound        →  reactive outreach triggered by a signal
03-outreach-strategy      →  planned outreach campaigns (not signal-triggered)
04-account-research       →  deeper research if signal comes from a high-priority account
05-qualification-scoring  →  confirm the account is worth acting on
```
