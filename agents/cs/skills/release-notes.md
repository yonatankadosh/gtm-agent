# Release Notes (owned by Customer Success)

## Purpose

Compose a customer-facing release-note email from free-text changelog items, get it approved by Yonatan, and publish it to a recipient list — one email per recipient, each with the Cyvore team on CC so internal threads stay aligned. The visual template is locked (the Cyvore-branded HTML the user signed off on); the content varies per release.

This is a **post-sale customer comms** skill. It is not marketing copy, not a blog post, not a sales pitch — it is the change-log we send so existing customers know what shipped to their environment.

## Inputs

Provided by the user in chat:

- **Free-text changelog items** — each item should map to one of the allowed tags (`improvement`, `bug fix`, `new feature`, `security`, `breaking change`). Items can be rough; the skill rewrites them into customer-facing language.
- **Headline / theme** — a short phrase describing the release (e.g. "Reliability & Accuracy Update"). Becomes the H1 + subject derivation.
- **Recipient list** — given only AFTER approval, as a comma-separated list of customer emails.

Constants the skill does NOT ask for:

- **Approver:** always `yonatank@cyvore.com`. Hardcoded in `tools/email/send-release-note.py`.
- **Cyvore-team CC list (default):** `ellar@cyvore.com, peterv@cyvore.com, yoav@cyvore.com, yiftach@cyvore.com`. Hardcoded as `DEFAULT_CYVORE_TEAM_CC` in the script; overridable via `--cc` at publish time if the user explicitly asks.
- **Template:** `agents/cs/templates/release-note.md` (markdown source schema). The rendered HTML is produced by `tools/email/send-release-note.py` using a locked email-safe template — do not modify the template per release.

## Output

- Markdown source: `output/cs/release-notes/{YYYY-MM-DD}-{slug}.md`
- Rendered HTML sibling: `output/cs/release-notes/{YYYY-MM-DD}-{slug}.html` (written automatically by the script)

`{slug}` = headline kebab-cased and lowercased (e.g. "Reliability & Accuracy Update" → `reliability-accuracy`). Keep it short — two or three words.

## Anti-fabrication rules (inherited verbatim)

- **No fabricated metrics.** If you don't have a real benchmark, write the change qualitatively ("consistently", "across all chat investigations") instead of inventing a percentage.
- **No internal product names or Jira tags** in customer-facing copy — translate to the language the customer uses.
- **No marketing fluff.** Customers reading release notes want change descriptions, not "we're thrilled to announce".

---

## Methodology

### Step 1: Collect the inputs in chat

Ask the user for:

1. The **headline / theme** for this release (one line).
2. The **free-text changelog items** — one per change. For each, the user gives you the gist; you assign the tag and rewrite it.

If the user has not specified tags, propose them; confirm with the user before writing.

### Step 2: Draft the markdown source

Write to `output/cs/release-notes/{YYYY-MM-DD}-{slug}.md` using the schema from `agents/cs/templates/release-note.md`:

```
---
title: <headline>
subtitle: <one sentence under the title>
---

## TL;DR
- <1:1 with the changelog items, in the same order>

## Changelog
### [tag] <item title>
<2–4 sentence body>

(repeat per item)

## Closing
<one sentence, default copy unless the release warrants something specific>
```

Rules:

- The TL;DR bullets are 1:1 with the changelog items, in the same order.
- Order items by importance to the customer — the most material change first.
- Tag must be one of: `improvement`, `bug fix`, `new feature`, `security`, `breaking change`.
- Subject line will be auto-derived as `Cyvore - Platform Release: {title}` — do not include "subject" in the source.

### Step 3: Render and show the draft in chat

Run with `--render-only` to generate the HTML without sending:

```
python3 tools/email/send-release-note.py \
    --file output/cs/release-notes/{date}-{slug}.md \
    --render-only
```

This writes the `.html` sibling. Open it / show the user the markdown source in chat and confirm before sending preview. Offer two options: (a) send the preview to Yonatan, (b) edit specific items first.

### Step 4: Send preview to Yonatan for approval

Once the user confirms the draft, send the preview:

```
python3 tools/email/send-release-note.py \
    --file output/cs/release-notes/{date}-{slug}.md \
    --mode preview
```

This sends a single email to `yonatank@cyvore.com` with subject `[PREVIEW] Cyvore - Platform Release: {title}`. No CCs. No customers.

Tell the user explicitly: "Preview sent to Yonatan for approval. Waiting for go/no-go before I ask for the recipient list."

### Step 5: Wait for approval

The user (relaying Yonatan's decision, or Yonatan himself) responds with one of:

- **"approved" / "ship it" / "go"** → proceed to Step 6.
- **"change X" / "edit Y"** → revise the markdown source, re-render, send another preview (loop Step 3–5).

Do NOT proceed to publish without explicit approval. There is no silent path from draft to customers.

### Step 6: Get the recipient list

Once approved, ask the user for the **recipient list**. There are two shapes; pick the one that matches the release:

- **Per-recipient sends (default):** comma-separated list of customer emails. Each address gets its own email; nobody sees any other customer.
- **Per-company shared threads:** when a single customer org has multiple stakeholders who should share the thread (e.g. customer admin + their MSP, or two managers at the same company), group them. The script supports this via `--group`: all addresses on `--to` go on the To: line of one email. Run the publish command **once per company** in this mode.

Example dialogue:

> "Approved. Two ways to send: (a) one email per recipient (default), or (b) grouped per company (multiple stakeholders at one customer share a thread). Which one? And paste the recipient list. I'll CC the Cyvore team (ellar, peterv, yoav, yiftach) on every send — say 'override CC' if you want different CCs."

If the user says "override CC", capture the new CC list. Otherwise use the default.

### Step 7: Publish

**Per-recipient mode (default):**

```
python3 tools/email/send-release-note.py \
    --file output/cs/release-notes/{date}-{slug}.md \
    --mode publish \
    --to "<comma-separated recipients>"
```

The script sends **one email per recipient** (To: just that person), with the Cyvore team on CC for every send. Each customer's thread therefore shows only themselves + the Cyvore team — they do not see other customers on To:.

**Grouped-per-company mode (`--group`):**

```
# One run per company; --to lists every stakeholder at THAT company
python3 tools/email/send-release-note.py \
    --file output/cs/release-notes/{date}-{slug}.md \
    --mode publish --group \
    --to "admin@customer.com,msp@partner.com"
```

All `--to` addresses share the To: line of a single email. Use this when a customer org has multiple stakeholders who should see each other on the thread (admin + MSP, or co-owners at the same customer). For multiple companies, run the command once per company. Customers across companies still never see each other — only the in-group recipients share the thread.

If the user gave a CC override, add `--cc "<list>"` to the command (works in both modes).

Confirm in chat: "Published N email(s) covering M recipient(s). CC on every send: {list}. Files at `output/cs/release-notes/{date}-{slug}.md` and `.html`."

---

## Output Schema

The markdown source file uses the schema in `agents/cs/templates/release-note.md`. After rendering, the `.html` sibling is the exact email body that was sent. Both files should be kept (the markdown is the source of truth; the HTML is the historical artifact of what customers actually received).

---

## Quality Checklist

- [ ] Every changelog item has exactly one tag from the allowed vocabulary
- [ ] TL;DR bullets are 1:1 with changelog items, in the same order
- [ ] Item bodies are 2–4 sentences, customer-facing language, no internal product/Jira names
- [ ] No fabricated metrics — every number traces to a real source, or the language is qualitative
- [ ] Headline and subtitle make sense without reading the rest
- [ ] Preview was sent to `yonatank@cyvore.com` and explicitly approved before any customer send
- [ ] Each customer org received the email in the intended shape (per-recipient by default, or grouped per company with `--group` when the user explicitly asked for a shared thread)
- [ ] Cyvore-team CC list was on every send unless the user explicitly overrode it
- [ ] Both `.md` and `.html` sibling files exist in `output/cs/release-notes/`
- [ ] Subject line is `Cyvore - Platform Release: {title}` (preview is `[PREVIEW] Cyvore - Platform Release: {title}`)

---

## Relationship to Other Skills

```
agents/cs/skills/release-notes (this skill)         →  customer-facing change communication
agents/cs/skills/health-check                       →  unrelated; per-customer health
agents/cs/skills/expansion-plan                     →  unrelated; per-customer expansion
agents/marketing/skills/content                     →  unrelated; release notes are NOT marketing copy
```

Release notes are explicitly **not** marketing. Marketing is welcome to adapt the content into a launch post afterwards, but the customer-facing release-note email is owned by CS — it goes to existing customers, in plain language, with no commercial framing.
