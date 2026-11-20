"""Generate the JSON Schemas of a WoT protocol binding vocabulary (pilot: Modbus).

Two schemas come from the same LinkML model:

- the Form schema, generated directly by LinkML: only the binding-specific Form terms;
- the TD-level schema, composed from it by the binding postprocessor: the binding Form
  applied to every Form of a Thing Description, in the shape of the W3C binding schemas.
"""
import json
import logging

from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime.utils.schemaview import SchemaView

from ..postprocessors.binding_jsonschema_postprocessor import compose_binding_td_schema


def generate_binding_form_schema(schema_path: Path, form_class: str) -> dict:
    """Return the JSON Schema for ``form_class`` in the binding LinkML schema at ``schema_path``.

    Form name-value pairs keep their prefixed JSON names (e.g. ``modv:pollingTime``)
    through the LinkML ``alias`` of each slot.
    """
    generator = JsonSchemaGenerator(
        str(schema_path),
        top_class=form_class,
        not_closed=True,
        include_null=False,
        preserve_names=True,
    )
    return json.loads(generator.serialize())


def generate_binding_td_schema(schema_path: Path, form_class: str, td_schema_uri: str) -> dict:
    """Return the draft-07 schema validating a whole TD whose Forms may use the binding terms."""
    form_schema = generate_binding_form_schema(schema_path, form_class)
    return compose_binding_td_schema(form_schema, SchemaView(str(schema_path)), form_class, td_schema_uri)


def _write_json(document: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(document, f, indent=2, ensure_ascii=False)
        f.write('\n')
    logging.info(f"Binding JSON Schema saved to {output_path}")


def write_binding_schemas(schema_path: Path, form_class: str, td_schema_uri: str, output_dir: Path) -> None:
    """Write ``form.schema.json`` and ``<schema name>.schema.json`` into ``output_dir``."""
    _write_json(generate_binding_form_schema(schema_path, form_class), output_dir / 'form.schema.json')
    _write_json(
        generate_binding_td_schema(schema_path, form_class, td_schema_uri),
        output_dir / f'{schema_path.stem}.schema.json',
    )
