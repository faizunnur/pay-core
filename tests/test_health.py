"""Tests for the health endpoints."""


def test_health_reports_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "paycore"


def test_health_includes_a_version(client):
    body = client.get("/health").json()

    assert body["version"]
    assert body["environment"]


def test_root_points_at_the_docs(client):
    body = client.get("/").json()

    assert body["docs"] == "/docs"
