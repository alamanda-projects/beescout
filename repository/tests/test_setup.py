"""
Tests for the /setup bootstrap endpoint.
Covers: first-run success, duplicate prevention, password validation.
"""

import pytest


VALID_PAYLOAD = {
    "username": "rootuser",
    "name": "Root User",
    "password": "Str0ng!Pass",
    "group_access": "root",
    "data_domain": "platform",
    "is_active": True,
}


@pytest.mark.asyncio
async def test_setup_status_not_complete_initially(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    response = await ac.get("/setup/status")
    assert response.status_code == 200
    assert response.json()["setup_complete"] is False


@pytest.mark.asyncio
async def test_setup_creates_root_when_none_exists(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["usr"].insert_one.return_value = None
    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert "Root account created" in response.json()["message"]


@pytest.mark.asyncio
async def test_setup_returns_409_when_root_exists(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {"username": "existing_root", "group_access": "root"}
    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_setup_rejects_weak_password(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    payload = {**VALID_PAYLOAD, "password": "weakpass"}
    response = await ac.post("/setup", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_setup_status_complete_when_root_exists(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {"username": "root", "group_access": "root", "is_active": True}
    response = await ac.get("/setup/status")
    assert response.status_code == 200
    assert response.json()["setup_complete"] is True
