# GTM Agent

A structured skill system that turns Cursor + Claude into a repeatable GTM (Go-To-Market) machine. No code, no APIs, no subscriptions — just methodology files that guide an AI agent to execute disciplined GTM motions.

Built for solo GTM operators and small teams who need pipeline without an army of SDRs.

## How It Works

The project has **7 skills** organized into **two engines**. Each skill is a detailed methodology file — not a loose prompt, but a structured framework with steps, scoring models, output schemas, and quality checklists.

You provide your product context and customer data. The agent executes skills on demand, producing structured output you can act on immediately.

### Account Targeting Engine
*Run once, refine periodically. Defines who to go after and how.*

| Skill | What It Does |
|-------|-------------|
| **01 — ICP Definition** | Builds your Ideal Customer Profile from actual customer data. Tiers customers, finds patterns, defines buying triggers, maps the buying committee. |
| **02 — Prospecting** | Finds and prioritizes net-new accounts matching the ICP. Web research, qualification scoring, lookalike expansion. |
| **03 — Outreach Strategy** | Builds personalized outreach sequences with angles, message anatomy, multi-threading, and A/B variations. |

### Account Activation Engine
*Run per account or batch. Turns targets into conversations.*

| Skill | What It Does |
|-------|-------------|
| **04 — Account Research** | Deep commercial picture of a specific company — who they are, what's happening, how they fit, who to talk to, and what angle to use. |
| **05 — Qualification & Scoring** | Scores accounts on Fit, Timing, Access, and Intent (1–3 per dimension, 12-point scale) with a clear next action. |
| **06 — Signal-Based Outbound** | Reactive outreach triggered by a buying signal — classified by urgency tier with timing SLAs. |
| **07 — Meeting Prep** | Pre-meeting brief with attendee profiles, prepared questions, objection anticipation, and a structured meeting flow. |

## Getting Started

### 1. Open in Cursor

Clone or download this repo and open it in [Cursor](https://cursor.com). The `.cursor/rules/gtm-agent.mdc` file automatically teaches the agent about the project structure and how skills work.

### 2. Add Your Context

Copy the template files and fill them in with your product and customer data:

```bash
cp context/product-overview.template.md context/product-overview.md
cp context/customers.template.md context/customers.md
```

Open each file and fill in the sections. Be specific — the more context you give, the better the agent performs. Even 2-3 customers are enough to start.

### 3. Run Skills

Tell the agent which skill to run:

- *"Run ICP Definition"* — start here, everything depends on it
- *"Run Prospecting"* — find target accounts
- *"Research [company name]"* — deep-dive on a specific account
- *"Score [company name]"* — qualify and prioritize
- *"Build outreach for [company name]"* — draft a personalized sequence
- *"Prep me for a meeting with [company name]"* — pre-meeting brief

The agent reads the skill file, pulls your context, does web research, and writes structured output to the `output/` folder.

### 4. Iterate

Skills are designed to be rerun. Refine your ICP as you learn. Update prospecting lists weekly. Research new accounts as they surface. The output accumulates over time — your GTM gets sharper with every cycle.

## Project Structure

```
GTM-agent/
  context/                              # Your product context (gitignored)
    product-overview.template.md        # Template — copy to .md and fill in
    customers.template.md               # Template — copy to .md and fill in
  skills/                               # Methodology files (the engine)
    01-icp-definition.md
    02-prospecting.md
    03-outreach-strategy.md
    04-account-research.md
    05-qualification-scoring.md
    06-signal-outbound.md
    07-meeting-prep.md
  output/                               # Generated results (gitignored)
    research/                           # Per-account research
    outreach/                           # Per-account outreach drafts
    meeting-prep/                       # Pre-meeting briefs
  .cursor/rules/
    gtm-agent.mdc                       # Cursor rule — auto-loaded
```

## Requirements

- [Cursor](https://cursor.com) IDE with Claude enabled
- No API keys needed
- No dependencies, no installs, no infrastructure

## Inspired By

The two-engine framework (Targeting + Activation) is inspired by the [Swan AI](https://www.linkedin.com/company/swan-ai/) approach to GTM methodology — giving AI agents structured skills instead of loose prompts.

## License

MIT — use it, fork it, make it yours.
