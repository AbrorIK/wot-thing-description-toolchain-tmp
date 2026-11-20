"""Check the composed TD-level Modbus JSON Schema against complete TD samples and PR #508.

The composed schema follows w3c/wot-binding-templates PR #508 (decision recorded as D-09 in
docs/bindings/modbus-vocabulary-inventory.md), so it must give the same verdict as the PR #508
schema on every sample and have the same structure apart from descriptions and list order.
The TD 1.1 schema referenced through anyOf is resolved offline from resources/upstream/schemas/.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource

from src.wotis import TD11_SCHEMA_URI
from src.wotis.generators.bindings import generate_binding_td_schema

REPO_ROOT = Path(__file__).resolve().parent.parent
MODBUS_SCHEMA = REPO_ROOT / "resources" / "schemas" / "bindings" / "modbus.yaml"
PR508_SCHEMA = REPO_ROOT / "resources" / "upstream" / "bindings" / "modbus" / "modbus.schema.pr508.json"
TD11_SCHEMA = REPO_ROOT / "resources" / "upstream" / "schemas" / "td11-json-schema-validation.json"
SAMPLES_DIR = Path(__file__).resolve().parent / "data" / "bindings" / "modbus" / "td"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry() -> Registry:
    td11 = Resource.from_contents(_load_json(TD11_SCHEMA))
    # Register under the published URI and the file's own $id, which its internal refs resolve against.
    return Registry().with_resources([(TD11_SCHEMA_URI, td11), (td11.id(), td11)])


@pytest.fixture(scope="module")
def composed_schema() -> dict:
    return generate_binding_td_schema(MODBUS_SCHEMA, "ModbusForm", TD11_SCHEMA_URI)


@pytest.fixture(scope="module")
def pr508_schema() -> dict:
    return _load_json(PR508_SCHEMA)


@pytest.fixture(scope="module")
def composed_validator(composed_schema: dict, registry: Registry) -> Draft7Validator:
    Draft7Validator.check_schema(composed_schema)
    return Draft7Validator(composed_schema, registry=registry)


@pytest.fixture(scope="module")
def pr508_validator(pr508_schema: dict, registry: Registry) -> Draft7Validator:
    return Draft7Validator(pr508_schema, registry=registry)


def _samples() -> list:
    return [
        pytest.param(path, path.parent.name == "valid", id=path.relative_to(SAMPLES_DIR).as_posix())
        for path in sorted(SAMPLES_DIR.rglob("*.json"))
    ]


def _without_descriptions_sorted(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: _without_descriptions_sorted(value) for key, value in node.items() if key != "description"}
    if isinstance(node, list):
        return sorted((_without_descriptions_sorted(item) for item in node), key=json.dumps)
    return node


@pytest.mark.parametrize("sample_path, is_expected_valid", _samples())
def test_composed_schema_verdict(composed_validator, sample_path: Path, is_expected_valid: bool):
    errors = list(composed_validator.iter_errors(_load_json(sample_path)))
    if is_expected_valid:
        assert not errors, f"composed schema rejected {sample_path.name}: {errors[0].message}"
    else:
        assert errors, f"composed schema accepted {sample_path.name}"


@pytest.mark.parametrize("sample_path, is_expected_valid", _samples())
def test_pr508_verdict_preserved(composed_validator, pr508_validator, sample_path: Path, is_expected_valid: bool):
    td = _load_json(sample_path)
    assert composed_validator.is_valid(td) == pr508_validator.is_valid(td)


@pytest.mark.parametrize("key", ["$schema", "anyOf", "type", "properties"])
def test_td_wiring_matches_pr508(composed_schema: dict, pr508_schema: dict, key: str):
    assert composed_schema[key] == pr508_schema[key]


def test_affordance_matches_pr508(composed_schema: dict, pr508_schema: dict):
    assert composed_schema["definitions"]["affordance"] == pr508_schema["definitions"]["affordance"]


def test_modbus_form_matches_pr508(composed_schema: dict, pr508_schema: dict):
    assert _without_descriptions_sorted(composed_schema["definitions"]["modbusForm"]) == (
        _without_descriptions_sorted(pr508_schema["definitions"]["modbusForm"])
    )


def test_no_linkml_metadata_left(composed_schema: dict):
    assert set(composed_schema) == {"$schema", "anyOf", "definitions", "type", "properties"}
    assert set(composed_schema["definitions"]) == {"modbusForm", "affordance"}
