# LinkedIn Skill (owned by Marketing)

## Purpose

Produce LinkedIn posts — founder voice (Yonatan / co-founders) or company voice — that earn engagement on substance, not on motivational platitudes. Each post is grounded in a specific observation: a customer pattern, a competitive move, a research finding, a recent signal in the market.

## Inputs

- `context/product-overview.md`
- `context/customers.md`
- `output/icp.md`
- The topic, voice (founder vs. company), and angle (from the user via the Orchestrator)
- On demand: `output/research/{icp}/{slug}.md`, `output/outreach-learnings.md`, `output/cs/{customer}/`, recent news (web search)

## Output

Write to `output/marketing/linkedin/{YYYY-MM-DD}-{topic-slug}.md`.

---

## Methodology

### Step 1: Confirm voice and angle

Voice options:

- **Founder voice** — first-person, opinionated, direct. "I just looked at 12 marketplaces' moderation logs. Here's what I found."
- **Company voice** — measured, informative, third-person OK. "We benchmarked 12 marketplaces against the same abuse pattern. Here's what we learned."

Angle = the one specific, concrete observation that anchors the post. Without an angle, the post becomes filler. Examples of valid angles:

- A pattern across multiple customers (anonymized)
- A specific competitive move that signals a market shift
- A finding from a recent research file
- A counter-intuitive observation from a meeting
- A reframe of conventional wisdom backed by data

If the user hasn't specified an angle, ask one question: "What's the specific observation you want to anchor this on?"

### Step 2: Draft against the LinkedIn-native shape

```
Line 1: Hook. Specific, surprising, or contrarian. ≤ 12 words.
        (Lines 2+ are hidden behind "see more" — line 1 has to earn the click.)
Line 2: Empty.
Lines 3-N: 2-4 short paragraphs, each ≤ 3 sentences. One concrete claim per paragraph.
Penultimate line: The "so what" — what the reader should think/do/share.
Final line: Question or CTA. (Open question gets more comments than statement.)
```

### Step 3: Constraints

- **≤ 1300 characters total.** (LinkedIn's no-truncation limit. Going over hides content behind "see more".)
- **No emoji unless the user explicitly asks.** (And usually they won't.)
- **No hashtag spam.** Maximum 3 hashtags, only if they're genuinely the conversation's tag.
- **No tagging people without permission.** If a tag would help, surface it to the user as a suggestion — don't write it into the draft.
- **No fabricated stats or fake customer quotes.** If you use a number, it has to come from a real source — link it or cite it.

### Step 4: Confirm and write

Show the full draft to the user. Offer:
- Save as-is
- Edit (loop)
- Discard

Only write on confirmation.

---

## Output Schema

```
# LinkedIn Post — {YYYY-MM-DD}

**Voice:** {founder / company}
**Angle:** {one sentence}
**Audience:** {who this is aimed at — ICP / persona}
**Source artifacts:** {files cited or referenced}

---

{Line 1: hook}

{Line 3-N: body, with empty lines between paragraphs}

{Penultimate: so what}

{Final: question or CTA}

---

**Char count:** {N} / 1300
**Recommended posting time:** {Tue-Thu 8-10am local based on audience}
**Suggested first comment** (own your thread): {optional 1-2 sentence first comment to seed the conversation}
```

---

## Quality Checklist

- [ ] Hook in line 1 is specific and ≤ 12 words
- [ ] One concrete observation anchors the post (not vibes, not motivational)
- [ ] Total ≤ 1300 chars
- [ ] No fabricated stats, customer quotes, or product capabilities
- [ ] Final line is a question or specific CTA
- [ ] Voice matches the requested voice (founder vs. company)
- [ ] User saw and confirmed the draft before the file was written
