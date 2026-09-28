def test_health(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").status_code == 200


def test_create_and_list(client, sample):
    r = client.post("/api/v1/applications", json=sample)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "payments-api"
    assert body["created_by"] == "anonymous"

    apps = client.get("/api/v1/applications").json()
    assert [a["name"] for a in apps] == ["payments-api"]
    assert client.get("/api/v1/applications/payments-api").status_code == 200


def test_duplicate_name_conflicts(client, sample):
    assert client.post("/api/v1/applications", json=sample).status_code == 201
    assert client.post("/api/v1/applications", json=sample).status_code == 409


def test_validation(client, sample):
    bad = {**sample, "name": "Not A Slug", "owner_email": "nope"}
    r = client.post("/api/v1/applications", json=bad)
    assert r.status_code == 422
    fields = {e["loc"][-1] for e in r.json()["detail"]}
    assert {"name", "owner_email"} <= fields


def test_missing_app_404(client):
    assert client.get("/api/v1/applications/ghost").status_code == 404


def test_agent_token_is_recorded(client, sample):
    r = client.post(
        "/api/v1/applications", json=sample, headers={"Authorization": "Bearer test-token"}
    )
    assert r.json()["created_by"] == "service:ci-agent"


def test_bad_token_rejected(client, sample):
    r = client.post("/api/v1/applications", json=sample, headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401


def test_sso_header_identity(client, sample):
    r = client.post(
        "/api/v1/applications", json=sample, headers={"X-Forwarded-Email": "alice@example.com"}
    )
    assert r.json()["created_by"] == "user:alice@example.com"


def test_require_auth(client, settings, sample):
    settings.require_auth = True
    assert client.get("/api/v1/applications").status_code == 401
    ok = client.get("/api/v1/applications", headers={"Authorization": "Bearer test-token"})
    assert ok.status_code == 200
