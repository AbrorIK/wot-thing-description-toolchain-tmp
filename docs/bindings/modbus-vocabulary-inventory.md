# Modbus Binding — Vocabulary Inventory and Discrepancy Report

**Status:** second iteration (Form vocabulary, Form JSON Schema, composed TD-level JSON Schema). Nothing here is approved by the Binding maintainers yet.
**Model:** [`resources/schemas/bindings/modbus.yaml`](../../resources/schemas/bindings/modbus.yaml)
**Generated** (`uv run wotis generate-binding-schema`):
- `resources/gens/bindings/modbus/form.schema.json` — the Modbus Form terms only, straight from LinkML;
- `resources/gens/bindings/modbus/modbus.schema.json` — a whole TD using them, same shape as the upstream `modbus.schema.json` (composed by `src/wotis/postprocessors/binding_jsonschema_postprocessor.py`).

**Tests:** [`tests/test_modbus_binding_schema.py`](../../tests/test_modbus_binding_schema.py) (Form samples in `tests/data/bindings/modbus/form/`) and [`tests/test_modbus_binding_td_schema.py`](../../tests/test_modbus_binding_td_schema.py) (complete-TD samples in `tests/data/bindings/modbus/td/`).

## Sources compared

| Source | Version | Role in reconciliation |
|---|---|---|
| Spec `bindings/protocols/modbus/index.template.html` (+ rendered `index.html`) | `w3c/wot-binding-templates@db1a256` (main, 2026-11-10) | Evidence of intended behavior. Note: the vocabulary tables are rendered from `ontology.ttl` + `mapping.ttl`, so only the prose, examples and mapping tables are independent of the ontology. |
| `modbus.schema.json` | main `@db1a256`, last changed in `ef16263` (#479); copied to [`resources/upstream/bindings/modbus/modbus.schema.json`](../../resources/upstream/bindings/modbus/modbus.schema.json) | Current validation baseline (what existing TDs were checked against). |
| `ontology.ttl` | main `@db1a256` | Existing semantic identifiers and ranges. |
| `context.jsonld` | main `@db1a256` | Existing JSON-LD term mappings. |
| `mapping.ttl` (SHACL) | main `@db1a256` | Existing RDF constraints and op-dependent defaults. |
| PR [w3c/wot-binding-templates#508](https://github.com/w3c/wot-binding-templates/pull/508) | head `7765ebd`, open; its `modbus.schema.json` copied to [`resources/upstream/bindings/modbus/modbus.schema.pr508.json`](../../resources/upstream/bindings/modbus/modbus.schema.pr508.json) | Fixes in progress; the proposals below follow it where it applies. Baseline for the composed TD-level schema: same verdict on every TD sample, same structure apart from descriptions and list order. Refresh the copy if the PR changes before merge. |

No source automatically overrides another. Where they conflict, the model follows the spec prose and ontology, and the conflict is listed below with its status.

## Form terms

The JSON key is what a TD contains. The ontology IRI is what the term means in RDF. The model keeps both: `alias` = JSON key, `slot_uri` = IRI.

| JSON key | LinkML slot | Ontology IRI | Spec type / assignment | Published schema | `context.jsonld` (main) | Ontology range | Model (generated) |
|---|---|---|---|---|---|---|---|
| `modv:pollingTime` | `pollingTime` | `modv:hasPollingTime` | integer, optional | number ≥ 0 | `xsd:integer` | `xsd:unsignedInt` | integer ≥ 0 (D-01, D-02) |
| `modv:timeout` | `timeout` | `modv:hasTimeout` | integer, optional, default "infinite" | number ≥ 0 | `xsd:integer` | `xsd:unsignedInt` | integer ≥ 0 (D-01, D-02) |
| `modv:mostSignificantByte` | `mostSignificantByte` | `modv:hasMostSignificantByte` | boolean, optional, default true | boolean | `xsd:boolean` | `xsd:boolean` | boolean |
| `modv:mostSignificantWord` | `mostSignificantWord` | `modv:hasMostSignificantWord` | boolean, optional, default true | boolean | `xsd:boolean` | `xsd:boolean` | boolean |
| `modv:zeroBasedAddressing` | `zeroBasedAddressing` | `modv:hasZeroBasedAddressingFlag` | boolean, optional, default false, deprecated | boolean + `$comment` | `xsd:boolean` | `xsd:boolean` | boolean, `deprecated` (D-18) |
| `modv:type` | `payloadDataType` | `modv:hasPayloadDataType` | PayloadDataType, optional | 15 `xsd:*` strings | `@vocab` | `modv:PayloadDataType` | 15 `xsd:*` strings (D-07, D-08) |
| `modv:entity` | `entity` | `modv:hasEntity` | Entity, optional | 4 strings | `@vocab` | `modv:Entity` | 4 strings, `meaning` = `modv:*` (D-05) |
| `modv:function` | `function` | `modv:hasFunction` | Function, optional | 9 strings | `@vocab` | `modv:Function` | 10 strings, `meaning` = `modv:*` (D-03) |

## URL terms

Carried in `href` (`modbus+tcp://{host}:{port}/{unitID}/{address}?quantity={quantity}`), not as Form keys. Modeled as slots in the `url_terms` subset and deliberately not attached to `ModbusForm`, so they do not appear in the Form JSON Schema (D-10).

| Term in spec table | Ontology IRI | Spec assignment | `context.jsonld` (main) | Ontology range | SHACL | Model |
|---|---|---|---|---|---|---|
| `modv:address` | `modv:hasAddress` | required | `xsd:integer` | `xsd:unsignedShort` | `xsd:integer`, minCount 1 | `unsignedShort`, required |
| `modv:unitID` | `modv:hasUnitID` | required | `xsd:integer` | `xsd:unsignedByte` | `xsd:integer`, minCount 1 | `unsignedByte`, required |
| `modv:quantity` | `modv:hasQuantity` | optional, default 1 | `xsd:integer` | `xsd:unsignedShort` | `xsd:integer` | `unsignedShort` |

## Enumerations

| Enum | Spec / ontology | Published schema | `context.jsonld` (main) | Model |
|---|---|---|---|---|
| Entity | Coil, DiscreteInput, HoldingRegister, InputRegister | same | same, IRIs correct | same |
| Function | 10 values incl. `readDeviceIdentification` (code 43) | 9, no `readDeviceIdentification` | wrong IRIs `modv:ReadCoil`…, `readHoldingRegister`/`writeMultipleHoldingRegister` singular, no `readDeviceIdentification` | 10 values, `meaning` = ontology individual, `code_number` annotation |
| PayloadDataType | 15 XML Schema datatypes | 15, written `xsd:int` etc. | none (PR #508 adds bare `int`, `integer`… terms) | 15, written `xsd:int` etc. |

## Discrepancies

Categories follow the policy agreed for this migration: *formatting* (ignore), *generator compatibility* (configure/adapt), *semantic mismatch* (fix with approval), *validation mismatch* (document, request decision), *specification ambiguity* (raise issue, do not invent), *missing generator capability* (customize or document exception).

| ID | Category | Finding | Model choice | Compatibility | Status |
|---|---|---|---|---|---|
| D-01 | validation mismatch | `pollingTime`, `timeout`: spec says "integer of milliseconds", ontology `xsd:unsignedInt`, published schema accepts any number ≥ 0. | `integer`, `minimum: 0` (same as PR #508). | **Narrowing:** `1.5` was valid, now rejected. Covered by `polling-time-fractional.json`, `timeout-fractional.json`. | Proposed — PR #508 |
| D-02 | validation mismatch | Ontology `xsd:unsignedInt` implies a maximum of 4294967295; no schema states it. | No maximum added. | None. | Open question |
| D-03 | validation mismatch | `readDeviceIdentification` is in the spec table and ontology, but not in the schema enum. | Included. | **Widening:** only accepts more. Covered by `read-device-identification.json`. | Proposed — PR #508 |
| D-04 | semantic mismatch | JSON key `modv:pollingTime` vs IRI `modv:hasPollingTime` (same for every term). With the prefix-only `@context` used in the spec examples, `modv:pollingTime` expands to `modv#pollingTime`, which the ontology does not define. Only loading `context.jsonld` gives `hasPollingTime`, and then the TD key would be `pollingTime`, not `modv:pollingTime`. | Both names recorded (`alias` + `slot_uri`); JSON Schema follows the published keys. | Depends on decision. | Open — discussed in PR #508 (relu91, sebastiankb) |
| D-05 | semantic mismatch | Enum values serialize as plain strings (`"Coil"`), so RDF gets a literal, not `modv:Coil`, unless the binding context is loaded. | `meaning: modv:Coil` etc. on every value, so the context generator can map them. | None for JSON Schema. | Open — PR #508 |
| D-06 | semantic mismatch | `context.jsonld` (main) maps Function values to non-existent IRIs (`modv:ReadCoil`, singular forms) and lacks `readDeviceIdentification`. | Meanings taken from the ontology individuals. | Context only. | Fixed in PR #508 |
| D-07 | semantic mismatch | The context term `type` → `hasPayloadDataType` collides with the TD `type` term on Forms; it expands to `hctl:hintsAtMediaType` (Mahda, PR #508 review). | Slot named `payloadDataType`; JSON key stays `modv:type`. A LinkML slot `type` also already exists in `jsonschema.yaml`. | Renaming the JSON key would be breaking. | Open — needs WG decision |
| D-08 | specification ambiguity | Values written `xsd:int` in spec and schema; PR #508 context adds bare terms (`int`, `integer`), implying TDs may write `"int"`. | Keeps `xsd:*` only. `"int"` rejected (`type-without-xsd-prefix.json`). | None today. | Open |
| D-09 | semantic mismatch | Namespace written without `#` in the published schema's `@context` check and the spec's full-TD example; the ontology uses `…/modbus#`. The published check also does not require `modv`. | `modv: https://www.w3.org/2019/wot/modbus#`; the composed schema takes it from the `modv` prefix and requires `modv` in an `@context` object, as PR #508 does (decided 2026-11-18). | **Narrowing vs published main:** TDs whose `@context` omits `modv`, declares it without `#`, or is a single string are rejected (`td/invalid/context-*.json`). Identical to PR #508. | Proposed — PR #508; namespace URI itself still under discussion |
| D-10 | specification ambiguity | `address`, `unitID`, `quantity`: the spec puts them in `href`; the SHACL requires `hasAddress`/`hasUnitID` on every Form (minCount 1); the context defines them as terms; the PR #508 playground example uses them as Form keys. | URL terms only, not Form keys. | None (published schema doesn't list them). | Open |
| D-11 | specification ambiguity | Spec examples: `"modv:function": "writeCoil"` (not a defined value), missing comma after `"modv:type": "xsd:int"`, trailing commas in `op` arrays. | `writeCoil` rejected (`function-write-coil.json`). | None. | To report |
| D-12 | semantic mismatch | SHACL default-mapping shapes use `sh:path modv:Function` (the class, not `modv:hasFunction`) and are named `…ModubsPropertyForm`; the rendered "Default mappings" table therefore shows `"modv:Function"`. | Not modeled yet. | Docs/SHACL only. | To report |
| D-13 | specification ambiguity | `zeroBasedAddressing` description: "the first coil/register can be either referred to as true or false" — presumably 0 or 1. | Copied verbatim. | None. | To report |
| D-14 | specification ambiguity | `writeSingleHoldingRegister` described as "(internal bits)", but holding registers are 16-bit. | Copied verbatim. | None. | To report |
| D-15 | formatting | Double spaces in Entity descriptions. | Normalized (same as PR #508). | None. | Done |
| D-16 | semantic mismatch | Ontology individual `excWriteMultipleHoldiungRegisters` (typo in an IRI). | Exception functions not modeled yet. | IRI change. | Fixed in PR #508 |
| D-17 | specification ambiguity | Spec: `modv:entity` "can be used in multi-operation forms whereas `modv:function` cannot". No schema enforces this. | Not enforced. Candidate for a LinkML `rules` constraint. | Would be narrowing. | Open |
| D-18 | generator compatibility | Generated schema is draft 2019-09 with `$defs` and `$id: https://www.w3.org/2019/wot/modbus`; published is draft-07 with `definitions` and no `$id`. LinkML `deprecated` is not emitted, so `zeroBasedAddressing` has no `$comment`. | `form.schema.json` left as generated. `modbus.schema.json` is draft-07 with `definitions`, inline enums, no `$id`, and `deprecated` emitted as `$comment` (known-linkml-gaps #13). | None. | Resolved for the TD-level schema |
| D-19 | missing generator capability | `gen-jsonld-context` fails (`ValueError: too many values to unpack`) on slots whose `alias` contains a colon (`modv:pollingTime`). | Not needed for JSON Schema. | Blocks context generation. | Next phase — workaround or upstream LinkML issue |
| D-20 | specification ambiguity | Op-dependent `modv:function` defaults (readproperty → readCoil, writeproperty/invokeaction → writeSingleCoil, read*/write*properties → *HoldingRegisters) and the `entity`-over-`function` precedence are Consumer rules, not field constraints. | Fixed defaults stored as `spec_default`; precedence as a class comment; op-dependent defaults not modeled yet. | None. | Next phase |

## Regenerating

```bash
uv run wotis generate-binding-schema
uv run pytest tests/test_modbus_binding_schema.py tests/test_modbus_binding_td_schema.py -v
```

`test_published_verdict_preserved` runs every Form sample against the published (main) schema and the generated one. A sample may only get a different verdict if it is listed in `PROPOSED_BEHAVIOR_CHANGES` with its D-number; when upstream aligns, the entry becomes stale and the test fails until it is removed.

`test_pr508_verdict_preserved` runs every complete-TD sample against the PR #508 schema and the composed one; they must agree on all of them. The TD 1.1 schema they reference is resolved offline from `resources/upstream/schemas/td11-json-schema-validation.json`.

The composed schema does not require a `modbus+tcp` href (hrefs may be relative to `base`, as in the spec's ModbusPLC example) and does not require any `modv:*` term in a Form; neither does upstream.
