# Deploying in a corporate setting

This is how a typical mid-to-large company would run an internal tool like this.
The specific vendors vary (AWS/GCP/Azure, Okta/Entra ID, Vault/Secrets Manager),
but the shape is almost always the same.

## Architecture

```
                 Corporate network / VPN / zero-trust access
                                   │
   Employee's browser ──► Internal load balancer / ingress (TLS)
                                   │
                         SSO proxy (oauth2-proxy / IAP)
                         ├─ not logged in → redirect to IdP (Okta, Entra ID)
                         └─ logged in → adds X-Auth-Request-Email header
                                   │
   AI agent / script ──► Bearer token ─┐
                                   ▼   ▼
                     app-registry pods (Kubernetes, 2–3 replicas)
                                   │
                     Managed Postgres (RDS / Cloud SQL), private subnet
```

## The pieces, and why each exists

| Concern | Typical choice | In this repo |
|---|---|---|
| Source control and review | GitHub / GitLab with protected `main` | `.github/`, CODEOWNERS, PR template |
| Build | CI builds one immutable container image per commit | `Dockerfile`, `deploy.yml` → GHCR |
| Image registry | ECR, GCR/Artifact Registry, ACR, GHCR, Artifactory | GHCR (`ghcr.io/<owner>/<repo>`) |
| Runtime | Kubernetes (EKS/GKE/AKS). Smaller shops use ECS, Cloud Run or App Service | `deploy/k8s/` (Kustomize) |
| Environments | dev → staging → production, separate namespaces or clusters | `overlays/staging`, `overlays/production` |
| Database | Managed Postgres with backups and point-in-time restore | `APP_DATABASE_URL` |
| Secrets | Vault / AWS Secrets Manager, synced into the cluster by External Secrets | `app-registry-secrets` Secret, not in git |
| Human auth | SSO via the corporate identity provider (OIDC/SAML), enforced at the proxy | `X-Forwarded-Email` / `X-Auth-Request-Email` header |
| Machine / agent auth | Per-agent service account tokens, or OAuth client credentials | `APP_API_TOKENS` bearer tokens |
| Network exposure | Internal-only DNS and load balancer, never on the public internet | `ingressClassName: nginx-internal` |
| Observability | Logs → Datadog/Splunk/ELK, metrics → Prometheus, alerts → PagerDuty | `/healthz`, `/readyz` probes (extend with metrics) |
| Change safety | Rolling deploys, health checks, fast rollback | `maxUnavailable: 0`, readiness probe, redeploy previous tag |

## Agentic access

Agents are treated like any other service account:

1. **A documented contract.** FastAPI publishes an OpenAPI spec at `/openapi.json`.
   Most agent frameworks can turn an OpenAPI spec directly into tools.
2. **Their own identity.** Each agent gets its own token (`name:token` in
   `APP_API_TOKENS`), so every record's `created_by` shows `service:<agent-name>`
   and you can revoke one agent without affecting the others.
3. **Least privilege.** A natural next step is scopes, for example a read-only token
   for agents that only look things up, and a write token only for approved automation.
4. **An MCP server (optional).** Many companies wrap internal APIs in a
   Model Context Protocol server so tools like Claude can call
   `list_applications` / `register_application` directly. It's a thin wrapper around
   the REST API and is a good extension exercise.
5. **Auditability and rate limits.** Put these at the gateway, or add them to the app
   as usage grows.

In production, move the token list into the secret manager, and consider replacing
static tokens with short-lived OAuth2 client-credentials tokens from the IdP.

## One-time setup to make this real

1. **Cluster.** Any Kubernetes cluster works. For practice, use `kind` or `minikube`
   locally, or a small managed cluster.
2. **Ingress and SSO.** Install ingress-nginx (as the `nginx-internal` class) and
   oauth2-proxy configured against your IdP. For practice, a free Okta developer
   account, Auth0, or Google OAuth all work.
3. **Database.** Create a Postgres instance and a database and user for the app.
4. **Secret.** Create the secret in each namespace. In a real company, External Secrets
   creates it from Vault or Secrets Manager.
   ```bash
   kubectl -n app-registry-staging create secret generic app-registry-secrets \
     --from-literal=APP_DATABASE_URL='postgresql+psycopg://user:pass@host:5432/registry' \
     --from-literal=APP_API_TOKENS='catalog-agent:<random-token>'
   ```
5. **GitHub environments.** In *Settings → Environments*, create `staging` and
   `production`. Add a `KUBECONFIG` secret to each. On `production`, add yourself as a
   **required reviewer** so production deploys wait for approval.
   Without a `KUBECONFIG` secret, the deploy job renders the manifests and skips the
   apply, so the pipeline still runs end to end as a dry run.

## Releasing and rolling back

- Merging to `main` builds `ghcr.io/<repo>:sha-<commit>` and deploys it to staging.
- Tagging `v1.2.3` promotes the same kind of immutable image to production after approval.
- To roll back, re-run the deploy workflow for the previous tag, or run
  `kubectl rollout undo deploy/app-registry -n app-registry-production`.

## Known simplifications (good interview talking points)

- Tables are created on startup. A real service would run **Alembic migrations** as a
  separate, versioned deploy step, and keep migrations backward compatible so rolling
  deploys are safe.
- Trusting the identity header is only safe because the app is reachable **only**
  through the SSO proxy. Enforce that with a NetworkPolicy, or verify the proxy's
  signed JWT instead of a plain header.
- There's no authorization model yet, such as "only owners can edit their app".
- Missing observability: structured JSON logs, Prometheus `/metrics`, and tracing.
- Supply-chain hardening: image scanning (Trivy/Grype), SBOMs, and signed images (cosign).
