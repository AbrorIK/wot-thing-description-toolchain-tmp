"""Check the generated Modbus Form JSON Schema against Form samples and the published schema.

The complete-TD schema composed from the same model is tested in test_modbus_binding_td_schema.py.

The published schema (resources/upstream/bindings/modbus/modbus.schema.json) is the
compatibility baseline, not the expected output: every place where the generated schema
gives a different verdict must be listed in PROPOSED_BEHAVIOR_CHANGES with its entry in
docs/bindings/modbus-vocabulary-inventory.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, validators

from src.wotis.generators.bindings import generate_binding_form_schema

REPO_ROOT = Path(__file__).resolve().parent.parent
MODBUS_SCHEMA = REPO_ROOT / "resources" / "schemas" / "bindings" / "modbus.yaml"
PUBLISHED_SCHEMA = REPO_ROOT / "resources" / "upstream" / "bindings" / "modbus" / "modbus.schema.json"
SAMPLES_DIR = Path(__file__).resolve().parent / "data" / "bindings" / "modbus" / "form"

# sample file name -> inventory entry that justifies the different verdict.
# Pending maintainer decision; remove an entry when upstream aligns.
PROPOSED_BEHAVIOR_CHANGES = {
    "read-device-identification.json": "D-03: readDeviceIdentification is in the spec and ontology, missing from the schema enum",
    "polling-time-fractional.json": "D-01: spec and ontology say integer milliseconds, published schema accepts any number",
    "timeout-fractional.json": "D-01: spec and ontology say integer milliseconds, published schema accepts any number",
}


@pytest.fixture(scope="module")
def generated_schema() -> dict:
    return generate_binding_form_schema(MODBUS_SCHEMA, "ModbusForm")


@pytest.fixture(scope="module")
def generated_validator(generated_schema: dict):
    cls = validators.validator_for(generated_schema)
    cls.check_schema(generated_schema)
    return cls(generated_schema)


@pytest.fixture(scope="module")
def published_form_schema() -> dict:
    published = json.loads(PUBLISHED_SCHEMA.read_text(encoding="utf-8"))
    return {"$ref": "#/definitions/modbusForm", "definitions": published["definitions"]}


@pytest.fixture(scope="module")
def published_validator(published_form_schema: dict) -> Draft7Validator:
    return Draft7Validator(published_form_schema)


def _samples() -> list:
    return [
        pytest.param(path, path.parent.name == "valid", id=path.relative_to(SAMPLES_DIR).as_posix())
        for path in sorted(SAMPLES_DIR.rglob("*.json"))
    ]


def _published_form_properties(published_form_schema: dict) -> dict:
    return published_form_schema["definitions"]["modbusForm"]["properties"]


def _enum_values(schema: dict, property_schema: dict) -> set[str] | None:
    try:
        ref = property_schema["$ref"]
    except KeyError:
        return set(property_schema["enum"]) if "enum" in property_schema else None
    return set(schema["$defs"][ref.rsplit("/", 1)[-1]]["enum"])


@pytest.mark.parametrize("sample_path, is_expected_valid", _samples())
def test_generated_schema_verdict(generated_validator, sample_path: Path, is_expected_valid: bool):
    form = json.loads(sample_path.read_text(encoding="utf-8"))
    errors = list(generated_validator.iter_errors(form))
    if is_expected_valid:
        assert not errors, f"generated schema rejected {sample_path.name}: {errors[0].message}"
    else:
        assert errors, f"generated schema accepted {sample_path.name}"


@pytest.mark.parametrize("sample_path, is_expected_valid", _samples())
def test_published_verdict_preserved(
    generated_validator, published_validator, sample_path: Path, is_expected_valid: bool
):
    form = json.loads(sample_path.read_text(encoding="utf-8"))
    is_generated_valid = generated_validator.is_valid(form)
    is_published_valid = published_validator.is_valid(form)
    proposal = PROPOSED_BEHAVIOR_CHANGES.get(sample_path.name)
    if proposal:
        assert is_generated_valid != is_published_valid, f"stale proposal, verdicts now agree: {proposal}"
        return
    assert is_generated_valid == is_published_valid, (
        f"{sample_path.name}: generated={is_generated_valid}, published={is_published_valid}; "
        "record the change in PROPOSED_BEHAVIOR_CHANGES and the inventory"
    )


def test_form_terms_match_published(generated_schema: dict, published_form_schema: dict):
    assert set(generated_schema["properties"]) == set(_published_form_properties(published_form_schema))


def test_form_terms_are_open_for_other_form_fields(generated_schema: dict):
    assert generated_schema["additionalProperties"] is True


@pytest.mark.parametrize("term, added_values", [
    ("modv:entity", set()),
    ("modv:function", {"readDeviceIdentification"}),  # D-03
    ("modv:type", set()),
])
def test_enum_values_match_published(
    generated_schema: dict, published_form_schema: dict, term: str, added_values: set[str]
):
    generated_values = _enum_values(generated_schema, generated_schema["properties"][term])
    published_values = _enum_values(published_form_schema, _published_form_properties(published_form_schema)[term])
    assert generated_values - published_values == added_values
    assert published_values - generated_values == set()
