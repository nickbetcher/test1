# Development workflow: change → PR → test → deploy

```
feature branch ──push──► Pull request ──CI: lint, test, container smoke test──►
   code review (CODEOWNERS) ──squash merge──► main
      ──► build image, push to GHCR ──► deploy to staging (automatic)
      ──► git tag vX.Y.Z ──► approval ──► deploy to production
```

## One-time GitHub setup (Settings)

1. **Default branch.** After the first merge, make sure `main` is the default branch.
2. **Branch protection / ruleset on `main`** (*Settings → Rules → Rulesets*, or *Branches*):
   - Require a pull request before merging, with at least 1 approval.
   - Require review from Code Owners.
   - Require status checks to pass: `lint`, `test`, `container`.
   - Require branches to be up to date before merging.
   - Block force pushes and deletions.
   - Tip: while practicing alone you can't approve your own PR. Either allow
     admins to bypass the rule, or set required approvals to 0 and keep the status checks.
3. **Merge settings.** Allow squash merging only, and automatically delete head branches.
4. **Environments.** `staging` and `production`, with a required reviewer on
   production (see DEPLOYMENT.md).
5. **Security.** Turn on Dependabot alerts and updates (config is in
   `.github/dependabot.yml`), plus secret scanning and push protection.

## Everyday loop

```bash
git switch main && git pull
git switch -c feat/add-search          # 1. branch per change
# ...edit code and tests...
pytest && ruff check . && ruff format . # 2. run the same checks as CI
git commit -am "Add search to the registry table"
git push -u origin feat/add-search      # 3. push and open a PR
```

4. CI runs on the PR. Fix anything red by pushing more commits to the same branch.
5. A reviewer (CODEOWNERS) approves. Address comments with follow-up commits.
6. Squash-merge. The deploy workflow ships `main` to staging automatically.
7. Check staging, then release:
   ```bash
   git switch main && git pull
   git tag v0.2.0 && git push origin v0.2.0
   ```
   Approve the production deployment in the Actions tab.

## Practice exercises

Each one exercises the full pipeline:

1. Add a search box that filters the table (UI + test).
2. Add `PATCH /api/v1/applications/{name}` to change lifecycle (API + test + docs).
3. Replace `create_all` with Alembic migrations, and run them as a Kubernetes Job before deploy.
4. Add Trivy image scanning to CI and see a PR fail on a vulnerable base image.
5. Add read-only vs read-write API tokens.
6. Break a test on purpose, open a PR, and watch branch protection block the merge.
7. Wrap the API in an MCP server so an AI assistant can query the registry.

## Interview vocabulary this repo demonstrates

CI/CD, trunk-based development, protected branches, required status checks, code
owners, immutable artifacts (build once, promote the same image), environment
promotion with manual approval gates, 12-factor config through environment variables,
secrets kept out of git, health and readiness probes, rolling deployments and
rollback, least-privilege containers (non-root, read-only filesystem, dropped
capabilities), SSO at the edge, and service-account auth for agents.
