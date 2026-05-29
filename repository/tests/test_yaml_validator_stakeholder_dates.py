"""Tests untuk strict stakeholder.date_in enforcement di YAML validator (#114 T1.3).

Spec BeeScout (data-contract/docs/README.md L95): `date_in` YES required
per stakeholder, `date_out` NO. Validator harus reject stakeholder ber-name
yang date_in-nya kosong.
"""

import io

import pytest


def _yaml_with_stakeholder(date_in: str | None = None, name: str = "Tester") -> bytes:
    lines = [
        "standard_version: 1.0.0",
        "contract_number: CN-STK",
        "metadata:",
        "  name: Test",
        "  owner: Test",
        "  version: 1.0.0",
        "  type: CSV",
        "  effective_date: 2024-01-01",
        "  expiry_date: 2025-12-31",
        "  stakeholders:",
        f"    - name: {name}",
        "      role: owner",
    ]
    if date_in is not None:
        lines.append(f"      date_in: {date_in}")
    return ("\n".join(lines) + "\n").encode("utf-8")


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


def _date_in_errors(body: dict) -> list:
    return [e for e in body.get("errors", []) if "date_in" in e.get("field", "")]


@pytest.mark.asyncio
async def test_validator_accepts_stakeholder_with_date_in(client, override_token):
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_with_stakeholder(date_in="2024-01-15"))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    assert _date_in_errors(res.json()) == []


@pytest.mark.asyncio
async def test_validator_rejects_stakeholder_without_date_in(client, override_token):
    """Stakeholder ber-name tapi tanpa date_in → 1 error."""
    ac, _ = client
    override_token()
    file = io.BytesIO(_yaml_with_stakeholder(date_in=None))
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("test.yaml", file, "application/x-yaml")},
    )
    assert res.status_code == 200, res.text
    errs = _date_in_errors(res.json())
    assert len(errs) == 1
    assert errs[0]["field"] == "metadata.stakeholders[0].date_in"
    assert "wajib" in errs[0]["message"].lower()
