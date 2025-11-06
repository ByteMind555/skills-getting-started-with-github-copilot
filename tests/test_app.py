import os
import pathlib
import importlib.util

from fastapi.testclient import TestClient


def load_app():
    """Dynamically load the FastAPI app from src/app.py so tests don't rely on package imports."""
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    app_path = repo_root / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("app_module", str(app_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_signup_and_unregister_flow():
    app = load_app()
    client = TestClient(app)

    # Ensure activities endpoint is available and contains a known activity
    r = client.get("/activities")
    assert r.status_code == 200
    activities = r.json()
    assert "Track and Field" in activities

    activity_name = "Track and Field"
    email = "pytest-user@example.com"

    # Signup the test user
    signup_resp = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert signup_resp.status_code == 200
    assert "Signed up" in signup_resp.json().get("message", "")

    # Confirm participant was added
    after = client.get("/activities").json()
    assert email in after[activity_name]["participants"]

    # Unregister the test user
    del_resp = client.delete(f"/activities/{activity_name}/participants?email={email}")
    assert del_resp.status_code == 200
    assert "Unregistered" in del_resp.json().get("message", "")

    # Confirm participant was removed
    after_del = client.get("/activities").json()
    assert email not in after_del[activity_name]["participants"]


def test_unregister_nonexistent_returns_404():
    app = load_app()
    client = TestClient(app)

    activity_name = "Track and Field"
    missing_email = "does-not-exist@example.com"

    # ensure this email is not present
    r = client.get("/activities")
    assert r.status_code == 200
    assert missing_email not in r.json()[activity_name]["participants"]

    # Attempt to unregister a non-existent participant
    resp = client.delete(f"/activities/{activity_name}/participants?email={missing_email}")
    assert resp.status_code == 404
