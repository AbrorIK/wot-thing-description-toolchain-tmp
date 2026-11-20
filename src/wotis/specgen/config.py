from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Dict

# The Jinja templates are part of the tool, not of the spec content, so they ship
# inside the wotis package and are found relative to it, wherever it is installed.
PACKAGE_TEMPLATES_DIR = Path(str(files("wotis") / "templates"))


@dataclass(frozen=True)
class Config:
    resources_path: Path
    jinja_templates: Path
    glossary_path: Path
    snippets_dir: Path
    placeholder: str
    section_schemas: Dict[str, Path]
    schema_prefixes: Dict[str, str]

    @classmethod
    def from_resources_dir(cls, resources: Path, placeholder: str = "%s") -> "Config":
        terms = resources / "xref"
        schema_dir = resources / "schemas"
        section_map = {
            "sec-core-vocabulary-definition": schema_dir / "thing_description.yaml",
            "sec-data-schema-vocabulary-definition": schema_dir / "jsonschema.yaml",
            "sec-security-vocabulary-definition": schema_dir / "wot_security.yaml",
            "sec-hypermedia-vocabulary-definition": schema_dir / "hypermedia.yaml",
        }
        schema_prefixes = {
            "thing_description": "td",
            "hypermedia": "hctl",
            "jsonschema": "jsonschema",
            "wot_security": "wotsec",
            "tm": "tm",
        }

        return cls(
            resources_path=resources,
            jinja_templates=PACKAGE_TEMPLATES_DIR,
            glossary_path=terms / "glossary.yaml",
            snippets_dir=resources / "snippets",
            placeholder=placeholder,
            section_schemas=section_map,
            schema_prefixes=schema_prefixes,
        )
