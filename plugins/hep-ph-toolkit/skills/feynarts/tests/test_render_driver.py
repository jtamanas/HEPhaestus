"""Tests for render_driver.py.

Verifies that format-substitution produces expected text for tree-level
golden and also for loop-order 1, excludes, and different model sources.
"""
from pathlib import Path

import pytest

from render_driver import render_driver, render_make_feynarts_driver

# Expected output for tree-level e+e- -> mu+mu- golden
_TREE_EXPECTED = '''\
Needs["FeynArts`"];
SetDirectory["/tmp/test_run"];
t   = CreateTopologies[0, 2 -> 2, ExcludeTopologies -> {}];
ins = InsertFields[t, {{F[2,{1}], -F[2,{1}]}, {F[2,{2}], -F[2,{2}]}}, Model -> "SM", GenericModel -> "Lorentz"];
nDiag = Length[ins];
If[nDiag == 0,
  Print["FEYNARTS_EMPTY_RESULT"]; Exit[0]];
If[nDiag > 2000,
  Print["FEYNARTS_TOO_MANY_DIAGRAMS ", nDiag]; Exit[2]];
Paint[ins, ColumnsXRows -> Automatic, DisplayFunction -> (Export["diagrams.pdf", #] &)];
amp = CreateFeynAmp[ins];
Put[{{"schema_version" -> 1, "feynarts_version" -> "3.11",
     "model_hash" -> "abc123", "amp" -> amp}}, "FeynAmpList.m"];
Print["FEYNARTS_OK ", nDiag];
Exit[0];
'''


class TestRenderDriver:
    def test_tree_level_golden(self):
        result = render_driver(
            run_dir="/tmp/test_run",
            loop_order=0,
            n_in=2,
            n_out=2,
            excludes_m="",
            process_tuple="{F[2,{1}], -F[2,{1}]}, {F[2,{2}], -F[2,{2}]}",
            model_name="SM",
            feynarts_version="3.11",
            model_hash="abc123",
            diagram_cap=2000,
        )
        # Normalize: the process_tuple in the template is wrapped in another set of braces
        # by the template literal {process_tuple}
        assert 'Needs["FeynArts`"]' in result
        assert "SetDirectory" in result
        assert "CreateTopologies[0, 2 -> 2" in result
        assert 'Model -> "SM"' in result
        assert 'GenericModel -> "Lorentz"' in result
        assert "FEYNARTS_EMPTY_RESULT" in result
        assert "FEYNARTS_TOO_MANY_DIAGRAMS" in result
        assert "CreateFeynAmp" in result
        assert '"feynarts_version" -> "3.11"' in result
        assert '"model_hash" -> "abc123"' in result
        assert "FEYNARTS_OK" in result

    def test_loop_order_1(self):
        result = render_driver(
            run_dir="/tmp/loop_run",
            loop_order=1,
            n_in=1,
            n_out=1,
            excludes_m="",
            process_tuple="{V[2]}, {V[2]}",
            model_name="SM",
            feynarts_version="3.11",
            model_hash="def456",
            diagram_cap=2000,
        )
        assert "CreateTopologies[1, 1 -> 1" in result

    def test_excludes_inserted(self):
        result = render_driver(
            run_dir="/tmp/excl_run",
            loop_order=1,
            n_in=1,
            n_out=1,
            excludes_m="Tadpoles, SelfEnergies",
            process_tuple="{V[2]}, {V[2]}",
            model_name="SM",
            feynarts_version="3.11",
            model_hash="def456",
            diagram_cap=2000,
        )
        assert "Tadpoles, SelfEnergies" in result

    def test_custom_diagram_cap(self):
        result = render_driver(
            run_dir="/tmp/cap_run",
            loop_order=0,
            n_in=2,
            n_out=2,
            excludes_m="",
            process_tuple="{F[2,{1}]}, {F[2,{2}]}",
            model_name="SM",
            feynarts_version="3.11",
            model_hash="abc",
            diagram_cap=500,
        )
        assert "nDiag > 500" in result

    def test_sarah_model_path(self):
        result = render_driver(
            run_dir="/tmp/sarah_run",
            loop_order=0,
            n_in=2,
            n_out=2,
            excludes_m="",
            process_tuple="{F[2,{1}]}, {F[2,{2}]}",
            model_name="DarkSU3",
            feynarts_version="3.11",
            model_hash="sarah_hash",
        )
        assert 'Model -> "DarkSU3"' in result


class TestRenderMakeFeynArtsDriver:
    def test_make_feynarts_driver(self):
        result = render_make_feynarts_driver(
            feynarts_state_dir="/state/models/DarkSU3/feynarts_state",
            sarah_path="/home/user/SARAH-4.15.3",
            model_name="DarkSU3",
        )
        assert 'SetDirectory["/state/models/DarkSU3/feynarts_state"]' in result
        assert 'AppendTo[$Path, "/home/user/SARAH-4.15.3/.."]' in result
        assert 'Needs["SARAH`"]' in result
        assert 'Start["DarkSU3"]' in result
        assert "MakeFeynArts[]" in result
        assert "Exit[0]" in result
