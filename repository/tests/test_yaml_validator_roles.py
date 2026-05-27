"""Tests untuk strict stakeholder.role enforcement di YAML validator.

Spec BeeScout (data-contract/docs/README.md line 94): enum closed 4 nilai
[owner, producer, consumer, reviewer]. Validator harus reject role non-spec.
"""

import io

import pytest


def _yaml_payload(role: str) -> bytes:
    """Bangun YAML minimal valid dengan 1 stakeholder pakai role param."""
    return f"""\
standard_version: 1.0.0
contract_number: CN-TEST
metadata:
  name: Test Contract
  owner: Test Team
  version: 1.0.0
  type: CSV
  stakeholders:
    - name: Tester
      role: {role}
""".encode("utf-8")


@pytest.fixture
def override_token():
    from app.main import app
    from app.core.verificator import token_verification

    def _set():
        app.dependency_overrides[token_verification] = lambda: {
            "usr": "admin", "typ": "user", "lvl": "admin", "sts": True, "tim": "admin"
        }

    yield _set
    app.dependency_overrides.pop(token_verification, None)


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["owner", "producer", "consumer", "reviewer"])
async def test_validator_accepts_4_spec_roles(client, override_token, role):
    """4 nilai spec diterima validator (Layer 2)."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_payload(role))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    # Tidak ada error tentang role
    role_errors = [e for e in body.get("errors", []) if "role" in e.get("field", "")]
    assert role_errors == [], f"Unexpected role error for spec value {role!r}: {role_errors}"


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["engineer", "analyst", "architect", "steward"])
async def test_validator_rejects_legacy_non_spec_roles(client, override_token, role):
    """Role yang sebelumnya allow (engineer/analyst/architect/steward) sekarang
    ditolak — strict ke 4 nilai spec."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_payload(role))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    role_errors = [e for e in body.get("errors", []) if "role" in e.get("field", "")]
    assert len(role_errors) == 1, f"Expected 1 role error, got: {role_errors}"
    assert role in role_errors[0]["message"]
    # Suggestion menyebut 4 nilai spec
    suggestion = role_errors[0].get("suggestion", "")
    for spec_role in ["owner", "producer", "consumer", "reviewer"]:
        assert spec_role in suggestion


@pytest.mark.asyncio
async def test_validator_rejects_custom_role(client, override_token):
    """Role custom asing → reject."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_payload("data-scientist"))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    body = res.json()
    role_errors = [e for e in body.get("errors", []) if "role" in e.get("field", "")]
    assert len(role_errors) == 1
