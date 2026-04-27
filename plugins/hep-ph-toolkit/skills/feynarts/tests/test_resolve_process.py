"""Tests for resolve_process.py."""
import json
from pathlib import Path

import pytest

from resolve_process import (
    ProcessResolutionError,
    resolve_process,
)


class TestRawForm:
    """Raw FeynArts tuple form (detected by leading '[')."""

    def test_raw_form_ee_mumu(self):
        result = resolve_process("[{F[2,{1}], -F[2,{1}]}, {F[2,{2}], -F[2,{2}]}]", model="SM")
        assert result["raw"] is True
        assert result["n_in"] == 2
        assert result["n_out"] == 2

    def test_raw_form_single_arrow(self):
        result = resolve_process("[{V[1]}, {F[2,{1}], -F[2,{1}]}]", model="SM")
        assert result["raw"] is True

    def test_raw_form_preserved(self):
        raw_str = "[{F[2,{1}], -F[2,{1}]}, {F[2,{2}], -F[2,{2}]}]"
        result = resolve_process(raw_str, model="SM")
        assert result["feynarts_tuple"] == raw_str


class TestAliasFormSM:
    """Alias form with SM table."""

    def test_ee_mumu(self, tables_dir):
        result = resolve_process("e+ e- -> mu+ mu-", model="SM", tables_dir=tables_dir)
        assert result["raw"] is False
        assert result["n_in"] == 2
        assert result["n_out"] == 2
        assert "-F[2, {1}]" in result["feynarts_tuple"] or "F[2" in result["feynarts_tuple"]

    def test_z_selfenergy(self, tables_dir):
        result = resolve_process("Z -> Z", model="SM", tables_dir=tables_dir)
        assert result["n_in"] == 1
        assert result["n_out"] == 1

    def test_unknown_particle_raises(self, tables_dir):
        with pytest.raises(ProcessResolutionError, match="unknown particle"):
            resolve_process("X -> Y", model="SM", tables_dir=tables_dir)


class TestAliasFormSMQCD:
    """Alias form with SMQCD table."""

    def test_gg_tt(self, tables_dir):
        result = resolve_process("g g -> t tbar", model="SMQCD", tables_dir=tables_dir)
        assert result["n_in"] == 2
        assert result["n_out"] == 2

    def test_gluon_alias(self, tables_dir):
        result = resolve_process("gluon gluon -> t tbar", model="SMQCD", tables_dir=tables_dir)
        assert result["n_in"] == 2


class TestAliasFormTHDM:
    """Alias form with THDM table."""

    def test_hh_to_bb(self, tables_dir):
        result = resolve_process("H -> b bbar", model="THDM", tables_dir=tables_dir)
        assert result["n_in"] == 1
        assert result["n_out"] == 2


class TestAliasFormMSSM:
    """Alias form with MSSM table."""

    def test_neutralino_pair(self, tables_dir):
        result = resolve_process("e+ e- -> N1 N2", model="MSSM", tables_dir=tables_dir)
        assert result["n_in"] == 2
        assert result["n_out"] == 2


class TestProcessSpec:
    """Processspec JSON output."""

    def test_processspec_fields(self, tables_dir):
        result = resolve_process("e+ e- -> mu+ mu-", model="SM", tables_dir=tables_dir)
        spec = result["processspec"]
        assert spec["schema_version"] == "processspec/v1"
        assert len(spec["particles"]["in"]) == 2
        assert len(spec["particles"]["out"]) == 2
        assert spec["loop_order"] == 0
        assert spec["kinematic_limit"] == "general"
        assert isinstance(spec["excludes"], list)

    def test_processspec_particle_labels(self, tables_dir):
        result = resolve_process("e+ e- -> mu+ mu-", model="SM", tables_dir=tables_dir)
        labels_in = [p["label"] for p in result["processspec"]["particles"]["in"]]
        labels_out = [p["label"] for p in result["processspec"]["particles"]["out"]]
        assert "e+" in labels_in
        assert "e-" in labels_in
        assert "mu+" in labels_out
        assert "mu-" in labels_out
