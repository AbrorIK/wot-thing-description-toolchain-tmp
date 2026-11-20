import click
import logging
import sys
import yaml

from pathlib import Path

from src.wotis import (YAML_SCHEMA_PATH, ASSERTION_PATH, EXTRA_ASSERTS_PATH,
                       BINDINGS_SCHEMA_PATH, BINDINGS_GENS_PATH, TD11_SCHEMA_URI)
from src.wotis.generators import run_pipeline
from src.wotis.generators.bindings import write_binding_schemas


input_option = click.option('-i', '--input_schema',
                            type=str,
                            show_default=True,
                            help="Path to the input schema specified as LinkML yaml.",
                            default=YAML_SCHEMA_PATH)
docs_option = click.option('-d',
                             '--generate_docs',
                             type=bool,
                             is_flag=True,
                             default=False,
                             show_default=True,
                             help="Boolean for generating the final TD Respec-based HTML specification.")
assertions_csv_option = click.option('--assertions-csv',
                             type=click.Path(path_type=Path, dir_okay=False),
                             default=ASSERTION_PATH,
                             show_default=True,
                             help="Path for the storing assertion inventory CSV. "
                                  "Defaults to resources/gens/assertions/assertions.csv.")
extra_asserts_option = click.option('--extra-asserts',
                             type=click.Path(path_type=Path, dir_okay=False, exists=False),
                             default=EXTRA_ASSERTS_PATH,
                             show_default=True,
                             help="Path to extra-asserts.html with additional testing assertions "
                                  "to merge into the assertion inventory.")


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose: int, quiet: bool):
    """CLI for WOTIS (Web of Things Integrated Schemas) toolchain.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)
    logger.info(f"Logger {logger.name} set to level {logger.level}")


@main.command()
@input_option
@docs_option
@assertions_csv_option
@extra_asserts_option
def generate_wot_resources(input_schema: str, generate_docs: bool, assertions_csv: Path, extra_asserts: Path):
    """
    Generating WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema)
    and the final Respec specification from LinkML schemas.
    """
    input_path = Path(input_schema)
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find input LinkML schema file {input_schema}.")

    try:
        run_pipeline(
            input_path,
            generate_docs=generate_docs,
            assertions_csv_path=assertions_csv,
            extra_asserts_path=extra_asserts,
        )
    except yaml.YAMLError as e:
        logging.error(f"LinkML schema validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred during resource generation: {e}", exc_info=True)
        sys.exit(1)


@main.command()
@click.option('-i', '--input_schema',
              type=click.Path(path_type=Path, dir_okay=False, exists=True),
              default=BINDINGS_SCHEMA_PATH / 'modbus.yaml',
              show_default=True,
              help="Path to the binding LinkML schema.")
@click.option('--form-class',
              default='ModbusForm',
              show_default=True,
              help="LinkML class holding the binding-specific Form terms.")
@click.option('--td-schema-uri',
              default=TD11_SCHEMA_URI,
              show_default=True,
              help="TD JSON Schema referenced through anyOf by the TD-level binding schema.")
@click.option('-o', '--output-dir',
              type=click.Path(path_type=Path, file_okay=False),
              default=None,
              help="Output directory. Defaults to resources/gens/bindings/<schema name>/.")
def generate_binding_schema(input_schema: Path, form_class: str, td_schema_uri: str, output_dir: Path | None):
    """
    Generating the JSON Schemas of a protocol binding (pilot: Modbus): form.schema.json for the
    binding Form terms and <schema name>.schema.json for a whole TD using them.
    """
    try:
        write_binding_schemas(input_schema, form_class, td_schema_uri,
                              output_dir or BINDINGS_GENS_PATH / input_schema.stem)
    except Exception as e:
        logging.error(f"Binding schema generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
