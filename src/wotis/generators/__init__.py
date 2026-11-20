import json
import logging
import shutil

from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.utils.schemaview import SchemaView

from ..config import ProjectConfig
from ..postprocessors.jsonschema_postprocessor import post_process_jsonschema
from ..postprocessors.shacl_postprocessor import post_process_shacl
from .visualization import generate_visualizations
from .respec import generate_respec_spec


def _resource_outputs(config: ProjectConfig) -> dict[str, Path]:
    """LinkML generator name -> file it writes. A generator without an output is skipped."""
    outputs = {
        "jsonschema": config.outputs.jsonschema,
        "shacl": config.outputs.shacl,
        "jsonldcontext": config.outputs.context,
        "owl": config.outputs.owl,
        "linkml": config.outputs.linkml,
    }
    return {name: path for name, path in outputs.items() if path is not None}


def _run_linkml_generator(schema_view: SchemaView, generator: str, output_file: Path, root: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if generator == 'jsonschema':
        logging.info("Proceeding with LinkML to JSON Schema conversion")
        json_schema_generator = JsonSchemaGenerator(
            schema_view.schema,
            mergeimports=True,
            top_class='Thing',
            not_closed=True,
            include_null=False,
            preserve_names=True,
        )
        raw_schema = json.loads(json_schema_generator.serialize())
        processed_schema = post_process_jsonschema(raw_schema, schema_view)
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(processed_schema, f, indent=2, ensure_ascii=False)
        logging.info(f"JSON Schema saved to {output_file}")

    elif generator == 'shacl':
        logging.info("Proceeding with LinkML to SHACL conversion")
        shacl_generator = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix='Shape')
        raw_shacl = shacl_generator.serialize()
        processed_shacl = post_process_shacl(raw_shacl, schema_view)
        output_file.write_text(processed_shacl, encoding='utf-8')
        logging.info(f"SHACL shapes saved to {output_file}")

    elif generator == 'owl':
        logging.info("Proceeding with LinkML to OWL conversion")
        owl_generator = OwlSchemaGenerator(schema_view.schema)
        output_file.write_text(owl_generator.serialize())
        logging.info(f"OWL ontology saved to {output_file}")

    elif generator == 'jsonldcontext':
        logging.info("Proceeding with LinkML to JSON-LD Context conversion")
        context_generator = ContextGenerator(schema_view.schema, mergeimports=True)
        output_file.write_text(context_generator.serialize())
        logging.info(f"JSON-LD context saved to {output_file}")

    elif generator == 'linkml':
        logging.info("Proceeding with LinkML to LinkML YAML conversion (merged)")
        linkml_generator = LinkmlGenerator(schema_view.schema, mergeimports=True, format='yaml')
        merged = linkml_generator.serialize()
        # LinkML records the absolute schema path; keep it relative to the project so the
        # file is the same on every machine.
        source = Path(schema_view.schema.source_file)
        if source.is_absolute() and source.is_relative_to(root):
            merged = merged.replace(f"source_file: {source}\n", f"source_file: {source.relative_to(root)}\n", 1)
        output_file.write_text(merged)
        logging.info(f"Merged LinkML schema saved to {output_file}")

    else:
        logging.warning(f"Unknown generator: {generator}")


def run_pipeline(config: ProjectConfig, *, generate_docs: bool = False) -> None:
    """Generate every output listed in *config*; with *generate_docs* also the HTML spec."""
    schema_view = SchemaView(config.schema, merge_imports=True)
    logging.info(f"Input schema {config.schema} loaded successfully!")

    for generator, output_file in _resource_outputs(config).items():
        logging.info(f"Proceeding with WoT resource generation for {generator}")
        _run_linkml_generator(schema_view, generator, output_file, config.root)

    generate_visualizations(config.schema.parent, config.outputs.diagrams)

    if generate_docs:
        if config.static_figures is not None:
            shutil.copytree(config.static_figures, config.outputs.diagrams, dirs_exist_ok=True)
        logging.info("Starting ReSpec specification generation...")
        generate_respec_spec(config)
        logging.info("ReSpec specification generation complete.")
