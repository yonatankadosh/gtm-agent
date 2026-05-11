# Partner Mapping Skill (owned by Partnerships)

## Purpose

Produce the universe of partners worth pursuing — categorized, prioritized, with a fit rationale per category. Answers: who should we partner with, why, and in what order? The output is the foundation that every co-sell plan builds on.

## Inputs

- `context/product-overview.md`
- `context/customers.md`
- `output/icp.md`
- `output/target-accounts.md`
- Web search for partner candidates (vendors in the ICP's stack, complementary platforms, channel partners, system integrators)

## Output

Write to `output/partnerships/landscape.md`.

---

## Methodology

### Step 1: Define the partner categories

Pick the categories that matter for our motion. Standard set:

- **Technology partners** — products that integrate with ours and where joint customers benefit (e.g., security platforms with adjacent coverage)
- **Channel / reseller partners** — companies that sell on our behalf (boutique consultancies, MSSPs)
- **System integrators** — implementation partners that make us easier to deploy
- **Co-marketing partners** — events, podcasts, content collaborations
- **Israeli ecosystem partners** — Israeli-founded vendors that share our network advantage (Wiz, SentinelOne, etc.) — separate category because the Israel angle is structural

### Step 2: Populate each category

For each partner candidate, capture the minimum:

- Partner name + domain
- Category (above)
- Their reach into our ICPs (which ICP, how strong)
- Mutual value (one sentence each direction)
- Known relationship (existing? warm intro path?)
- Source of the lead (how did this partner end up on the list)

Don't try to be exhaustive — capture 5-15 partners across categories, only ones with a real path. A long speculative list is worse than a short real one.

### Step 3: Prioritize

Score each partner on three dimensions, 1-3:

- **ICP overlap** — how directly does this partner reach our target accounts?
- **Activation effort** — how hard is it to get a joint motion live? (1 = months of legal, 3 = a phone call)
- **Mutual incentive** — does this partner have a real reason to want this? (1 = we want it, they don't care; 3 = they actively need us)

Total /9. Tier:

- **Tier 1 (8-9):** pursue now
- **Tier 2 (6-7):** pursue when we have bandwidth
- **Tier 3 (≤5):** monitor, don't pursue

### Step 4: Recommend the top 3 to activate

For each Tier 1, name the next action:

- The partner-side contact (real person if known, role if not)
- The first meeting / artifact (intro call, joint POC scope, co-marketing pitch)
- The expected outcome (referral motion live, first joint deal, joint event committed)

---

## Output Schema

```
# Partner Landscape

**Date:** {YYYY-MM-DD}

## Categories considered
- Technology
- Channel / reseller
- System integrators
- Co-marketing
- Israeli ecosystem

## Partner table

| Partner | Domain | Category | ICP overlap | Activation effort | Mutual incentive | Total | Tier | Existing relationship | Notes |
|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | 1-3 | 1-3 | 1-3 | /9 | T1/T2/T3 | yes/no/warm | ... |

## Tier 1 — pursue now (top 3)

### {Partner 1}
- **Why:** {1-2 sentences}
- **Partner-side contact:** {name or role}
- **First action:** {meeting / artifact}
- **Expected outcome:** {what success looks like, with timeline}

### {Partner 2}
...

### {Partner 3}
...

## Tier 2 — pursue when bandwidth allows

- {Partner} — {one-line rationale and trigger that would upgrade them}
- ...

## Tier 3 — monitor

- {Partner} — {why they're noted but not pursued}
- ...

## Research gaps

- [ ] ...
```

---

## Quality Checklist

- [ ] At least 5 partners across at least 3 categories
- [ ] Every partner is real (verified domain, actual product/service)
- [ ] Each partner has all three dimension scores with one-sentence justification
- [ ] Top 3 Tier 1 partners have a named partner-side contact (or explicit "needs verification") and a specific next action
- [ ] No fabricated partner relationships or imaginary integrations
