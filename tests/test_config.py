from pathlib import Path

import pytest

from wotis.config import ConfigError, load_config

REPO_ROOT = Path(__file__).resolve().parents[1]

MINIMAL = """
[tool.wotis]
schema = "schemas/td.yaml"
template = "index.template.html"

[tool.wotis.sections]
sec-core = "schemas/td.yaml"

[tool.wotis.outputs]
jsonschema = "out/schema.json"
context = "out/context.jsonld"
shacl = "out/shapes.ttl"
owl = "out/ontology.ttl"
diagrams = "out/figures"
spec = "out/index.html"
assertions = "out/assertions.csv"
"""


def _write(tmp_path: Path, text: str) -> Path:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(text, encoding="utf-8")
    return pyproject


def test_repo_config_points_at_existing_inputs():
    cfg = load_config(REPO_ROOT / "pyproject.toml")
    assert cfg.root == REPO_ROOT
    inputs = [cfg.schema, cfg.template, cfg.snippets, cfg.glossary,
              cfg.static_figures, cfg.extra_asserts, cfg.tm_schema, *cfg.sections.values()]
    missing = [p for p in inputs if not p.exists()]
    assert not missing, f"[tool.wotis] points at missing inputs: {missing}"
    assert list(cfg.sections)[0] == "sec-core-vocabulary-definition"
    assert cfg.outputs.spec == REPO_ROOT / "resources" / "gens" / "index.html"


def test_paths_are_relative_to_the_pyproject_not_the_cwd(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    pyproject = _write(project, MINIMAL)
    monkeypatch.chdir(tmp_path)

    cfg = load_config(pyproject)

    assert cfg.root == project.resolve()
    assert cfg.schema == project.resolve() / "schemas" / "td.yaml"
    assert cfg.sections == {"sec-core": project.resolve() / "schemas" / "td.yaml"}
    assert cfg.outputs.jsonschema == project.resolve() / "out" / "schema.json"


def test_optional_keys_default_to_none(tmp_path):
    cfg = load_config(_write(tmp_path, MINIMAL))
    assert cfg.snippets is None
    assert cfg.glossary is None
    assert cfg.tm_schema is None
    assert cfg.outputs.linkml is None


def test_missing_table(tmp_path):
    with pytest.raises(ConfigError, match=r"no \[tool.wotis\] table"):
        load_config(_write(tmp_path, '[project]\nname = "x"\n'))


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "pyproject.toml")


def test_missing_required_key(tmp_path):
    with pytest.raises(ConfigError, match="missing required keys: template"):
        load_config(_write(tmp_path, MINIMAL.replace('template = "index.template.html"\n', "")))


def test_missing_required_output(tmp_path):
    with pytest.raises(ConfigError, match=r"outputs\] is missing required keys: shacl"):
        load_config(_write(tmp_path, MINIMAL.replace('shacl = "out/shapes.ttl"\n', "")))


def test_unknown_key_is_rejected(tmp_path):
    # A typo must fail loudly instead of silently falling back to a default.
    with pytest.raises(ConfigError, match="unknown keys: snipets"):
        load_config(_write(tmp_path, MINIMAL.replace("[tool.wotis.sections]", 'snipets = "s"\n\n[tool.wotis.sections]')))


def test_sections_must_not_be_empty(tmp_path):
    with pytest.raises(ConfigError, match="sections"):
        load_config(_write(tmp_path, MINIMAL.replace('sec-core = "schemas/td.yaml"\n', "")))


def test_path_must_be_a_string(tmp_path):
    with pytest.raises(ConfigError, match="schema must be a non-empty path string"):
        load_config(_write(tmp_path, MINIMAL.replace('schema = "schemas/td.yaml"', "schema = 3")))
