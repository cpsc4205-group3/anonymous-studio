# How to Protect the `main` Branch

Branch protection prevents direct pushes to `main` and ensures every change goes through a pull request with passing checks and code review.

## Prerequisites added by this PR

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI workflow that checks Python syntax on every PR — use as a **required status check** |
| `.github/CODEOWNERS` | Automatically requests reviews from `@cpsc4205-group3/maintainers` |

## Steps (GitHub UI)

1. Go to **Settings → Branches** in the repository
   ([direct link](https://github.com/cpsc4205-group3/v2_anonymous-studio/settings/branches))
2. Under **Branch protection rules**, click **Add branch protection rule** (or **Add classic branch protection rule** if using the new rulesets UI)
3. Set **Branch name pattern** to `main`
4. Enable the following recommended settings:

| Setting | Why |
|---------|-----|
| **Require a pull request before merging** | No direct pushes to `main` |
| ↳ Require approvals (1+) | At least one teammate must review |
| ↳ Dismiss stale pull request approvals when new commits are pushed | Re-review after changes |
| **Require status checks to pass before merging** | Ensures CI passes |
| ↳ Require branches to be up to date before merging | PR must be current with `main` |
| ↳ Add **CI / lint** as a required status check | Uses the workflow from this PR |
| **Do not allow bypassing the above settings** | Applies rules to admins too |

5. Click **Create** / **Save changes**

## Using the new Repository Rulesets (alternative)

GitHub now offers **Rulesets** as a more flexible replacement for classic branch protection.

1. Go to **Settings → Rules → Rulesets**
2. Click **New ruleset → New branch ruleset**
3. Name it (e.g., `Protect main`)
4. Under **Target branches**, add `main`
5. Enable **Require a pull request before merging** and **Require status checks to pass**
6. Add `CI / lint` as a required check
7. Click **Create**

## Verifying protection is active

After enabling, the branch list at **Code → Branches** will show a 🔒 icon next to `main`. Attempting to push directly will be rejected:

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
```

## CODEOWNERS

The `.github/CODEOWNERS` file automatically requests reviews from the `@cpsc4205-group3/maintainers` team. If that team doesn't exist yet, create it at **Organization → Teams**, or replace the entry with individual GitHub usernames (e.g., `@51nk0r5w1m`).
