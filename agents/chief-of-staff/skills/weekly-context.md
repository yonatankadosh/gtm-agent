# Weekly Context Interview (owned by Chief of Staff)

## Purpose

Capture the qualitative state of the business each week — wins, losses, hires, product changes, and anything noteworthy that lives outside HubSpot — by interviewing the user with a fixed set of 5 questions. The output feeds the Exec Comms skill (digests, board updates, investor letters, all-hands), also owned by Chief of Staff.

## Inputs

- The user's answers in chat (no file inputs required)
- Existing `state/weekly-context.md` (to prepend new entry, preserving history)

## Output

Update `state/weekly-context.md`. New entries are prepended (most recent on top) with a date stamp.

---

## Methodology

### Step 1: Greet and confirm scope

One short message: "Quick weekly check-in — 5 questions, ~2 minutes. The answers feed your weekly digest, board prep, and any other comms we generate this week. Ready?"

If the user says no or wants to skip, abort gracefully — do NOT write to `state/weekly-context.md`.

### Step 2: Ask the 5 questions (one at a time)

Ask each question in a separate message. Wait for the answer before moving on. Keep the tone friendly but tight.

1. **Win:** "What's one win this week — deal moved, meeting booked, partnership signed, customer expansion, anything that should be celebrated or amplified?"
2. **Loss / stall:** "What's one loss or stall to flag — deal lost, deal stalled, hire didn't close, vendor issue, missed deadline?"
3. **People:** "Any hires, departures, role changes, or org shifts this week?"
4. **Product / pricing / positioning:** "Any product, pricing, or positioning change worth noting — even a small one?"
5. **Flag for leadership:** "Anything you want raised to the board, investors, or team that's NOT in HubSpot — concerns, asks, decisions you want input on?"

If the user answers "nothing" or "skip" to a question, log it as `(none)` and move on.

### Step 3: Confirm before writing

Show the user a clean summary of all 5 answers and ask: "Save this to `state/weekly-context.md`?" Only write on confirmation.

### Step 4: Write to file

Prepend the new entry to `state/weekly-context.md` using the schema below. If the file doesn't exist, create it with the schema header.

---

## Output Schema

```
# Weekly Context Log

Most recent entry on top. Each block is one week's qualitative state.

---

## Week of {YYYY-MM-DD}  <!-- Monday of the ISO week the interview covers, NOT the day it was run. Example: an interview run on Friday May 1 about the week of Apr 27–May 3 → "Week of 2026-04-27". -->

**Win:** {answer}

**Loss / stall:** {answer}

**People:** {answer}

**Product / pricing / positioning:** {answer}

**Flag for leadership:** {answer}

---

## Week of {prior Monday's YYYY-MM-DD}
...
```

---

## Quality Checklist

- [ ] All 5 answers are present (use `(none)` for skipped questions)
- [ ] User explicitly confirmed before writing to file
- [ ] New entry was **prepended**, not appended (preserves recent-on-top ordering)
- [ ] No prior weeks were modified or deleted
- [ ] Date stamp uses ISO format `YYYY-MM-DD`

## Relationship to Other Skills

```
agents/chief-of-staff/skills/weekly-context (this skill) →  captures qualitative state once per week
agents/chief-of-staff/skills/exec-comms                  →  reads state/weekly-context.md to write digests / board updates
agents/orchestrator                                      →  invokes this skill at the start of a "run weekly" flow
```

## When to Run

- **Manually:** at the start of every Monday (or whatever your weekly cadence is) by saying "weekly context" or "run weekly check-in"
- **Automatically:** orchestrator runs this first whenever you say "run weekly" before generating the digest
