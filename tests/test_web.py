def test_index_empty(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "No applications registered yet" in r.text


def test_form_renders(client):
    r = client.get("/applications/new")
    assert r.status_code == 200
    assert 'name="owner_email"' in r.text


def test_form_submit_creates_and_redirects(client, sample):
    r = client.post("/applications/new", data=sample, follow_redirects=False)
    assert r.status_code == 303
    page = client.get("/").text
    assert "payments-api" in page and "Payments" in page


def test_form_blank_repo_url_is_allowed(client, sample):
    r = client.post("/applications/new", data={**sample, "repo_url": ""}, follow_redirects=False)
    assert r.status_code == 303


def test_form_shows_errors_and_keeps_input(client, sample):
    r = client.post("/applications/new", data={**sample, "owner_email": "bad"})
    assert r.status_code == 422
    assert "owner_email" in r.text
    assert 'value="payments-api"' in r.text


def test_form_duplicate(client, sample):
    client.post("/applications/new", data=sample)
    r = client.post("/applications/new", data=sample)
    assert r.status_code == 422
    assert "already exists" in r.text


def test_html_is_escaped(client, sample):
    client.post("/applications/new", data={**sample, "description": "<script>x</script>"})
    assert "<script>x</script>" not in client.get("/").text
