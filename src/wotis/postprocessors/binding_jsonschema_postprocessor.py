"""Compose a protocol binding's TD-level JSON Schema from its LinkML-generated Form schema.

W3C binding schemas (see bindings/protocols/template.schema.json in w3c/wot-binding-templates)
validate a whole Thing Description: they reference the TD schema through ``anyOf``, apply the
binding Form definition to every Form under ``properties``, ``actions`` and ``events``, and require
the binding prefix in ``@context``. They use JSON Schema draft-07. The LinkML JSON Schema generator
can express none of this (docs/known-linkml-gaps.md #13); it only produces the binding Form itself.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .jsonschema_postprocessor import _clean_metadata, _resolve_refs, _walk_schema

logger = logging.getLogger(__name__)

DRAFT_07 = "http://json-schema.org/draft-07/schema#"
AFFORDANCE_DEF = "affordance"
AFFORDANCE_MAPS = ("properties", "actions", "events")


def _form_definition_name(form_class: str) -> str:
    return form_class[0].lower() + form_class[1:]


def _add_deprecation_comments(form_def: dict, schema_view: SchemaView, form_class: str) -> None:
    # The generator drops LinkML `deprecated`; W3C binding schemas carry it as `$comment`.
    properties = form_def.get("properties", {})
    for slot in schema_view.class_induced_slots(form_class):
        if not slot.deprecated:
            continue
        try:
            properties[slot.alias or slot.name]["$comment"] = slot.deprecated
        except KeyError:
            logger.warning(f"Deprecated slot {slot.name} not found in {form_class} JSON Schema properties")


def _assert_no_defs_refs(schema: dict) -> None:
    def _check(obj: dict) -> None:
        ref = obj.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            raise ValueError(f"Unresolved reference {ref}: only enum ranges are supported in binding Forms")

    _walk_schema(schema, _check)


def _binding_namespace(schema_view: SchemaView) -> tuple[str, str]:
    prefix = schema_view.schema.default_prefix
    return prefix, schema_view.schema.prefixes[prefix].prefix_reference


def _context_constraint(prefix: str, namespace: str) -> dict:
    return {
        "type": "array",
        "contains": {
            "type": "object",
            "properties": {prefix: {"type": "string", "enum": [namespace]}},
            "required": [prefix],
        },
    }


def _affordance_definition(form_def_name: str) -> dict:
    return {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "forms": {"type": "array", "items": {"$ref": f"#/definitions/{form_def_name}"}},
            },
        },
    }


def compose_binding_td_schema(
    raw_form_schema: dict[str, Any],
    schema_view: SchemaView,
    form_class: str,
    td_schema_uri: str,
) -> dict[str, Any]:
    """Return the draft-07 TD-level schema that applies ``form_class`` to every Form of a TD."""
    form_schema = copy.deepcopy(raw_form_schema)
    _resolve_refs(form_schema, schema_view)
    _clean_metadata(form_schema)

    form_def = form_schema["$defs"][form_class]
    if form_def.get("additionalProperties") is True:
        del form_def["additionalProperties"]  # draft-07 default; keeps the Form open to TD terms
    _add_deprecation_comments(form_def, schema_view, form_class)
    _assert_no_defs_refs(form_def)

    form_def_name = _form_definition_name(form_class)
    prefix, namespace = _binding_namespace(schema_view)
    logger.info(f"Composing TD-level binding schema for {form_class} ({prefix}: {namespace})")
    return {
        "$schema": DRAFT_07,
        "anyOf": [{"$ref": td_schema_uri}],
        "definitions": {
            form_def_name: form_def,
            AFFORDANCE_DEF: _affordance_definition(form_def_name),
        },
        "type": "object",
        "properties": {
            "@context": _context_constraint(prefix, namespace),
            **{name: {"$ref": f"#/definitions/{AFFORDANCE_DEF}"} for name in AFFORDANCE_MAPS},
        },
    }
