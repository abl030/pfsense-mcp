"""
Smoke tests for pfSense REST API v2.

These tests verify basic API connectivity and CRUD operations
against a live pfSense VM booted from the golden image.
"""

import httpx
import pytest


def test_api_version(api_client: httpx.Client):
    """API responds with version info."""
    resp = api_client.get("/api/v2/system/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert "data" in data


def test_basic_auth_works(basic_auth_client: httpx.Client):
    """BasicAuth authentication works."""
    resp = basic_auth_client.get("/api/v2/system/version")
    assert resp.status_code == 200


def test_create_and_read_firewall_alias(api_client: httpx.Client):
    """Create a firewall alias via POST, then read it back via GET."""
    # Create an alias
    alias_payload = {
        "name": "test_smoke_alias",
        "type": "host",
        "descr": "Smoke test alias",
        "address": ["10.0.0.1", "10.0.0.2"],
    }
    create_resp = api_client.post(
        "/api/v2/firewall/alias",
        json=alias_payload,
    )
    assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
    create_data = create_resp.json()
    assert create_data["code"] == 200
    alias_id = create_data["data"]["id"]

    # Read it back
    get_resp = api_client.get(
        "/api/v2/firewall/alias",
        params={"id": alias_id},
    )
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["data"]["name"] == "test_smoke_alias"
    assert get_data["data"]["type"] == "host"

    # Clean up: delete the alias
    delete_resp = api_client.delete(
        "/api/v2/firewall/alias",
        params={"id": alias_id},
    )
    assert delete_resp.status_code == 200


def test_list_firewall_aliases(api_client: httpx.Client):
    """List firewall aliases (plural endpoint)."""
    resp = api_client.get("/api/v2/firewall/aliases")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)


def test_list_interfaces(api_client: httpx.Client):
    """List network interfaces."""
    resp = api_client.get("/api/v2/interface")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
