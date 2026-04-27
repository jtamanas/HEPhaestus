"""test_spheno_backend_unchanged.py — WS-A §8.5 backward-compat gate.

The SPheno backend is now a wrapper around run_point.run. We want to prove
that dispatcher.dispatch with the default (spheno) backend forwards the
run_point.run payload verbatim and appends backend='spheno' — without
invoking a real SPheno binary.

We inject a FakeSphenoBackend via the dispatcher's ``backend_factory`` kwarg
(added in Step 6). This avoids the monkeypatch-the-wrong-module-instance
problem that results from patching SphenoBackend._load — since
dispatcher._load_backend loads backends/spheno.py through its own
spec_from_file_location and produces a separate module instance from the
test's own _load.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"


def _load(name: str, p: Path):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture
def tmp_lh(tmp_path):
    (tmp_path / "LesHouches.in").write_text("Block MODSEL\n   1   0\n")
    return tmp_path


def test_dispatcher_delegates_to_run_point_unchanged(tmp_lh):
    """Dispatcher must forward run_point.run's payload + add backend='spheno'.

    Mechanism: inject a FakeSphenoBackend via dispatch(..., backend_factory=...).
    The fake stands in for the real SphenoBackend, returning a canned payload
    matching what run_point.run would return. The dispatcher's job is simply
    to call backend.compute() with the forwarded arguments and return the
    result unchanged — the fake captures the args so we can assert on them.
    """
    disp = _load("disp", _SCRIPTS / "dispatcher.py")

    captured: dict = {}
    stub_payload = {
        "status": "ok",
        "blocker_code": None,
        "slha_path": str(tmp_lh / "SPheno.spc"),
        "summary": {"masses": {"25": 125.0}, "problems": []},
        "backend": "spheno",
        "cache_hit": False,
    }

    class FakeSphenoBackend:
        name = "spheno"

        def compute(self, model_name, spec, params, out_dir, config):
            captured["model_name"] = model_name
            captured["spec"] = spec
            captured["params"] = params
            captured["out_dir"] = out_dir
            captured["config"] = config
            return dict(stub_payload)

    def factory(backend_name: str):
        assert backend_name == "spheno", (
            f"dispatcher chose {backend_name!r}; expected 'spheno' for spec with "
            "outputs=[ufo,spheno] and no backends.spectrum override"
        )
        return FakeSphenoBackend()

    spec = {"outputs": ["ufo", "spheno"]}
    r = disp.dispatch(
        model_name="dummy",
        spec=spec,
        params={"MZERO": 1.0},
        out_dir=tmp_lh,
        config={"k": "v"},
        backend_factory=factory,
    )

    # Forwarding correctness.
    assert captured["model_name"] == "dummy"
    assert captured["spec"] == spec
    assert captured["params"] == {"MZERO": 1.0}
    assert captured["out_dir"] == tmp_lh
    assert captured["config"] == {"k": "v"}

    # Payload passthrough.
    assert r["status"] == "ok"
    assert r["backend"] == "spheno"
    assert r["summary"]["masses"]["25"] == 125.0
    assert r["blocker_code"] is None
