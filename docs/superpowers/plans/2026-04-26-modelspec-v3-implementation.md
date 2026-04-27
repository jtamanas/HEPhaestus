# ModelSpec v3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python-only model-spec validator + SARAH renderer for BSM/EFT model authoring, verified against four SARAH goldens (singlet_doublet, dark_su3, 2hdm_a, SSM), with the SM template and three BSM ports as acceptance fixtures.

**Architecture:** Single phase. No backward compatibility with v1. Three-stage pure-Python validator (schema/refs/physics), renderer for `<Name>.m` + `parameters.m` + `particles.m`, copy-paste SM template, four BSM ports.

**Tech Stack:** Python 3.11+, `pyyaml`, `jsonschema`, `pytest`. No Mathematica subprocess.

**Source of truth:** `docs/superpowers/specs/2026-04-26-model-agnostic-modelspec-design.md`. Read it first.

**Implementation root:** `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/` (new directory; v1's `_shared/modelspec.schema.json` is deleted in Task 23).

---

## Task 1: Directory + reserved-name module

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/__init__.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/reserved.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/__init__.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_reserved.py`

- [ ] **Step 1: Write the failing test** (`tests/test_reserved.py`)

```python
from modelspec_v3 import reserved

def test_mathematica_builtins_contains_core():
    for name in ['I', 'E', 'D', 'Pi', 'Sum', 'If', 'Sqrt', 'Mass']:
        assert name in reserved.MATHEMATICA_BUILTINS

def test_sarah_reserved_contains_directives():
    for name in ['Casimir', 'Dynkin', 'LagHC', 'LagNoHC', 'GaugeES', 'EWSB',
                'DEFINITION', 'AddHC', 'conj', 'RealScalars']:
        assert name in reserved.SARAH_RESERVED

def test_single_letters_complete():
    assert len(reserved.SINGLE_LETTERS) == 52  # a-z + A-Z
    assert 'a' in reserved.SINGLE_LETTERS and 'Z' in reserved.SINGLE_LETTERS

def test_renderer_aliases():
    assert reserved.RENDERER_ALIASES == {'eEM': 'e'}

def test_lambda_with_brackets_not_reserved():
    # \[Lambda] is allowed as a parameter name; bare 'Lambda' is reserved
    assert 'Lambda' in reserved.SARAH_RESERVED
    assert '\\[Lambda]' not in reserved.SARAH_RESERVED

def test_is_reserved_helper():
    assert reserved.is_reserved('Sum')
    assert reserved.is_reserved('a')
    assert not reserved.is_reserved('eEM')   # alias, not reserved itself
    assert not reserved.is_reserved('Yu')
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_reserved.py -v`
Expected: ImportError (module not yet created).

- [ ] **Step 3: Implement `reserved.py`**

```python
"""Reserved-name registries for ModelSpec v3."""

MATHEMATICA_BUILTINS = frozenset({
    'I', 'E', 'D', 'N', 'O', 'K', 'C', 'Pi', 'True', 'False', 'Null',
    'Sum', 'If', 'Sin', 'Cos', 'Tan', 'Sqrt', 'Exp', 'Log', 'Abs', 'Sign',
    'Re', 'Im', 'List', 'Times', 'Plus', 'Power', 'Module', 'Block',
    'Function', 'Rule', 'RuleDelayed', 'Set', 'SetDelayed', 'Equal',
    'Unequal', 'Greater', 'Less', 'And', 'Or', 'Not', 'Derivative',
    'Integrate', 'Solve', 'Simplify', 'Mass', 'Width', 'Conjugate',
})

SARAH_RESERVED = frozenset({
    'Casimir', 'Dynkin', 'Delta', 'Eps', 'epsTensor', 'KroneckerDelta',
    'Lam', 'Lambda', 'f',
    'Gauge', 'Global', 'FermionFields', 'ScalarFields', 'RealScalars',
    'Model',
    'LagHC', 'LagNoHC', 'LagrangianInput', 'MatterSector', 'DiracSpinors',
    'GaugeSector', 'VEVs', 'Phases',
    'Description', 'LaTeX', 'OutputName', 'PDG', 'LesHouches', 'Automatic',
    'FeynArtsNr', 'ElectricCharge', 'Goldstone', 'Real',
    'DependenceNum', 'Dependence', 'DependenceSPheno',
    'ParameterDefinitions', 'ParticleDefinitions',
    'WeylFermionAndIndermediate',
    'NameOfStates', 'GaugeES', 'EWSB', 'DEFINITION', 'AddHC', 'conj',
})

SINGLE_LETTERS = frozenset(
    [chr(c) for c in range(ord('a'), ord('z') + 1)]
    + [chr(c) for c in range(ord('A'), ord('Z') + 1)]
)

RENDERER_ALIASES = {'eEM': 'e'}


def is_reserved(name: str) -> bool:
    """True if `name` cannot be used as a declared identifier."""
    if name in RENDERER_ALIASES:
        return False  # alias source is allowed
    return (
        name in MATHEMATICA_BUILTINS
        or name in SARAH_RESERVED
        or name in SINGLE_LETTERS
    )
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_reserved.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/
git commit -m "modelspec-v3: reserved-name registries + tests"
```

---

## Task 2: JSONSchema (top-level shape)

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_schema.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/fixtures/minimal_valid.yaml`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/fixtures/missing_required.yaml`

- [ ] **Step 1: Write `minimal_valid.yaml`** — smallest spec that validates: empty fermions/scalars/parameters, just enough to pass schema.

```yaml
model:
  name: TestModel
  latex: '\text{Test}'
  authors: 'tester'
  date: '2026-04-26'
gauge_groups:
  - { symbol: B, type: U(1), label: hypercharge, coupling: g1, ssb: false }
global_symmetries: []
fermions: []
scalars: []
parameters:
  - { name: g1, real: true }
lagrangian: { hc: [], no_hc: [] }
ewsb:
  vevs: []
  gauge_sector: []
  mixing_sector: []
  phases: []
  dirac_spinors_pre_ewsb: []
  dirac_spinors_post_ewsb: []
particles:
  gauge_es: []
  ewsb: []
  weyl_intermediate: []
```

- [ ] **Step 2: Write `missing_required.yaml`** — same as above but with `model:` block omitted entirely.

- [ ] **Step 3: Write the failing test**

```python
import json
import yaml
import jsonschema
import pathlib

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / 'schema.json'
FIX_DIR = pathlib.Path(__file__).parent / 'fixtures'

def load_schema():
    return json.loads(SCHEMA_PATH.read_text())

def test_minimal_valid_passes():
    schema = load_schema()
    spec = yaml.safe_load((FIX_DIR / 'minimal_valid.yaml').read_text())
    jsonschema.validate(spec, schema)  # raises if invalid

def test_missing_required_fails():
    schema = load_schema()
    spec = yaml.safe_load((FIX_DIR / 'missing_required.yaml').read_text())
    with pytest.raises(jsonschema.ValidationError) as ei:
        jsonschema.validate(spec, schema)
    assert 'model' in str(ei.value)

def test_unknown_top_level_key_fails():
    schema = load_schema()
    spec = yaml.safe_load((FIX_DIR / 'minimal_valid.yaml').read_text())
    spec['frobnicate'] = True   # unknown key
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(spec, schema)
```

- [ ] **Step 4: Implement the JSONSchema**

Write `schema.json` per the design spec's schema tables. Top-level `additionalProperties: false`. Sketch:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["model", "gauge_groups", "global_symmetries", "fermions",
               "scalars", "parameters", "lagrangian", "ewsb", "particles"],
  "properties": {
    "model": { "$ref": "#/$defs/Model" },
    "gauge_groups": { "type": "array", "minItems": 1,
                      "items": { "$ref": "#/$defs/GaugeGroup" } },
    "global_symmetries": { "type": "array",
                            "items": { "$ref": "#/$defs/GlobalSym" } },
    "fermions": { "type": "array", "items": { "$ref": "#/$defs/Fermion" } },
    "scalars": { "type": "array", "items": { "$ref": "#/$defs/Scalar" } },
    "parameters": { "type": "array", "items": { "$ref": "#/$defs/Param" } },
    "lagrangian": { "$ref": "#/$defs/Lagrangian" },
    "ewsb": { "$ref": "#/$defs/EWSB" },
    "particles": { "$ref": "#/$defs/Particles" },
    "sarah_raw": { "type": "string", "default": "" }
  },
  "$defs": {
    "Model": { ... },
    "GaugeGroup": { ... },
    ... // see design spec for shapes
  }
}
```

Use the design spec's tables verbatim for each `$defs` entry. `additionalProperties: false` everywhere. `Charge` type as `{"oneOf": [{"type": "integer"}, {"type": "number"}, {"type": "string"}]}`. Mass as `{"oneOf": [{"const": "Automatic"}, {"const": "LesHouches"}, {"type": "integer"}, {"type": "array", "items": {"type": "integer"}}]}`. Spinor components as `{"type": "array", "items": {"oneOf": [{"type": "string"}, {"const": 0}]}}`.

- [ ] **Step 5: Run tests, verify pass**

Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/
git commit -m "modelspec-v3: JSONSchema with closed top-level + minimal fixtures"
```

---

## Task 3: YAML loader

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/loader.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_loader.py`

- [ ] **Step 1: Write the failing test**

```python
from modelspec_v3.loader import load_spec, SpecLoadError
import pathlib

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_load_minimal():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    assert spec['model']['name'] == 'TestModel'

def test_load_nonexistent_raises():
    with pytest.raises(SpecLoadError):
        load_spec(FIX / 'nope.yaml')

def test_load_malformed_yaml_raises():
    bad = FIX / 'malformed.yaml'
    bad.write_text('model: {name: foo')
    with pytest.raises(SpecLoadError):
        load_spec(bad)
```

- [ ] **Step 2: Implement `loader.py`**

```python
"""YAML loader for ModelSpec v3."""
import pathlib
import yaml


class SpecLoadError(Exception):
    """Failed to load a spec file."""


def load_spec(path: pathlib.Path | str) -> dict:
    p = pathlib.Path(path)
    if not p.is_file():
        raise SpecLoadError(f"spec file not found: {p}")
    try:
        with p.open() as fh:
            return yaml.safe_load(fh) or {}
    except yaml.YAMLError as e:
        raise SpecLoadError(f"YAML parse error in {p}: {e}") from e
```

- [ ] **Step 3: Run tests + commit**

```bash
pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_loader.py -v
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/loader.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_loader.py
git commit -m "modelspec-v3: YAML loader with explicit error type"
```

---

## Task 4: Stage 1 validator (schema)

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/diagnostics.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/stage1.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_stage1.py`

- [ ] **Step 1: Write `diagnostics.py`** — the diagnostic dataclass

```python
"""Validator diagnostics."""
from dataclasses import dataclass
from typing import Literal, Optional

Severity = Literal['error', 'warning']


@dataclass(frozen=True)
class Diagnostic:
    stage: int                      # 1, 2, or 3
    severity: Severity
    code: str                       # e.g. 'SCHEMA_TYPE', 'REF_UNDECLARED'
    path: str                       # JSONPointer
    message: str
    hint: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'stage': self.stage, 'severity': self.severity,
            'code': self.code, 'path': self.path,
            'message': self.message, 'hint': self.hint,
        }
```

- [ ] **Step 2: Write the failing test**

```python
from modelspec_v3.stage1 import validate_schema
from modelspec_v3.loader import load_spec
import pathlib

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_minimal_valid_clean():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    diags = validate_schema(spec)
    assert diags == []

def test_missing_model_blocks():
    spec = load_spec(FIX / 'missing_required.yaml')
    diags = validate_schema(spec)
    assert len(diags) >= 1
    assert all(d.severity == 'error' for d in diags)
    assert all(d.stage == 1 for d in diags)
    assert any('model' in d.path or 'model' in d.message for d in diags)

def test_unknown_key_blocks():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    spec['extra'] = 'oops'
    diags = validate_schema(spec)
    assert any('extra' in d.message for d in diags)
```

- [ ] **Step 3: Implement `stage1.py`**

```python
"""Stage 1: JSONSchema validation."""
import json
import pathlib
import jsonschema
from typing import List
from .diagnostics import Diagnostic

_SCHEMA_PATH = pathlib.Path(__file__).parent / 'schema.json'
_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(_SCHEMA_PATH.read_text())
    return _SCHEMA


def _path_to_pointer(path) -> str:
    return '/' + '/'.join(str(p) for p in path) if path else '/'


def validate_schema(spec: dict) -> List[Diagnostic]:
    diags = []
    validator = jsonschema.Draft202012Validator(_schema())
    for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.path)):
        diags.append(Diagnostic(
            stage=1,
            severity='error',
            code='SCHEMA_' + err.validator.upper(),
            path=_path_to_pointer(err.path),
            message=err.message,
        ))
    return diags
```

- [ ] **Step 4: Run + commit**

```bash
pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_stage1.py -v
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/{diagnostics,stage1}.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_stage1.py
git commit -m "modelspec-v3: Stage 1 schema validator"
```

---

## Task 5: Mathematica tokenizer

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tokenizer.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_tokenizer.py`

- [ ] **Step 1: Write the failing test**

```python
from modelspec_v3.tokenizer import tokenize, extract_identifiers, Token

def test_simple_identifiers():
    toks = tokenize('Yd conj[H].d.q')
    types = [t.kind for t in toks]
    assert 'IDENT' in types
    idents = [t.value for t in toks if t.kind == 'IDENT']
    assert 'Yd' in idents and 'conj' in idents and 'H' in idents
    assert 'd' in idents and 'q' in idents

def test_named_symbol():
    toks = tokenize('-1/2 \\[Lambda] conj[H].H.conj[H].H')
    named = [t.value for t in toks if t.kind == 'NAMED_SYM']
    assert '\\[Lambda]' in named

def test_sum_brackets():
    toks = tokenize('Sum[yL[i,a] phi[a] LL[i].NL, {i,1,3}, {a,1,3}]')
    idents = [t.value for t in toks if t.kind == 'IDENT']
    assert 'Sum' in idents and 'yL' in idents and 'phi' in idents

def test_extract_identifiers_skips_reserved():
    # Sum, conj, Mass should be filtered out
    ids = extract_identifiers('Sum[Yu[i,j] H.u.q, {i,1,3}, {j,1,3}]')
    assert 'Yu' in ids
    assert 'H' in ids and 'u' in ids and 'q' in ids
    assert 'Sum' not in ids and 'i' not in ids and 'j' not in ids

def test_extract_identifies_imaginary_unit():
    ids = extract_identifiers('\\[ImaginaryI] ychi a0.ChiR.ChiL')
    assert '\\[ImaginaryI]' not in ids   # builtin, filtered
    assert 'ychi' in ids and 'a0' in ids
```

- [ ] **Step 2: Implement the tokenizer**

```python
"""Mathematica tokenizer for Lagrangian terms."""
import re
from dataclasses import dataclass
from typing import List, Set
from .reserved import MATHEMATICA_BUILTINS, SARAH_RESERVED

@dataclass(frozen=True)
class Token:
    kind: str   # NAMED_SYM, IDENT, INT, OP, BRACKET, BRACE, COMMA, DOT
    value: str
    pos: int

# \[LetterRuns]   first; this must precede plain IDENT
_NAMED_SYM_RE = re.compile(r'\\\[([A-Za-z]+)\]')
_IDENT_RE     = re.compile(r'[A-Za-z][A-Za-z0-9]*')
_INT_RE       = re.compile(r'\d+')
_OP_RE        = re.compile(r'[+\-*/]')
_DOT          = '.'
_WS           = re.compile(r'\s+')

# Skip-set for extract_identifiers: reserved tokens that are NOT field/param refs
_EXTRACTION_SKIP: Set[str] = MATHEMATICA_BUILTINS | {
    'conj',   # SARAH lower-case conj wrapper
}


def tokenize(s: str) -> List[Token]:
    out, i = [], 0
    while i < len(s):
        if (m := _WS.match(s, i)):
            i = m.end(); continue
        if (m := _NAMED_SYM_RE.match(s, i)):
            out.append(Token('NAMED_SYM', m.group(0), i)); i = m.end(); continue
        if (m := _IDENT_RE.match(s, i)):
            out.append(Token('IDENT', m.group(0), i)); i = m.end(); continue
        if (m := _INT_RE.match(s, i)):
            out.append(Token('INT', m.group(0), i)); i = m.end(); continue
        c = s[i]
        if c in '+-*/':
            out.append(Token('OP', c, i)); i += 1; continue
        if c in '[]':
            out.append(Token('BRACKET', c, i)); i += 1; continue
        if c in '{}':
            out.append(Token('BRACE', c, i)); i += 1; continue
        if c == ',':
            out.append(Token('COMMA', c, i)); i += 1; continue
        if c == '.':
            out.append(Token('DOT', c, i)); i += 1; continue
        raise SyntaxError(f'unexpected char {c!r} at pos {i} in {s!r}')
    return out


def extract_identifiers(s: str) -> Set[str]:
    """Return field/parameter identifiers in `s`, with reserved names removed."""
    out = set()
    toks = tokenize(s)
    for j, t in enumerate(toks):
        if t.kind == 'NAMED_SYM':
            if t.value not in _EXTRACTION_SKIP:
                out.add(t.value)
        elif t.kind == 'IDENT':
            if t.value in _EXTRACTION_SKIP:
                continue
            # Skip Sum/If iteration variables: identifiers inside `{ident, ...}`
            # immediately following a comma at depth-1 brace are iterators.
            # Cheap heuristic: skip 1- or 2-letter idents that appear inside braces.
            # (More precise: track brace depth; for now use heuristic.)
            out.add(t.value)
    # Drop iterator-looking single-letter names (i, j, k, n) inside `{...}`.
    # Conservative: inspect raw braces in source.
    out -= _detect_brace_iterators(s)
    return out


def _detect_brace_iterators(s: str) -> Set[str]:
    """Identify Mathematica iteration variables in `{var, lo, hi}` constructs."""
    iters = set()
    for m in re.finditer(r'\{\s*([A-Za-z][A-Za-z0-9]*)\s*,\s*\d', s):
        iters.add(m.group(1))
    return iters
```

- [ ] **Step 3: Run + commit**

Tests pass. Commit:

```bash
pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_tokenizer.py -v
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tokenizer.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_tokenizer.py
git commit -m "modelspec-v3: Mathematica tokenizer + identifier extractor"
```

---

## Task 6: Canonical Weyl Table builder

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/cwt.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_cwt.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/fixtures/sm_minimal.yaml`

- [ ] **Step 1: Write `sm_minimal.yaml`** — SM gauge groups + 5 fermion entries + Higgs scalar; no parameters/lagrangian/ewsb beyond what schema requires.

- [ ] **Step 2: Write the failing test**

```python
from modelspec_v3.cwt import build_cwt, WeylRef, FieldRef
from modelspec_v3.loader import load_spec
import pathlib

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_sm_cwt_has_quark_components():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    # bare and indexed forms
    for sym in ['uL', 'dL', 'eL', 'vL', 'dR', 'uR', 'eR']:
        assert sym in cwt
        for g in [1, 2, 3]:
            assert f'{sym}[{g}]' in cwt

def test_sm_cwt_marks_conjugates():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    # 'd' is declared with components 'conj[dR]' → CWT entry for dR is conjugated
    assert cwt['dR'].conjugated is True
    assert cwt['uL'].conjugated is False

def test_cwt_has_field_aliases():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    assert isinstance(cwt['q'], FieldRef)
    assert isinstance(cwt['LL'], FieldRef)

def test_cwt_seeds_gauge_bosons():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    for tok in ['VB', 'VWB[1]', 'VWB[2]', 'VWB[3]', 'VWp', 'VG', 'VP', 'VZ']:
        assert tok in cwt
```

- [ ] **Step 3: Implement `cwt.py`**

```python
"""Canonical Weyl Table — the symbol resolution source of truth."""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WeylRef:
    field_name: str
    gen: Optional[int]
    component: str
    conjugated: bool


@dataclass(frozen=True)
class FieldRef:
    field_name: str


_CONJ_RE = re.compile(r'^conj\[([A-Za-z][A-Za-z0-9]*)\]$')

_GAUGE_BUILTIN = ('VB', 'VWB[1]', 'VWB[2]', 'VWB[3]', 'VWp', 'VG', 'VP', 'VZ')


def build_cwt(spec: dict) -> dict:
    cwt: dict = {}
    for f in spec.get('fermions', []):
        _add_field(cwt, f, is_scalar=False)
    for s in spec.get('scalars', []):
        _add_field(cwt, s, is_scalar=True)
    for tok in _GAUGE_BUILTIN:
        cwt[tok] = WeylRef(field_name='__builtin__', gen=None,
                            component=tok, conjugated=False)
    return cwt


def _add_field(cwt: dict, f: dict, *, is_scalar: bool):
    name = f['name']
    gens = f['generations']
    raw = f['components']

    is_conj = isinstance(raw, str) and (m := _CONJ_RE.match(raw))
    if is_conj:
        components = [is_conj.group(1)]   # the inner symbol
        conjugated = True
    else:
        components = [raw] if isinstance(raw, str) else list(raw)
        conjugated = False

    for comp in components:
        for g in range(1, gens + 1):
            cwt[f'{comp}[{g}]'] = WeylRef(name, g, comp, conjugated)
        cwt[comp] = WeylRef(name, None, comp, conjugated)
    cwt[name] = FieldRef(name)
```

- [ ] **Step 4: Run + commit**

```bash
pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_cwt.py -v
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/cwt.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_cwt.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/fixtures/sm_minimal.yaml
git commit -m "modelspec-v3: Canonical Weyl Table builder"
```

---

## Task 7: Stage 2 — refs + reserved-name checks

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/stage2.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_stage2.py`
- Create: `tests/fixtures/typo_in_mixing.yaml`, `tests/fixtures/reserved_param.yaml`

- [ ] **Step 1: Write fixtures**
- `typo_in_mixing.yaml`: SM-derived spec with `mixing_sector.lh: [dr]` (lowercase typo for `dL`).
- `reserved_param.yaml`: SM with parameter `e` (reserved single-letter; user should have used `eEM`).

- [ ] **Step 2: Write the failing test**

```python
from modelspec_v3.stage2 import validate_refs
from modelspec_v3.loader import load_spec
import pathlib

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_sm_minimal_clean():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    diags = validate_refs(spec)
    assert [d for d in diags if d.severity == 'error'] == []

def test_undeclared_weyl_in_mixing_blocks():
    spec = load_spec(FIX / 'typo_in_mixing.yaml')
    diags = validate_refs(spec)
    errs = [d for d in diags if d.severity == 'error']
    assert any('REF_UNDECLARED' in d.code for d in errs)
    assert any('dr' in d.message for d in errs)
    # hint should mention dL (Levenshtein-nearest)
    assert any(d.hint and 'dL' in d.hint for d in errs)

def test_reserved_parameter_name():
    spec = load_spec(FIX / 'reserved_param.yaml')
    diags = validate_refs(spec)
    errs = [d for d in diags if d.code == 'NAME_RESERVED']
    assert len(errs) >= 1
    assert any("'e'" in d.message for d in errs)

def test_collision_two_fermions_same_name():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['fermions'].append({**spec['fermions'][0]})  # duplicate first entry
    diags = validate_refs(spec)
    errs = [d for d in diags if d.code == 'NAME_COLLISION']
    assert len(errs) >= 1
```

- [ ] **Step 3: Implement `stage2.py`**

```python
"""Stage 2: ref integrity + reserved names + canonical Weyl table."""
from typing import List, Set
from .diagnostics import Diagnostic
from .reserved import is_reserved
from .cwt import build_cwt, FieldRef
from .tokenizer import extract_identifiers


def validate_refs(spec: dict) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    cwt = build_cwt(spec)
    declared_params: Set[str] = {p['name'] for p in spec.get('parameters', [])}

    # 1. Reserved-name + collision checks for declared names
    diags.extend(_check_reserved_and_collision(spec))

    # 2. Ref checks: every Weyl reference in EWSB blocks must resolve
    diags.extend(_check_ewsb_refs(spec, cwt))

    # 3. Lagrangian term symbol-extraction → cross-check against CWT ∪ params
    diags.extend(_check_lagrangian_refs(spec, cwt, declared_params))

    return diags


def _check_reserved_and_collision(spec) -> List[Diagnostic]:
    seen: dict = {}   # name -> path where first declared
    diags = []
    for collection_path, items, key in [
        ('parameters', spec.get('parameters', []), 'name'),
        ('fermions', spec.get('fermions', []), 'name'),
        ('scalars', spec.get('scalars', []), 'name'),
        ('gauge_groups', spec.get('gauge_groups', []), 'symbol'),
        ('global_symmetries', spec.get('global_symmetries', []), 'name'),
    ]:
        for i, it in enumerate(items):
            name = it.get(key)
            if name is None:
                continue
            path = f'/{collection_path}/{i}/{key}'
            if is_reserved(name):
                diags.append(Diagnostic(
                    stage=2, severity='error', code='NAME_RESERVED',
                    path=path,
                    message=f"name {name!r} is reserved",
                ))
            elif name in seen:
                diags.append(Diagnostic(
                    stage=2, severity='error', code='NAME_COLLISION',
                    path=path,
                    message=f"name {name!r} already declared at {seen[name]}",
                ))
            else:
                seen[name] = path
    return diags


def _check_ewsb_refs(spec, cwt) -> List[Diagnostic]:
    diags = []
    ewsb = spec.get('ewsb', {})
    # vevs[].component, .vev[0], .goldstone[0], .physical[0]
    for i, v in enumerate(ewsb.get('vevs', [])):
        for slot in ('component',):
            sym = v.get(slot)
            if sym is None or sym == 0:
                continue
            if sym not in cwt:
                diags.append(_undeclared_diag(f'/ewsb/vevs/{i}/{slot}', sym, cwt))
    # mixing_sector.weyls/lh/rh
    for i, m in enumerate(ewsb.get('mixing_sector', [])):
        kind = m.get('kind')
        if kind in ('majorana', 'scalar'):
            for j, w in enumerate(m.get('weyls', [])):
                if w not in cwt:
                    diags.append(_undeclared_diag(
                        f'/ewsb/mixing_sector/{i}/weyls/{j}', w, cwt))
        elif kind == 'dirac':
            for slot in ('lh', 'rh'):
                for j, w in enumerate(m.get(slot, [])):
                    if w == 0 or w in cwt:
                        continue
                    # also accept conj[X] strings whose inner X is in cwt
                    if w.startswith('conj[') and w[5:-1] in cwt:
                        continue
                    diags.append(_undeclared_diag(
                        f'/ewsb/mixing_sector/{i}/{slot}/{j}', w, cwt))
    # dirac_spinors_pre_ewsb / dirac_spinors_post_ewsb
    for block in ('dirac_spinors_pre_ewsb', 'dirac_spinors_post_ewsb'):
        for i, sp in enumerate(ewsb.get(block, [])):
            for j, c in enumerate(sp.get('components', [])):
                if c == 0:
                    continue
                if c.startswith('conj[') and c[5:-1] in cwt:
                    continue
                if c not in cwt:
                    diags.append(_undeclared_diag(
                        f'/ewsb/{block}/{i}/components/{j}', c, cwt))
    return diags


def _check_lagrangian_refs(spec, cwt, params) -> List[Diagnostic]:
    diags = []
    for bucket in ('hc', 'no_hc'):
        for i, t in enumerate(spec.get('lagrangian', {}).get(bucket, [])):
            term = t.get('term', '')
            for ident in extract_identifiers(term):
                if ident in cwt or ident in params:
                    continue
                diags.append(Diagnostic(
                    stage=2, severity='error', code='REF_UNDECLARED',
                    path=f'/lagrangian/{bucket}/{i}/term',
                    message=f"undeclared symbol {ident!r} in term",
                    hint=_levenshtein_hint(ident, cwt, params),
                ))
    return diags


def _undeclared_diag(path, sym, cwt) -> Diagnostic:
    return Diagnostic(
        stage=2, severity='error', code='REF_UNDECLARED',
        path=path,
        message=f"undeclared Weyl symbol {sym!r}",
        hint=_levenshtein_hint(sym, cwt, set()),
    )


def _levenshtein_hint(s, cwt, params) -> str | None:
    candidates = [k for k in (set(cwt) | params)
                  if isinstance(k, str) and '[' not in k]
    if not candidates:
        return None
    scored = sorted(candidates, key=lambda c: _lev(s, c))[:3]
    return f"did you mean: {', '.join(scored)}?"


def _lev(a: str, b: str) -> int:
    """Iterative Levenshtein."""
    if a == b: return 0
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j-1] + 1,
                        prev + (0 if a[i-1] == b[j-1] else 1))
            prev = cur
    return dp[n]
```

- [ ] **Step 4: Run + commit**

```bash
pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_stage2.py -v
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/stage2.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_stage2.py \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/fixtures/typo_in_mixing.yaml \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/fixtures/reserved_param.yaml
git commit -m "modelspec-v3: Stage 2 ref/reserved-name validation"
```

---

## Task 8: Stage 3 — anomaly cancellation

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/anomaly.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/charge_eval.py` (sandboxed `If[]` evaluator)
- Create: `tests/test_anomaly.py`

- [ ] **Step 1: Write `charge_eval.py`** — sandboxed evaluator for `If[A==g, ...]` reps

```python
"""Sandboxed evaluator for expression-valued charges in `reps:`."""
import re
from fractions import Fraction
from typing import Union

ChargeValue = Union[int, Fraction]


class ChargeEvalError(Exception):
    pass


# Recognises: integer literal, fraction `a/b`, `If[<cond>, <then>, <else>]`
# where <cond> is `A == n` or `A != n` etc.
_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<frac>-?\d+/\d+)"
    r"|(?P<int>-?\d+)"
    r"|(?P<ident>[A-Za-z][A-Za-z0-9]*)"
    r"|(?P<op>==|!=|<=|>=|<|>|[+\-*/(),\[\]])"
    r")"
)


def evaluate(expr, A_value: int) -> ChargeValue | None:
    """Evaluate `expr` with substitution A=A_value. Returns None for symbolic.

    `expr` may be: int, str (numeric, fraction, or `If[]`-form expression).
    """
    if isinstance(expr, int):
        return expr
    if isinstance(expr, (Fraction,)):
        return expr
    if not isinstance(expr, str):
        return None
    s = expr.strip()
    if '/' in s and re.fullmatch(r'-?\d+/\d+', s):
        n, d = s.split('/'); return Fraction(int(n), int(d))
    if re.fullmatch(r'-?\d+', s):
        return int(s)
    # Generic: tokenize and eval
    return _eval_tokens(s, A_value)


def _eval_tokens(s: str, A: int):
    """Recursive descent over a tiny grammar. Returns None on bare symbol."""
    # ... (full impl — about 80 lines; key cases: If[cond, then, else], int, A)
    raise NotImplementedError("expand the recursive descent parser")
```

(Full implementation should support `If[A==1, X, Y]`, `If[A==1, X, If[A==2, Y, Z]]`, integer arithmetic, and return `None` for bare param symbols like `qChi`.)

- [ ] **Step 2: Write the failing tests** (anomaly check)

```python
from modelspec_v3.anomaly import check_anomalies
from modelspec_v3.loader import load_spec
import pathlib

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_sm_cubic_y_anomaly_cancels():
    spec = load_spec(FIX / 'sm_minimal.yaml')   # SM has full content for anomaly
    diags = check_anomalies(spec)
    # SM cancels on all four anomaly types
    errs_or_warns = [d for d in diags if d.code.startswith('ANOMALY_')]
    assert errs_or_warns == []   # silent

def test_z2_lmu_le_anomaly_cancels_with_expression_reps():
    spec = load_spec(FIX / 'u1_lmu_le.yaml')   # WIMP-1 sketch
    diags = check_anomalies(spec)
    # Le-Lμ within leptons cancels by construction
    assert [d for d in diags if d.code.startswith('ANOMALY_')] == []

def test_artificial_anomaly_warns():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    # corrupt a fermion's Y charge by a small amount
    spec['fermions'][0]['reps']['B'] = '1/7'
    diags = check_anomalies(spec)
    warns = [d for d in diags if d.severity == 'warning']
    assert any('ANOMALY' in d.code for d in warns)

def test_dirac_partner_excluded_from_anomaly():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    diags = check_anomalies(spec)
    # PsiDd / PsiDu form a vectorlike pair; their net contribution is zero,
    # but only because of the dirac_partner annotation. Without it, this would
    # warn. With it, silent.
    assert [d for d in diags if 'PsiD' in (d.message or '')] == []

def test_sarah_raw_with_two_u1s_emits_kinmix_warning():
    spec = load_spec(FIX / 'kinmix_toy.yaml')
    diags = check_anomalies(spec)
    assert any(d.code == 'ANOMALY_KINMIX_SKIP' for d in diags)
```

- [ ] **Step 3: Implement `anomaly.py`** per design spec — anomaly formulas, vectorlike exclusion, kinetic-mixing skip warning. Approximately 200 lines.

- [ ] **Step 4: Run + commit**

---

## Task 9: Stage 3 — per-term U(1) charge conservation + discrete-symmetry conservation

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/per_term.py`
- Create: `tests/test_per_term.py`

- [ ] **Step 1: Write the failing test**

```python
def test_sm_yukawas_balance():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    diags = check_per_term_charges(spec)
    assert [d for d in diags if d.severity == 'warning'] == []

def test_charge_violating_term_warns():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['hc'].append({'term': 'Yextra H.q.q'})  # charge-violating
    diags = check_per_term_charges(spec)
    assert any(d.code == 'CHARGE_NONZERO' for d in diags)

def test_dmparity_violating_term_warns():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    # add Yukawa connecting Z2-odd FS to Z2-even q (DMParity-violating)
    spec['lagrangian']['hc'].append({'term': 'Ybad FS conj[H].d.q'})
    diags = check_discrete_symmetry(spec)
    assert any(d.code == 'DISCRETE_NONZERO' for d in diags)
```

- [ ] **Step 2: Implement** — extract identifiers per term via tokenizer, look up `reps[<u1>]` per leaf via CWT, sum. Same algorithm for discrete symmetries (mod-N for Z_n).

- [ ] **Step 3: Run + commit**

---

## Task 10: Validator orchestrator

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/validate.py`
- Create: `tests/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
def test_three_stages_in_order():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    result = validate(spec)
    assert result.errors == []
    assert isinstance(result.warnings, list)

def test_stage1_errors_halt_pipeline():
    # If schema is broken, Stage 2/3 should not run (wasted work)
    spec = load_spec(FIX / 'missing_required.yaml')
    result = validate(spec)
    assert all(d.stage == 1 for d in result.errors)
```

- [ ] **Step 2: Implement**

```python
"""Validation orchestrator."""
from dataclasses import dataclass, field
from typing import List
from .diagnostics import Diagnostic
from .stage1 import validate_schema
from .stage2 import validate_refs
from .anomaly import check_anomalies
from .per_term import check_per_term_charges, check_discrete_symmetry


@dataclass
class ValidationResult:
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)

    @property
    def all(self) -> List[Diagnostic]:
        return self.errors + self.warnings


def validate(spec: dict) -> ValidationResult:
    res = ValidationResult()
    s1 = validate_schema(spec)
    res.errors.extend(s1)
    if s1:
        return res   # Stage 2/3 require valid schema
    s2 = validate_refs(spec)
    res.errors.extend(d for d in s2 if d.severity == 'error')
    if any(d.severity == 'error' for d in s2):
        return res
    res.warnings.extend(check_anomalies(spec))
    res.warnings.extend(check_per_term_charges(spec))
    res.warnings.extend(check_discrete_symmetry(spec))
    return res
```

- [ ] **Step 3: Run + commit**

---

## Task 11: Diagnostic emitters (JSON + pretty)

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/emit.py`
- Create: `tests/test_emit.py`

- [ ] **Step 1: Tests**

```python
def test_emit_json_round_trip():
    diag = Diagnostic(stage=1, severity='error', code='X', path='/y',
                      message='m', hint='h')
    line = emit_json([diag])
    parsed = [json.loads(l) for l in line.splitlines()]
    assert parsed[0] == diag.to_dict()

def test_emit_pretty_includes_severity_marker():
    diag = Diagnostic(stage=2, severity='warning', code='C', path='/p', message='m')
    text = emit_pretty([diag])
    assert 'warning' in text and 'C' in text and '/p' in text
```

- [ ] **Step 2: Implement** ~50 lines — `emit_json` writes one diag per line; `emit_pretty` writes coloured (or plain) tagged lines plus a summary count.

- [ ] **Step 3: Run + commit**

---

## Task 12: CLI

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Tests** (use `subprocess` against the entry point)

```python
def test_cli_validates_clean(tmp_path):
    fixture = pathlib.Path('tests/fixtures/sm_minimal.yaml')
    proc = subprocess.run(
        ['python', '-m', 'modelspec_v3.cli', 'validate', str(fixture)],
        capture_output=True, text=True)
    assert proc.returncode == 0
    assert 'OK' in proc.stdout or proc.stdout.strip() == ''

def test_cli_reports_errors_with_exit_2(tmp_path):
    fixture = pathlib.Path('tests/fixtures/missing_required.yaml')
    proc = subprocess.run(
        ['python', '-m', 'modelspec_v3.cli', 'validate', str(fixture)],
        capture_output=True, text=True)
    assert proc.returncode == 2
    assert 'error' in proc.stdout

def test_cli_warnings_exit_0_by_default(tmp_path):
    # if there are only warnings, exit 0
    proc = subprocess.run(
        ['python', '-m', 'modelspec_v3.cli', 'validate',
         'tests/fixtures/anomaly_warn.yaml'],
        capture_output=True, text=True)
    assert proc.returncode == 0   # warnings don't fail by default

def test_cli_strict_warns_become_errors():
    proc = subprocess.run(
        ['python', '-m', 'modelspec_v3.cli', 'validate', '--strict',
         'tests/fixtures/anomaly_warn.yaml'],
        capture_output=True, text=True)
    assert proc.returncode == 1   # warnings become errors with --strict

def test_cli_json_format():
    proc = subprocess.run(
        ['python', '-m', 'modelspec_v3.cli', 'validate', '--format=json',
         'tests/fixtures/missing_required.yaml'],
        capture_output=True, text=True)
    for line in proc.stdout.strip().splitlines():
        json.loads(line)   # each line must be valid JSON
```

- [ ] **Step 2: Implement**

```python
"""ModelSpec v3 CLI."""
import argparse
import sys
from .loader import load_spec, SpecLoadError
from .validate import validate
from .emit import emit_json, emit_pretty


def main(argv=None):
    p = argparse.ArgumentParser(prog='modelspec-v3')
    sub = p.add_subparsers(dest='cmd', required=True)

    v = sub.add_parser('validate')
    v.add_argument('path')
    v.add_argument('--format', choices=['pretty', 'json'], default='pretty')
    v.add_argument('--strict', action='store_true',
                    help='warnings become errors')

    args = p.parse_args(argv)

    if args.cmd == 'validate':
        try:
            spec = load_spec(args.path)
        except SpecLoadError as e:
            print(f'load error: {e}', file=sys.stderr)
            return 3
        result = validate(spec)

        out = (emit_json if args.format == 'json' else emit_pretty)(result.all)
        print(out)

        if result.errors:
            return 2
        if args.strict and result.warnings:
            return 1
        return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 3: Run + commit**

---

## Task 13: Renderer scaffolding

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/__init__.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/header.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/gauge.py`
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/_idioms.py` (shared helpers)
- Create: `tests/test_render_header.py`, `tests/test_render_gauge.py`

- [ ] **Step 1: Tests for header rendering**

```python
def test_render_model_header_basic():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_header(spec)
    assert 'Model`Name = "TestModel";' in out
    assert "Off[General::spell]" in out
    assert "NameOfStates = {GaugeES, EWSB};" in out

def test_render_model_header_with_globals():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_header(spec)
    assert 'Global[[1]] = {Z[2], DMParity};' in out

def test_render_lagrangian_input_block_emitted():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_header(spec)
    assert 'DEFINITION[GaugeES][LagrangianInput]' in out
    assert 'AddHC -> True' in out
    assert 'AddHC -> False' in out
```

- [ ] **Step 2: Tests for gauge rendering**

```python
def test_render_gauge_5tuple_no_globals():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_gauge(spec)
    assert 'Gauge[[1]] = {B, U[1], hypercharge, g1, False};' in out
    # 5-tuple — no trailing column

def test_render_gauge_6tuple_one_global():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_gauge(spec)
    # 6-tuple — trailing column for DMParity charge
    assert 'Gauge[[1]] = {B, U[1], hypercharge, g1, False, 1};' in out
```

- [ ] **Step 3: Implement** ~80 lines for header + ~60 for gauge.

- [ ] **Step 4: Run + commit**

---

## Task 14: Renderer — fermions + scalars

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/matter.py`
- Create: `tests/test_render_matter.py`

- [ ] **Step 1: Test against the singlet_doublet golden**

```python
GOLDEN = pathlib.Path('plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/singlet_doublet/SingletDoublet.m')

def test_sm_fermions_match_golden_lines():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_fermions(spec)
    expected = [
        'FermionFields[[1]] = {q, 3, {uL, dL}, 1/6, 2, 3, 1};',
        'FermionFields[[2]] = {LL, 3, {vL, eL}, -1/2, 2, 1, 1};',
        'FermionFields[[3]] = {d, 3, conj[dR], 1/3, 1, -3, 1};',
        'FermionFields[[4]] = {u, 3, conj[uR], -2/3, 1, -3, 1};',
        'FermionFields[[5]] = {e, 3, conj[eR], 1, 1, 1, 1};',
        'FermionFields[[6]] = {FS, 1, s0, 0, 1, 1, -1};',
        'FermionFields[[7]] = {PsiDd, 1, {PsiDd0, PsiDdm}, -1/2, 2, 1, -1};',
        'FermionFields[[8]] = {PsiDu, 1, {PsiDup, PsiDu0}, 1/2, 2, 1, -1};',
    ]
    for line in expected:
        assert line in out

def test_singleton_components_emit_bare():
    spec = load_spec(FIX / 'sm_real_singlet.yaml')   # real-scalar with components: [Sing]
    out = render_scalars(spec)
    # YAML had list `[Sing]`; renderer emits bare `Sing`
    assert '{s, 1, Sing,' in out

def test_realscalars_block_emitted():
    spec = load_spec(FIX / '2hdm_a_v3.yaml')
    out = render_scalars(spec)
    assert 'RealScalars = {a0};' in out
```

- [ ] **Step 2: Implement** ~120 lines.

- [ ] **Step 3: Run + commit**

---

## Task 15: Renderer — parameters.m

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/parameters.py`
- Create: `tests/test_render_parameters.py`

- [ ] **Step 1: Tests**

```python
GOLDEN_PARAMS = pathlib.Path(
    'plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/singlet_doublet/parameters.m')

def test_sm_gauge_params_match_golden():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_parameters_m(spec)
    assert '{g1,        { Description -> "Hypercharge-Coupling"}}' in out
    assert '{AlphaS,    { Description -> "Alpha Strong"}}' in out

def test_yukawa_dependence_num():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_parameters_m(spec)
    assert 'DependenceNum ->  Sqrt[2]/v* {{Mass[Fu,1],0,0}, {0, Mass[Fu,2],0}, {0, 0, Mass[Fu,3]}}' in out

def test_les_houches_indexed():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_parameters_m(spec)
    assert 'LesHouches -> {BSMPARAMS, 1}' in out
    # bare-symbol form
    assert 'LesHouches -> ZNMIX' in out

def test_eEM_renders_as_e():
    # Renderer aliases YAML name `eEM` to SARAH `e`
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_parameters_m(spec)
    assert '{e,         { Description -> "electric charge"}}' in out
    assert 'eEM' not in out
```

- [ ] **Step 2: Implement** ~150 lines.

- [ ] **Step 3: Run + commit**

---

## Task 16: Renderer — Lagrangian assembly

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/lagrangian.py`
- Create: `tests/test_render_lagrangian.py`

- [ ] **Step 1: Tests**

```python
def test_laghc_wraps_with_minus():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_lagrangian(spec)
    assert 'LagHC = -(Yd conj[H].d.q + Ye conj[H].e.LL + -Yu H.u.q);' in out

def test_lagnohc_no_wrap():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_lagrangian(spec)
    assert 'LagNoHC = -mu2 conj[H].H -1/2 \\[Lambda] conj[H].H.conj[H].H;' in out

def test_empty_buckets_emit_empty_strings():
    spec = load_spec(FIX / 'minimal_valid.yaml')   # both buckets empty
    out = render_lagrangian(spec)
    assert 'LagHC = ;' in out or 'LagHC =' not in out  # decision point
```

- [ ] **Step 2: Implement** ~40 lines.

- [ ] **Step 3: Run + commit**

---

## Task 17: Renderer — EWSB blocks

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/ewsb.py`
- Create: `tests/test_render_ewsb.py`

- [ ] **Step 1: Tests** for VEVs (with literal `[0,0]` Goldstone), GaugeSector, MatterSector (per-`stage` routing), Phases, DiracSpinors (literal int `0`).

```python
def test_real_scalar_vev_emits_zero_goldstone():
    spec = load_spec(FIX / 'ssm_v3.yaml')
    out = render_ewsb(spec)
    assert '{Sing, {vS, 1}, {0, 0}, {phiS, 1}}' in out

def test_majorana_mixing_singular_output():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_ewsb(spec)
    assert '{{s0, PsiDd0, PsiDu0}, {Chi, ZN}}' in out

def test_dirac_mixing_two_outputs():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    out = render_ewsb(spec)
    assert '{{{PsiDdm}, {PsiDup}}, {{ChiM, UM}, {ChiP, UP}}}' in out

def test_scalar_mixing_at_gauge_es_stage():
    # scotogenic: 3 real scalars mix at GaugeES (no VEV)
    spec = load_spec(FIX / 'scotogenic_v3.yaml')
    out = render_ewsb(spec)
    assert 'DEFINITION[GaugeES][MatterSector]' in out
    assert '{{phi1, phi2, phi3}, {phiM, Zphi}}' in out

def test_scalar_mixing_at_ewsb_stage():
    # SSM: hh1 + hh2 mix at EWSB after both VEVs
    spec = load_spec(FIX / 'ssm_v3.yaml')
    out = render_ewsb(spec)
    assert 'DEFINITION[EWSB][MatterSector]' in out
    assert '{{phiH, phiS}, {hh, ZH}}' in out

def test_dirac_spinors_zero_components():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_ewsb(spec)
    assert 'Fv -> {vL, 0}' in out
```

- [ ] **Step 2: Implement** ~150 lines.

- [ ] **Step 3: Run + commit**

---

## Task 18: Renderer — particles.m + auto-emission

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/particles.py`
- Create: `tests/test_render_particles.py`

- [ ] **Step 1: Tests**

```python
def test_auto_emit_gauge_bosons_and_ghosts():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_particles_m(spec)
    # Auto-emit: VB, gB, VWB, gWB, VG, gG
    for sym in ['VB', 'gB', 'VWB', 'gWB', 'VG', 'gG']:
        assert sym in out

def test_user_override_takes_precedence():
    # If user declares `{VB, {Description -> "Custom"}}`, use that not default
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['particles']['gauge_es'].append({
        'name': 'VB', 'description': 'Custom B-Boson',
    })
    out = render_particles_m(spec)
    assert 'Custom B-Boson' in out

def test_auto_emit_weyl_intermediate_from_cwt():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_particles_m(spec)
    for sym in ['dR', 'eR', 'uR', 'q', 'eL', 'dL', 'uL', 'vL']:
        assert sym in out

def test_dark_su3_emits_dark_gauge_boson():
    spec = load_spec(FIX / 'dark_su3_v3.yaml')
    out = render_particles_m(spec)
    assert 'VGD' in out and 'gGD' in out
```

- [ ] **Step 2: Implement** ~120 lines.

- [ ] **Step 3: Run + commit**

---

## Task 19: Render orchestrator + golden round-trip

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/__init__.py` (top-level)
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/orchestrator.py`
- Create: `tests/test_render_round_trip.py`

- [ ] **Step 1: Test that round-trips singlet_doublet to bytewise-similar** (smoke test, not byte-equivalent — just structural)

```python
def test_singlet_doublet_renders_all_three_files():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    files = render_all(spec)
    assert 'SingletDoublet.m' in files
    assert 'parameters.m' in files
    assert 'particles.m' in files

def test_singlet_doublet_main_m_contains_all_required_blocks():
    spec = load_spec(FIX / 'singlet_doublet_v3.yaml')
    files = render_all(spec)
    main = files['SingletDoublet.m']
    for required in [
        'Model`Name = "SingletDoublet";',
        'Global[[1]] = {Z[2], DMParity};',
        'NameOfStates = {GaugeES, EWSB};',
        'DEFINITION[GaugeES][LagrangianInput]',
        'Gauge[[1]] = {B, U[1], hypercharge, g1, False, 1};',
        'FermionFields[[1]] = {q, 3,',
        'ScalarFields[[1]] = {H, 1, {Hp, H0}',
        'LagNoHC =',
        'LagHC =',
        'DEFINITION[EWSB][MatterSector]',
        'DEFINITION[GaugeES][DiracSpinors]',
        'DEFINITION[EWSB][GaugeSector]',
        'DEFINITION[EWSB][VEVs]',
        'DEFINITION[EWSB][Phases]',
        'DEFINITION[EWSB][DiracSpinors]',
    ]:
        assert required in main, f'missing: {required}'
```

- [ ] **Step 2: Implement orchestrator** (~50 lines combining the section renderers)

- [ ] **Step 3: Run + commit**

---

## Task 20: Author SM template

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/sm.yaml`
- Create: `tests/test_sm_template.py`

- [ ] **Step 1: Test that the SM template validates clean and renders without error**

```python
SM_PATH = pathlib.Path(__file__).parent.parent / 'templates' / 'sm.yaml'

def test_sm_template_validates_clean():
    spec = load_spec(SM_PATH)
    result = validate(spec)
    assert result.errors == []
    assert result.warnings == []

def test_sm_template_renders():
    spec = load_spec(SM_PATH)
    files = render_all(spec)
    assert 'SM.m' in files
    main = files['SM.m']
    assert 'Model`Name = "SM"' in main
    assert 'NameOfStates = {GaugeES, EWSB};' in main
```

- [ ] **Step 2: Author the SM template** at `templates/sm.yaml` per the design spec's Section "verified against goldens." Use the iterated v2 SM template from the brainstorming session as the starting point, with all review-2 patches applied.

- [ ] **Step 3: Verify it renders, run tests, commit**

```bash
git add plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/sm.yaml \
        plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/tests/test_sm_template.py
git commit -m "modelspec-v3: SM template + acceptance test"
```

---

## Task 21: Port singlet_doublet to v3

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml`
- Update: `tests/test_render_round_trip.py` to confirm round-trip

- [ ] **Step 1: Write the spec** by hand. Start from `tests/fixtures/singlet_doublet_spec.yaml` (v1) and the singlet_doublet golden `.m`. Apply the v3 schema shape (mixing_sector with `kind: majorana | dirac`, expression-valued reps as needed, `dirac_partner: PsiDu / PsiDd`, etc.).

- [ ] **Step 2: Validate it; round-trip into the rendered .m; diff against the golden**

```bash
python -m modelspec_v3.cli validate plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml
python -m modelspec_v3.cli render plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml \
       --out /tmp/v3_render
diff -u /tmp/v3_render/SingletDoublet.m \
        plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/singlet_doublet/SingletDoublet.m | head -80
```

Acceptance: structural equivalence (same blocks, same content). Whitespace differences ok.

- [ ] **Step 3: Commit**

---

## Task 22: Port dark_su3 to v3

Same shape as Task 21. Start from `tests/fixtures/dark_su3_spec.yaml` and the dark_su3 golden `.m`. Validate, render, diff.

---

## Task 23: Port 2hdm_a to v3

Same. Stress-tests `kind: scalar` mixing with three Weyl symbols (Ah1, Ah2, a0), `RealScalars = {a0}`, scalar-only mixings, two complex doublets with VEVs.

---

## Task 24: Port SSM to v3 (real-scalar VEV verification)

**File:**
- Create: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/ssm.yaml`

- [ ] **Step 1: Author** the SSM spec, using `/Users/yianni/SARAH/SARAH-current/Models/SSM/SSM.m` as the target. This is the canonical real-scalar-with-VEV case (validates Q1 from brainstorming).

- [ ] **Step 2: Validate, render, diff against SARAH's published SSM.m**

This is the model-agnostic verification: if v3 can reproduce SARAH's official SSM (which we did not author), the schema is honest.

- [ ] **Step 3: Commit**

---

## Task 25: Delete v1 + update lagrangian-builder skill

**Files:**
- Delete: `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`
- Delete: `plugins/hep-ph-toolkit/skills/_shared/validate_one.py` (and tests)
- Delete: `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/{singlet_doublet,dark_su3,2hdm_a}_spec.yaml` (v1 specs)
- Delete: `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/ws1/` (v1 ws1 fixtures)
- Delete: `plugins/hep-ph-toolkit/skills/sarah-build/scripts/sections/sm_content.py`
- Delete: `plugins/hep-ph-toolkit/skills/sarah-build/scripts/sections/{gauge,parameters,ewsb,particles,matter,model_header,lagrangian}.py` (v1 renderer)
- Modify: `plugins/hep-ph-toolkit/skills/sarah-build/scripts/render_templates.py` — replace v1 entry point with a thin wrapper around `modelspec_v3.render.render_all`
- Modify: `plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py` — call `modelspec_v3.validate.validate` first
- Update: `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` — drop references to v1 schema; point at `modelspec_v3/templates/sm.yaml` and `specs/`
- Update: `plugins/hep-ph-toolkit/skills/lagrangian-builder/references/sarah-gotchas.md` — refresh to reflect v3 (no `kind: dark`, etc.)

- [ ] **Step 1: Identify all v1 entry points** and grep for callers

```bash
grep -rln "modelspec.schema.json\|validate_one\|sm_content" plugins/hep-ph-toolkit/
```

- [ ] **Step 2: Delete v1 files**

- [ ] **Step 3: Update sarah-build to use v3**

```python
# plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py (sketched)
from modelspec_v3.loader import load_spec
from modelspec_v3.validate import validate
from modelspec_v3.render import render_all

def build(spec_path: str, out_dir: str) -> None:
    spec = load_spec(spec_path)
    result = validate(spec)
    if result.errors:
        for d in result.errors:
            print(d)
        raise SystemExit(2)
    files = render_all(spec)
    for name, content in files.items():
        (pathlib.Path(out_dir) / name).write_text(content)
```

- [ ] **Step 4: Run the full sarah-build test suite** — all v1 fixtures should be gone; v3 ports replace them. The build pipeline against the v3 specs should produce equivalent SARAH `.m` files (verified in Tasks 21-24).

- [ ] **Step 5: Update the lagrangian-builder skill content** to reference v3 paths and conventions.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "modelspec-v3: delete v1, switch sarah-build to v3 backend"
```

---

## Acceptance criteria

The plan is done when all of the following hold:

1. `pytest plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/` passes (all unit tests).
2. `python -m modelspec_v3.cli validate templates/sm.yaml` exits 0 with no errors and no warnings.
3. The four ported BSM specs (singlet_doublet, dark_su3, 2hdm_a, ssm) all validate clean, render to `.m` files, and the rendered files structurally match the SARAH goldens (same SARAH directives, same ordering, content equivalent modulo whitespace).
4. `git grep -E "modelspec\.schema\.json|sm_content|validate_one"` returns no matches in `plugins/hep-ph-toolkit/`.
5. `git log` shows ~25 commits matching the task structure above.

## Notes for the implementer

- TDD throughout. Write the failing test, run it, implement, verify pass, commit. Frequent small commits.
- The Mathematica tokenizer (Task 5) and `charge_eval.py` (Task 8) are the hardest pieces. Allocate extra time and write extensive tests before implementing.
- `Sum[]` in Lagrangian terms is a v3 feature exercised by the scotogenic spec (not in the four ports). Test the tokenizer against it but don't author a scotogenic port in v1 — defer to a follow-up.
- The renderer's auto-emission rules (Task 18) are the biggest source of subtle bugs; cross-reference each emission against the four goldens line-by-line during implementation.
- All Python is pure-stdlib + pyyaml + jsonschema. No Mathematica subprocess. Validator runs in milliseconds even on the largest BSM spec.
- Diagnostics paths use JSONPointer (`/foo/0/bar`). Pretty-print rendering is line-based with severity prefix and code; no fancy formatting required.
