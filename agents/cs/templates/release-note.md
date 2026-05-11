---
title: <H1 of the release — e.g. "Reliability & Accuracy Update">
subtitle: <One sentence under the title — what changed, in plain language>
---

## TL;DR

- <Plain-language one-liner per change — what the customer sees, not what we shipped>
- <One bullet per changelog item below; same wording the customer would describe it in>
- <Keep to 3–5 bullets total>
- <No commercial fluff ("we're excited to..."); just the change>

## Changelog

### [improvement] <Item title — customer-facing, not internal>

<2–4 sentences. What changed, why it matters to the customer, what they will now see. No internal jargon. No fabricated metrics — if you don't have a number, say "consistently" / "reliably" / "across all X" instead of inventing one.>

### [bug fix] <Item title>

<Same body rules.>

### [new feature] <Item title>

<Same body rules.>

### [security] <Item title>

<Same body rules.>

### [breaking change] <Item title>

<Same body rules — and call out the action the customer needs to take, if any.>

## Closing

<One sentence. Default: "If you have any questions about these changes or their impact on your environment, we're happy to walk you through them." Override only if the release warrants something specific (e.g., scheduled maintenance window, customer action required).>

---

## Authoring notes (NOT part of the rendered email — strip before commit)

**Allowed tags** (each maps to a colored badge in the rendered email):

- `improvement` — blue (incremental upgrade to existing capability)
- `bug fix` — green (something that was broken is now fixed)
- `new feature` — purple (genuinely new capability)
- `security` — amber (security-relevant change customers should know about)
- `breaking change` — red (customer action required, deprecation, contract impact)

**Tag rules**:

- One tag per item. Choose the most-customer-relevant tag if multiple apply.
- Order items in the changelog by importance to the customer — the first item is the one a busy customer should read if they read nothing else.
- The TL;DR bullets are 1:1 with the changelog items, in the same order.

**What this template does NOT include** (by design):

- No greeting line ("Hi X,") — release notes go out to multiple customers, no personalization.
- No marketing language ("We're thrilled to..."). Customers see plain, factual change descriptions.
- No fabricated benchmarks or metrics. If you don't have a real number, leave it qualitative.
- No internal product names or internal Jira tags — translate to customer-facing language.

**Rendered by**: `tools/send-release-note.py`. The script reads the YAML frontmatter (`title`, `subtitle`) and the three sections (`TL;DR`, `Changelog`, `Closing`) and renders into the locked Cyvore email-safe HTML template with the Cyvore mark embedded as a CID inline image.

**Output filename**: `output/cs/release-notes/{YYYY-MM-DD}-{slug}.md` (and `.html` sibling once rendered).
