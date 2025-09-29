import io
import json
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

AUTH = {"Authorization": "Bearer demo"}


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["status"] == "ok"


def test_list_leads_requires_auth():
    r = client.get("/api/v1/leads")
    assert r.status_code == 401


def test_list_leads_ok():
    r = client.get("/api/v1/leads", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["total"] >= 2
    assert isinstance(body["data"]["items"], list)


def test_get_lead_by_id_ok():
    r = client.get("/api/v1/leads", headers=AUTH)
    lead_id = r.json()["data"]["items"][0]["id"]

    r2 = client.get(f"/api/v1/leads/{lead_id}", headers=AUTH)
    assert r2.status_code == 200
    body = r2.json()
    assert body["data"]["id"] == lead_id
    assert "vars" in body["data"]


def test_import_csv():
    csv_content = (
        "email,company,url,image_key,extra_field\n"
        "new.user@example.com,New Co,https://new.co,new-logo,42\n"
        "john.doe@acme.com,Acme Updated,https://acme.com,,\n"
        "invalid-email,Nope,https://nope.com,.,\n"
    ).encode("utf-8")

    files = {"file": ("leads.csv", io.BytesIO(csv_content), "text/csv")}
    r = client.post("/api/v1/import/leads", headers=AUTH, files=files)
    assert r.status_code == 200
    body = r.json()
    data = body["data"]
    assert data["inserted"] >= 1
    assert data["updated"] >= 1
    assert data["skipped"] >= 1
    assert data["jobId"].startswith("import-")


def test_asset_url():
    r = client.get("/api/v1/assets/image-by-key", headers=AUTH, params={"key": "acme-logo"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data is not None
    url = data["url"]
    assert isinstance(url, str)
    assert len(url) > 0
    # Accept both mock URLs and real Supabase URLs
    assert "acme-logo" in url or url.endswith("acme-logo.png")


def test_preview_render():
    # fetch any lead id
    r = client.get("/api/v1/leads", headers=AUTH)
    lead_id = r.json()["data"]["items"][0]["id"]

    payload = {"template_id": "1", "lead_id": lead_id}
    r2 = client.post("/api/v1/previews/render", headers=AUTH, json=payload)
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert "html" in data and "text" in data and "warnings" in data


def test_import_job_status():
    # First create an import job
    csv_content = "email,company\ntest@example.com,Test Co\n".encode("utf-8")
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    r = client.post("/api/v1/import/leads", headers=AUTH, files=files)
    assert r.status_code == 200
    job_id = r.json()["data"]["jobId"]

    # Then check job status
    r2 = client.get(f"/api/v1/import/jobs/{job_id}", headers=AUTH)
    assert r2.status_code == 200
    job_data = r2.json()["data"]
    assert job_data["id"] == job_id
    assert job_data["status"] in ["running", "succeeded", "failed"]
    assert "progress" in job_data
    assert "inserted" in job_data
    assert "updated" in job_data
    assert "skipped" in job_data
