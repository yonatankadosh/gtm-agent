# GTM Agent

A structured skill system that turns Cursor + Claude into a repeatable GTM (Go-To-Market) machine. No code, no APIs, no subscriptions — just methodology files that guide an AI agent to execute disciplined GTM motions.

Built for solo GTM operators and small teams who need pipeline without an army of SDRs.

## How It Works

The project has **8 skills** organized into **two engines**. Each skill is a detailed methodology file — not a loose prompt, but a structured framework with steps, scoring models, output schemas, and quality checklists.

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
| **08 — Inbound Qualification** | Full research + qualification of an unknown account — ICP classification, full Skill 04 research, score, and route (Tier 1 / Tier 2 / Pass). Entry point for anything not already in `target-accounts.md`. |

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
  agents/                               # The agent layer
    orchestrator.md                     # Routing & composition contract
    research-bizdev/
      AGENT.md
      skills/                           # Owned primitives (inherited + extensions)
        01-icp-definition.md
        02-prospecting.md
        04-account-research.md
        05-qualification-scoring.md
        08-inbound-qualification.md
    sales/
      AGENT.md
      skills/
        03-outreach-strategy.md
        06-signal-outbound.md
        pipeline-maintenance.md
        hubspot-quick-update.md
        hubspot-status-sync.md
    chief-of-staff/
      AGENT.md
      skills/
        07-meeting-prep.md
        exec-comms.md
        weekly-context.md
      templates/                        # Reusable comms templates
    marketing/, cs/, partnerships/      # Each with AGENT.md + skills/
  state/                                # Persistent qualitative memory (gitignored)
    weekly-context.md
    okrs.md
  output/                               # Generated results (gitignored)
    research/{icp}/{slug}.md            # Per-account research
    outreach/{icp}/{slug}.md            # Per-account outreach drafts
    meeting-prep/{slug}-{date}.md       # Pre-meeting briefs
    pipeline/{YYYY-WW}/                 # Per-week pipeline subfolder
      snapshot.md                       # pipeline-maintenance output
      sync-log.md                       # HubSpot writes audit log
      merge-plan.json / merge-report.md # hubspot-status-sync outputs
    exec-comms/{audience}/{date}.md     # Digests, board, investor, all-hands
    exec-comms/weekly-tasks/{week}/     # Per-assignee task files
    marketing/, partnerships/, cs/      # Per-agent artifacts
    industry-reports/                   # Vertical market reports (Marketing reads)
  tools/                                # Subfoldered by integration
    apollo/   email/   hubspot/   sheets/   telegram/   ops/   assets/
  .cursor/
    rules/gtm-agent.mdc                 # Cursor rule — auto-loaded
    mcp.json                            # HubSpot MCP config (gitignored)
```

The system has two layers. The **primitives** are the methodology files described in the tables above (Skills 01–08) — these are the GTM motions, owned by the relevant agent and read by reference. The **agent layer** sits on top: a single Orchestrator routes user intents to specialized agents (Research & BizDev, Sales, Chief of Staff, Marketing, CS, Partnerships), each of which inherits its primitives and adds its own extensions (e.g. Sales adds `pipeline-maintenance`, Chief of Staff adds `exec-comms` and `weekly-context`). See [agents/orchestrator.md](agents/orchestrator.md) for the full routing table.

## Requirements

- [Cursor](https://cursor.com) IDE with Claude enabled
- No API keys needed
- No dependencies, no installs, no infrastructure

## Inspired By

The two-engine framework (Targeting + Activation) is inspired by the [Swan AI](https://www.linkedin.com/company/swan-ai/) approach to GTM methodology — giving AI agents structured skills instead of loose prompts.

## License

MIT — use it, fork it, make it yours.
