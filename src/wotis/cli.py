import click
import logging
import sys
import yaml

from dataclasses import replace
from pathlib import Path

from wotis.config import ConfigError, load_config
from wotis.generators import run_pipeline


config_option = click.option('-c', '--config',
                             type=click.Path(path_type=Path, dir_okay=False),
                             default=Path("pyproject.toml"),
                             show_default=True,
                             help="pyproject.toml whose [tool.wotis] table lists inputs and outputs.")
input_option = click.option('-i', '--input_schema',
                            type=click.Path(path_type=Path, dir_okay=False),
                            default=None,
                            help="Root LinkML schema. Overrides [tool.wotis] schema.")
docs_option = click.option('-d',
                             '--generate_docs',
                             type=bool,
                             is_flag=True,
                             default=False,
                             show_default=True,
                             help="Boolean for generating the final TD Respec-based HTML specification.")
assertions_csv_option = click.option('--assertions-csv',
                             type=click.Path(path_type=Path, dir_okay=False),
                             default=None,
                             help="Where to write the assertion inventory CSV. "
                                  "Overrides [tool.wotis.outputs] assertions.")
extra_asserts_option = click.option('--extra-asserts',
                             type=click.Path(path_type=Path, dir_okay=False, exists=False),
                             default=None,
                             help="extra-asserts.html with additional testing assertions to merge "
                                  "into the assertion inventory. Overrides [tool.wotis] extra_asserts.")


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
@config_option
@input_option
@docs_option
@assertions_csv_option
@extra_asserts_option
def generate_wot_resources(config: Path, input_schema: Path | None, generate_docs: bool,
                           assertions_csv: Path | None, extra_asserts: Path | None):
    """
    Generating WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema)
    and the final Respec specification from LinkML schemas.
    """
    try:
        project = load_config(config)
    except ConfigError as e:
        logging.error(f"Invalid wotis configuration: {e}")
        sys.exit(1)

    # Command-line options win over [tool.wotis]; relative paths are taken from the current directory.
    if input_schema is not None:
        project = replace(project, schema=input_schema.resolve())
    if extra_asserts is not None:
        project = replace(project, extra_asserts=extra_asserts.resolve())
    if assertions_csv is not None:
        project = replace(project, outputs=replace(project.outputs, assertions=assertions_csv.resolve()))

    if not project.schema.exists():
        raise FileNotFoundError(f"Cannot find input LinkML schema file {project.schema}.")

    try:
        run_pipeline(project, generate_docs=generate_docs)
    except yaml.YAMLError as e:
        logging.error(f"LinkML schema validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred during resource generation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
