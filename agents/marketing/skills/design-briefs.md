# Design Briefs Skill (owned by Marketing)

## Purpose

Produce **design-prompt-ready briefs** for visual marketing assets — vertical one-pagers, use-case slide sheets, partner-co-branded one-pagers, event one-pagers, ICP-specific solution sheets — that an external design tool (Claude with image generation, Midjourney via wrapper, Figma AI, a human designer) can execute without further context.

The deliverable is **the brief, not the rendered PDF**. The brief contains the design prompt, the cover-email blurb, the source-grounding check, and a quality checklist. The user takes the prompt out of the file, pastes it into the design tool with the reference images attached, and produces the rendered asset.

This skill exists so vertical / use-case / partner adaptations of the master one-pager stay on-brand, anti-fabricated, and properly anti-positioned (Cyvore is a platform; the vertical/use case is one application — never the other way around).

## Inputs

- `context/product-overview.md` — master positioning, the three engines (OPR / TIAO / DAN), pricing, patent line
- `context/customers.md`
- `output/icp.md`
- `output/outreach-strategy.md` (for messaging consistency — the asset should echo, not contradict, Sales)
- The asset type (one-pager, slide sheet, event one-pager, etc.), the vertical / use case / audience, and the trigger reason (cold-email attachment, event handout, partner co-sell, …)
- **Reference visual assets** — at minimum the master one-pager PDF and one prior use-case slide (screenshot or PDF). Without these, stop and ask.
- On demand: `output/research/{icp}/{slug}.md`, `output/industry-reports/*.md`, `output/cs/{customer}/`, prior `output/marketing/campaigns/*.md` (for tone reference)

## Output

Write to `output/marketing/campaigns/{slug}-{YYYY-MM-DD}.md`.

`{slug}` = the asset's distinguishing label, lowercased and hyphenated. Examples: `gaming-one-pager`, `finance-vertical-sheet`, `papaya-partner-one-pager`, `cybertech-2026-handout`.

The rendered PDF that gets produced from this brief later goes to `output/marketing/content/{slug}-{YYYY-MM-DD}.pdf` — that's not this skill's output, but record the planned path inside the brief so the loop is closed.

---

## Hard rules (the gaming one-pager taught us these — do not relax them)

These are the same rules from `output/marketing/campaigns/gaming-one-pager-2026-05-10.md`. They apply to **every** vertical / use-case / partner adaptation Marketing produces.

1. **Master positioning leads.** The master Cyvore tagline ("Proactive Security for the Modern Workspace") and the suite-level sub-paragraph ("Cyvore delivers a complete Centralized Workspace Security Platform for CISOs with full visibility across human and AI-driven collaboration.") occupy the top ~55% of the page. Anyone who web-searches Cyvore must see the same story.
2. **Three-engine block appears twice.** Once in Part 1 with **universal** descriptions ("OPR — Visual phishing detection across digital interfaces"). Once in Part 2 with **vertical-applied** descriptions ("OPR in {vertical} — catches X, Y, Z"). The engine **names stay constant**: OPR, TIAO, DAN. Their order stays constant: OPR, TIAO, DAN.
3. **The vertical is a clearly-labeled `USE CASE` section, not the headline.** Use a magenta `USE CASE` pill / badge at the top-left of Part 2, mirroring the marketplace use-case slide. The reader must feel "this is a vertical solution sheet for me," NOT "they tailored their product for me."
4. **No "{vertical}" word in the headline.** Examples of forbidden headlines: "Cyvore for Gaming," "Cyvore for Banks," "Player Safety Platform." The headline is the master tagline, period.
5. **No customer logos** unless the user explicitly approves a real, public, named customer reference. Cyvore has very few public customer references; assume none for a vertical adaptation unless told otherwise.
6. **No invented stats.** Every number that appears on the page is either (a) one of the four master pain stats from the existing one-pager (`2,535%`, `15B`, `967%`, `83%`, `65%`) or (b) a stat with an inline-quotable source from a research file. The brief must include a **source-grounding table** that quotes the exact source phrase for every Part 2 stat.
7. **Closing tagline = master one-pager closing tagline.** Suite-level. ("Enabling secure collaboration across every conversation, connection and interaction in the modern workspace.") Do not write a vertical-specific closing line.
8. **No "Request a demo" CTA box.** The master one-pager has none — keep visual consistency.
9. **Patent line preserved verbatim.** "Granted U.S. Patent — Workspace Cyber Protection Platform and Methods Thereof."
10. **Footer preserved verbatim.** `info@cyvore.com   cyvore.com   LinkedIn   YouTube`
11. **Visual style preserved verbatim.** Lavender background (~#EFE9FF), deep purple ink, magenta-purple dust-splash motif top-right, geometric sans typography, oversized stat numbers in deep purple. Do not introduce a new accent color "for this vertical."
12. **No literal/casual industry iconography.** Examples of forbidden: game controllers, dollar bills, stethoscopes, shopping carts. The audience is CISO-level. Subtle motifs only — chat-bubble glyphs, faint node-and-edges line motifs, abstract geometric shapes.

If the user pushes back on any of these, surface the trade-off explicitly and ask before relaxing.

---

## Methodology

### Step 1: Lock the brief

In plain text, lock six things before reading anything:

1. **Asset type** — vertical one-pager, use-case slide sheet, partner co-branded one-pager, event handout, ICP-specific solution sheet
2. **Audience** — exact persona (e.g., "CISO at mobile / social gaming studios," "Head of T&S at marketplaces > 500 employees," "VP Security at Israeli banks")
3. **Vertical / use case angle** — the one specific lens through which the master platform is presented
4. **Distribution channel** — cold-email attachment, event handout, in-meeting collateral, partner co-sell
5. **Job to be done** — what the recipient does after reading (book a 20-min coffee, request a POC, share with the security team)
6. **Reference visual assets** — exact filesystem paths to the master one-pager and at least one prior use-case slide

If any of the six is missing, stop and ask the user. Do not proceed on assumption.

### Step 2: Source-grounding pass (before writing any copy)

Identify every stat / fact that will appear in Part 2. For each one, locate the exact source phrase in `context/`, `output/research/`, `output/industry-reports/`, or a public source. Build a source-grounding table:

| Stat / claim | Source file | Quoted phrase |
|---|---|---|
| {stat} | `output/research/{icp}/{slug}.md` | *"…"* |

If a stat cannot be grounded, **cut it**. Do not paraphrase a number into existence. The four master pain stats from the existing one-pager (`2,535%`, `15B`, `967%`, `83%`, `65%`) are pre-grounded and may always be reused for Part 1.

### Step 3: Lock the page architecture

The architecture is fixed across all vertical / use-case adaptations:

```
═══════════════════════════════════════════════════
PART 1 — CYVORE THE PLATFORM (top ~55% of page)
═══════════════════════════════════════════════════
Wordmark "cyvore™" (top-left)
Master headline (the existing one-pager headline, verbatim)
Master sub-paragraph (verbatim)
Two-block intro (verbatim from master)
"The Pain" + 4-stat strip (verbatim from master)
"AI-First Workspace Security" + 3-engine block (UNIVERSAL descriptions)

═══════════════════════════════════════════════════
PART 2 — VERTICAL USE CASE (bottom ~40% of page)
═══════════════════════════════════════════════════
[Magenta "USE CASE" pill / badge]
Vertical section title (e.g. "Player Safety in Mobile & Social Gaming")
Use-case framing paragraph (anchors the application; embeds 1–3 grounded stats)
Three-engine block REPEATED, this time with VERTICAL-APPLIED descriptions
Optional small horizontal use-case strip (4 short labels)

═══════════════════════════════════════════════════
PART 3 — CLOSING + FOOTER
═══════════════════════════════════════════════════
Master closing tagline (verbatim)
Patent line + footer (verbatim)
```

If the asset is a slide-sheet variant rather than a one-pager (e.g., a single use-case slide like the marketplace reference), Part 1 may be compressed to a header bar with wordmark + master tagline only, and Part 2 expands to fill the rest. The master positioning still appears.

### Step 4: Draft the design prompt

The design prompt is the actual artifact that will be pasted into the design tool. It must be **self-contained** — the design tool has no access to research files, the GTM agent, or this brief.

Required sections of the prompt itself, in order:

1. Role + goal + reference-image instruction (tells the design tool to use the two attached reference images)
2. **CRITICAL POSITIONING RULE** — paraphrase Hard Rule #1, #2, #3, #4 from above so the design tool sees them
3. Output format spec (A4 portrait, production resolution)
4. Visual style spec (palette, typography, accent motifs — all from the master)
5. Page layout block — Part 1 / Part 2 / Part 3 with **all copy verbatim**, no `[fill in]` placeholders. Use box-drawing dividers (`═══`) so the layout is visually obvious in the prompt itself.
6. Iconography guidance (subtle, no literal industry props)
7. **WHAT NOT TO DO** — bullet list repeating Hard Rules #5–#12 in the prompt's own voice so the design model is constrained by the prompt, not just by the human reviewer
8. Iteration guidance — what feedback to expect on round 2

Wrap the entire design prompt in **quad-backticks** (`` ```` ``) inside the brief file so any inner triple-backticks render correctly.

### Step 5: Draft the cover-email blurb

A 50–80 word blurb the user pastes into the email body when sending the rendered PDF. Voice is the user's (founder voice, first-person, plain language). Must reinforce:

- "We are a platform" (not "we are a {vertical} product")
- "Here's how it applies to your industry" (not "we built this for you")
- One specific call-to-action ("20-minute conversation" / "POC scoped to one game" / "book the slot we held for Cybertech")

Keep the blurb in a separate quad-backtick block in the brief so the user can copy it independently of the design prompt.

### Step 6: Draft the quality checklist

The brief includes an **asset-specific quality checklist** the user runs against the rendered PDF before it goes external. The 10–12 items below are the baseline; add asset-specific items as needed.

- [ ] Headline is the master Cyvore tagline (verbatim).
- [ ] Master sub-paragraph + Part 1 stats + Part 1 engine block match the reference one-pager copy.
- [ ] Part 2 is clearly labeled with a `USE CASE` badge or section heading.
- [ ] Part 2 occupies less than 50% of the page (Part 1 leads visually).
- [ ] All Part-2 stats are present, unmodified, and traceable to the source-grounding table.
- [ ] Three engines appear twice (Part 1 universal, Part 2 vertical-applied) with the same names and the same order.
- [ ] No customer logos.
- [ ] No "Request a demo" CTA box.
- [ ] Closing tagline = master one-pager closing line, suite-level (not vertical-specific).
- [ ] Footer matches reference exactly (patent + email + URL + LinkedIn + YouTube).
- [ ] No literal/casual industry iconography.
- [ ] Visual palette matches reference exactly.

### Step 7: Confirm and write

Show the full brief draft (source-grounding table + design prompt + cover-email blurb + checklist) to the user in chat. Offer:

- Save as-is to `output/marketing/campaigns/{slug}-{YYYY-MM-DD}.md`
- Edit specific sections (loop)
- Discard

Only write the file on explicit user confirmation. After writing, run `bash tools/ops/sync-to-gcp.sh` per workspace rules.

---

## Output Schema

```
# Campaign Brief — {Asset name}

**Date:** {YYYY-MM-DD}
**Owner:** Marketing
**Asset type:** {vertical one-pager / use-case slide sheet / partner co-branded one-pager / event handout / ICP-specific solution sheet}
**Audience:** {persona}
**Vertical / use case:** {gaming / finance / marketplace / …}
**Channel:** {cold-email attachment / event handout / partner co-sell / in-meeting collateral}
**Success metric:** {≥N first-meeting acceptances within {timeframe} / N leads / event KPI}
**Reference visuals:** {filesystem paths to master one-pager + use-case slide}
**Rendered PDF will land at:** `output/marketing/content/{slug}-{YYYY-MM-DD}.pdf`

---

## Source grounding (anti-fabrication check)

| Stat / claim | Source file | Quoted phrase |
|---|---|---|
| … | … | *"…"* |

Master pain stats (`2,535%`, `15B`, `967%`, `83%`, `65%`) are pre-grounded from the existing master one-pager — no new research needed.

---

## Usage instructions

When pasting the design prompt below into your design tool:

1. Attach both reference images alongside the prompt:
   - Master one-pager: {path}
   - Use-case slide reference: {path}
2. Run a first generation. Expect 1 round of feedback on density, divider styling, and {vertical}-iconography weight.
3. Once approved, save the rendered PDF to `output/marketing/content/{slug}-{YYYY-MM-DD}.pdf` and use the cover-email blurb below when sending.

---

## The design prompt (copy-paste ready)

````
{the full design prompt — Part 1 + Part 2 + Part 3 with verbatim copy, visual style spec, WHAT NOT TO DO, iteration guidance}
````

---

## Cover-email blurb (~60 words, founder voice)

````
{the blurb}
````

---

## Quality checklist (run before sending the rendered PDF externally)

- [ ] {12 baseline items + asset-specific items}

---

*This brief is the deliverable. The rendered PDF (after running the prompt through a design model) goes to: `output/marketing/content/{slug}-{YYYY-MM-DD}.pdf` once produced.*
```

---

## Quality Checklist (for the brief itself, not the rendered PDF)

- [ ] All six brief-locking inputs (asset type, audience, vertical, channel, JTBD, references) are explicit in the file header.
- [ ] Source-grounding table is present and every Part-2 stat has an inline source quote.
- [ ] Design prompt is fully self-contained — no `{fill in}`, no references to files the design tool can't see.
- [ ] Hard Rules #1–#12 are reflected both in the brief's "Hard rules" reminder AND in the design prompt's "WHAT NOT TO DO" block.
- [ ] Three-engine block appears twice in the design prompt — Part 1 universal, Part 2 vertical-applied — with the same names in the same order (OPR, TIAO, DAN).
- [ ] Master tagline is in the headline; "{vertical}" word is NOT in the headline.
- [ ] Closing tagline is the master one-pager's closing line, verbatim.
- [ ] Cover-email blurb is in the user's voice and reinforces the platform-first framing ("we have a platform; here's the vertical lens").
- [ ] Quality checklist for the rendered PDF is asset-specific, not generic.
- [ ] `output/marketing/content/{slug}-{YYYY-MM-DD}.pdf` is named in the brief so the loop closes.
- [ ] User saw and confirmed the draft before the file was written.

---

## Trigger phrases (for the Orchestrator)

Route to Marketing → design-briefs skill on:

- "Create a one-pager for {vertical / use case}"
- "Make a design brief / design prompt for {asset}"
- "I need a {vertical} solution sheet"
- "Adapt the one-pager for {industry / partner / event}"
- "Build a use-case slide for {use case}"
- "Vertical handout for {Cybertech / RSA / event}"
- "{Partner name} co-branded one-pager"

If the request is for **the rendered PDF itself** (rather than the brief), this skill produces the brief and the user generates the PDF externally; record the planned PDF path so when the rendered file lands in `output/marketing/content/`, the artifact pair stays linked.

---

## Worked example

The first asset produced under this skill is `output/marketing/campaigns/gaming-one-pager-2026-05-10.md`. Read it as the canonical reference. Future briefs should match its shape, discipline, and tone — only the vertical / use-case lens, the source-grounding table, and the Part-2 copy change.
