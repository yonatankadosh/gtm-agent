# Git workflow for Chief of Staff (and related) features

This repo uses **`gtm-plus` as the day-to-day integration line** (where agent work lands first). `main` remains the long-term default branch on GitHub; merge `gtm-plus` → `main` when you want production parity.

## Branching

1. Sync the base branch:

   ```bash
   git fetch origin
   git checkout gtm-plus
   git pull origin gtm-plus
   ```

2. Create a short-lived feature branch:

   ```bash
   git checkout -b feature/cos-<short-name>
   ```

   Examples: `feature/cos-weekly-digest-v2`, `feature/cos-board-kpi-section`.

3. Scope: CoS work usually touches `agents/chief-of-staff/` and sometimes `agents/orchestrator.md` for routing. Keep one capability per branch unless changes are tightly coupled.

## Commits

- Prefer small commits with clear messages (skill draft → orchestrator wiring → `.cursor/rules` update).
- Do not commit secrets or customer data (see `.gitignore`: `state/`, `tools/email-config.json`, sensitive `output/` paths).

## Pull request

- Push: `git push -u origin feature/cos-<short-name>`
- Open a PR **into `gtm-plus`** (same as the branch base).
- PR description should cover what changed, which paths, and how to validate (e.g. dry-run or manual skill steps).
- Use **squash merge** or **merge commit** consistently—pick one convention for the repo.

## After merge

- Delete the remote feature branch on GitHub.
- Locally: `git checkout gtm-plus && git pull` and `git branch -d feature/cos-<short-name>`.

## Large changes

Use stacked PRs only when it helps review (template only → skill → orchestrator), each targeting `gtm-plus` and merging in order.

## If policy changes

If `main` must always be the integration line, branch from `main`, PR into `main`, and treat `gtm-plus` as staging only—do not mix bases without a deliberate merge strategy.
