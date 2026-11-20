"""Project configuration read from the ``[tool.wotis]`` table of a ``pyproject.toml``.

A repository that uses wotis (this one, or w3c/wot-thing-description) says where its
inputs are and where the generated files go, for example::

    [tool.wotis]
    schema = "schemas/thing_description.yaml"
    template = "index.template.html"

    [tool.wotis.sections]
    sec-core-vocabulary-definition = "schemas/thing_description.yaml"

    [tool.wotis.outputs]
    jsonschema = "generated/td-json-schema-validation.json"
    ...

Every path is relative to the folder that holds the ``pyproject.toml``, so the result
does not depend on the directory wotis is started from.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Optional


class ConfigError(ValueError):
    """The ``[tool.wotis]`` table is missing, incomplete or has unknown keys."""


@dataclass(frozen=True)
class Outputs:
    """Where each generated file is written."""

    jsonschema: Path
    context: Path
    shacl: Path
    owl: Path
    diagrams: Path
    spec: Path
    assertions: Path
    linkml: Optional[Path] = None  # merged LinkML schema; skipped when not set


@dataclass(frozen=True)
class ProjectConfig:
    """Inputs and outputs of one wotis project, all as absolute paths."""

    root: Path
    schema: Path
    template: Path
    sections: dict[str, Path]  # spec section id -> LinkML schema rendered into it, in spec order
    outputs: Outputs
    snippets: Optional[Path] = None
    glossary: Optional[Path] = None
    static_figures: Optional[Path] = None  # hand-drawn figures copied next to the spec
    extra_asserts: Optional[Path] = None
    tm_schema: Optional[Path] = None  # JSON Schema that TM snippets are validated against


def _required(cls) -> set[str]:
    return {f.name for f in fields(cls) if f.default is not None and f.name != "root"}


def _optional(cls) -> set[str]:
    return {f.name for f in fields(cls) if f.default is None}


def _check_keys(table: dict[str, Any], cls, where: str, nested: set[str] = frozenset()) -> None:
    keys = set(table) - nested
    missing = _required(cls) - nested - keys
    unknown = keys - _required(cls) - _optional(cls)
    if missing:
        raise ConfigError(f"{where} is missing required keys: {', '.join(sorted(missing))}")
    if unknown:
        raise ConfigError(f"{where} has unknown keys: {', '.join(sorted(unknown))}")


def _path(root: Path, value: Any, key: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"[tool.wotis] {key} must be a non-empty path string, got {value!r}")
    return (root / value).resolve()


def load_config(pyproject: Path = Path("pyproject.toml")) -> ProjectConfig:
    """Read ``[tool.wotis]`` from *pyproject* and resolve its paths against the file's folder."""
    pyproject = Path(pyproject).resolve()
    if not pyproject.is_file():
        raise ConfigError(f"{pyproject} not found")
    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    table = data.get("tool", {}).get("wotis")
    if table is None:
        raise ConfigError(f"{pyproject} has no [tool.wotis] table")

    root = pyproject.parent
    _check_keys(table, ProjectConfig, "[tool.wotis]", nested={"sections", "outputs"})

    sections = table.get("sections")
    if not isinstance(sections, dict) or not sections:
        raise ConfigError("[tool.wotis.sections] must map at least one spec section id to a schema file")

    outputs = table.get("outputs")
    if not isinstance(outputs, dict):
        raise ConfigError("[tool.wotis.outputs] is missing")
    _check_keys(outputs, Outputs, "[tool.wotis.outputs]")

    flat = {k: v for k, v in table.items() if k not in ("sections", "outputs")}
    return ProjectConfig(
        root=root,
        sections={sid: _path(root, p, f"sections.{sid}") for sid, p in sections.items()},
        outputs=Outputs(**{k: _path(root, v, f"outputs.{k}") for k, v in outputs.items()}),
        **{k: _path(root, v, k) for k, v in flat.items()},
    )
