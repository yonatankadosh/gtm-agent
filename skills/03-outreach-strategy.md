# Skill 03: Outreach Strategy

## Purpose

Build a full outreach plan for any target account — the angle, the sequence, the message for each touch. The goal is outreach that reads like it was written by someone who actually did their homework. Always run Account Research (Skill 04) first. Outreach without account context produces generic messages that don't convert.

## Inputs

- `context/product-overview.md` (required)
- `output/icp.md` (required)
- `output/research/{company-slug}.md` (required — run Skill 04 first)
- `output/outreach-strategy.md` (optional — if a general strategy exists, use it to align messaging angles)

## Dependencies

- Skill 01: ICP Definition
- Skill 04: Account Research (for the specific account)

## Output

Write to `output/outreach/{company-slug}.md`

---

## Methodology

### Step 1: Angle Selection

Before writing a single word, lock in the angle. The angle is the one reason this person should care about hearing from you, right now, given what's happening in their world.

**A strong angle has three components:**
- **Signal:** A specific, observable thing about them (funding round, job posting, LinkedIn post, product launch, news, company growth)
- **Bridge:** Why that signal is relevant to the problem you solve
- **Stakes:** What gets better (or worse) for them if they act (or don't)

**Choose the strongest angle type:**

| Angle Type | Description | Use When |
|------------|-------------|----------|
| **Trigger-based** | A recent event creates urgency or relevance | Clear signal in the last 60 days |
| **Pain-based** | Lead with the symptom they're experiencing | No strong trigger, but pain is obvious from research |
| **Outcome-based** | Lead with a result you've achieved for a similar company | Strong proof point that maps to their situation |
| **Insight-based** | Share a non-obvious observation about their business or market | Buyer is sophisticated; generic pitches won't land |
| **Peer-based** | Reference a competitor or peer company using you | Social proof is likely to resonate with this persona |

> Choose ONE angle. Do not blend multiple angles into one message. Blending dilutes the hook.

State the chosen angle before drafting: *"The angle is: [signal] → [bridge] → [stakes]."*

### Step 2: Channel & Sequence Strategy

Select the right channel(s) and sequence structure based on persona seniority and what you know about how they engage.

**Channel selection logic:**

| Situation | Recommended Primary Channel |
|-----------|---------------------------|
| C-suite or VP, cold | LinkedIn first (connection or DM), then email |
| Director / Manager, cold | Email first, LinkedIn as follow-up |
| Already connected on LinkedIn | LinkedIn DM |
| High-priority account, no email found | LinkedIn only |
| Warm intro or prior contact | Email, reference the connection |
| Event or content trigger | Email, reference the trigger |

**Sequence structure — design as a story, not a series of pings:**

| Touch | Channel | Purpose | Timing |
|-------|---------|---------|--------|
| 1 | Primary | Lead with the angle. One ask only. | Day 1 |
| 2 | Secondary | Add a new data point or proof point. Don't repeat touch 1. | Day 4-6 |
| 3 | Primary | Shift the frame — try a different angle or a direct question. | Day 10-12 |
| 4 (optional) | Either | Short breakup message. Give them an easy out. | Day 18-21 |

**Adjust based on account tier:**
- Strategic accounts (top 10-20): Longer sequences, more touches, multi-threaded (multiple contacts)
- Mid-market: Standard 3-4 touch sequence
- High-volume: Shorter, faster, single-threaded

### Step 3: Message Construction

Write each message using this anatomy:

```
HOOK (1 sentence)
The thing that makes them keep reading.
Reference the signal, ask a provocative question, or state something
specific about them that shows you did your homework.
Don't introduce yourself here.

BRIDGE (1-2 sentences)
Connect the hook to the problem you solve.
"We work with [persona type] who are dealing with [situation]
and typically see [symptom]."

CREDIBILITY (1 sentence, optional)
One proof point. A customer name + result. Not a paragraph of credentials.

ASK (1 sentence)
One clear, low-friction ask. Not a demo request on the first touch.
"Worth a 15-min conversation?" or "Is this on your radar?"
or "Happy to share how we approached this — want me to send it over?"
```

**Length rules:**
- Cold email: 75-120 words. Subject line: 3-6 words, specific, no clickbait.
- LinkedIn DM: 50-80 words max.
- LinkedIn connection request: 1 sentence, no pitch. (~300 char limit)
- Follow-up touches: shorter than the first message, not longer.

**What to avoid:**
- Opening with "I" or your company name
- "I hope this finds you well" or any equivalent
- Listing features or product capabilities
- Multiple questions in one message
- "Just checking in" follow-ups with no new value
- Vague CTAs ("let me know if you're interested")

### Step 4: Multi-Threading Strategy

For strategic accounts, never rely on a single contact. Map at least two entry points.

- **Thread 1 — Champion:** The person who feels the pain most. Goal: get internal advocacy.
- **Thread 2 — Economic buyer:** The person who signs off. Goal: create top-down awareness so the champion isn't selling alone.
- **Thread 3 — Influencer (optional):** Ops, IT, or adjacent function. Goal: reduce friction in evaluation.

> Coordinate timing: don't hit all three simultaneously. Stagger by 5-7 days. If one thread responds, pause the others.

### Step 5: Personalization Calibration

Match effort to account tier:

| Tier | Personalization Level | What to Customize |
|------|----------------------|-------------------|
| Strategic (top 10-20 accounts) | Deep | Specific signal, relevant proof point, named stakeholders, custom research |
| Mid-market | Moderate | Industry/role-specific pain, one relevant signal |
| High-volume | Light | Persona-level relevance, no individual research |

> For high-volume outreach, personalize the first sentence only. One specific, relevant sentence outperforms a generic paragraph every time.

### Step 6: Objection Pre-emption

Anticipate the most likely reason they don't respond and address it before it becomes an objection.

| Common Failure Mode | Pre-emption Approach |
|--------------------|---------------------|
| "We already have a solution" | Focus on outcome gap, not product replacement |
| "Not a priority right now" | Urgency framing tied to their strategic moment |
| "Send me more info" | Don't. Redirect to a conversation. Info without context doesn't sell. |
| No response | Don't assume disinterest. Most non-responses are timing, not rejection. |
| "You're a young company" | Lead with proof points and named customers in similar situations |

### Step 7: Write Variation B

For each primary message, write one variation using a different angle. This gives options and enables A/B testing over time.

### Step 8: Pre-Send Checklist

Before finalizing each message:

1. **The "so what" test:** Remove the company name — is the message meaningless? If yes, it's genuinely personalized.
2. **The "reply motivation" test:** Why would this specific person reply? What's in it for them?
3. **The "cringe" test:** Would you be embarrassed to receive this? If yes, rewrite.
4. **The "forward" test:** If they forwarded this to a colleague, would it make them look smart?

---

## Output Schema

```
# Outreach Plan: [Company Name]

## Angle
Signal: [what you noticed]
Bridge: [why it's relevant to what you solve]
Stakes: [what's at risk]
Angle type: [trigger / pain / outcome / insight / peer]

## Sequence Overview
| Touch | Channel | Timing | Contact | Angle |
|-------|---------|--------|---------|-------|
| 1 | ... | Day 1 | ... | ... |
| 2 | ... | Day 5 | ... | ... |
| 3 | ... | Day 12 | ... | ... |

## Touch 1: [Channel]

### Version A
**Subject:** [if email]
[Message body — 75-120 words]

### Version B (alternate angle)
**Subject:** [if email]
[Message body]

## Touch 2: [Channel]
[Message body]

## Touch 3: [Channel]
[Message body]

## Multi-Thread Plan (if strategic account)
- Thread 1 (Champion): [name], [angle], [timing]
- Thread 2 (Economic buyer): [name], [angle], [timing — staggered 5-7 days]

## Outreach Summary
[One paragraph: who, what angle, what sequence, what ask, what risk]

## Internal Notes
- Best angle for this account: ...
- Fallback if no reply after sequence: ...
- Key talking points if they reply: ...
```

## Quality Checklist

- [ ] The hook references something specific about this person or company — not a generic opener
- [ ] Each message has exactly one ask
- [ ] Follow-up messages add new value — not a bump of the first message
- [ ] The sequence respects the buyer's time — not too many touches, not too fast
- [ ] The CTA is calibrated for cold outreach — low friction, not a 45-min demo request
- [ ] You can answer: "Why this person, why this angle, why now?"
- [ ] Email is 75-120 words. LinkedIn DM is 50-80 words. No exceptions.

## Relationship to Other Skills

```
03-outreach-strategy      →  planned outreach for any account
04-account-research       →  run this first — outreach depends on account context
05-qualification-scoring  →  confirm the account is worth the effort before building sequence
06-signal-outbound        →  reactive outreach triggered by a signal (distinct from planned)
07-meeting-prep           →  prepare for the call once it's booked
```
