"""
Claude Code runner — invokes `claude -p` with HEP skills loaded.

Spawns a Claude Code subprocess with the monte-carlo-tools plugin,
passes the task prompt, and extracts structured answers from the response.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from ..types import Task
from .base import RunnerBase


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "hep-ph-toolkit"


# PR-A blocker contract: the agent MUST reply with one of two shapes.
#   {"status": "tool_verified", "value": {<observable keys>}}
#   {"status": "blocked", "reason": "...", "missing": [...], "next_steps": [...]}
# Mixing `status: "blocked"` with a populated `value` is a contract
# violation and will be classified as MG_WRONG by the outcome classifier.
# PR-D will add a third status `reference_only`; do not invent it here.
SYSTEM_PROMPT = """\
You are a high-energy physics computation assistant. For observables that \
require MadGraph5_aMC@NLO or MadDM to compute (cross-sections, branching \
ratios, event rates that depend on a UFO model), you MUST use the real \
tool. Do NOT fabricate numerical values from memory.

Workflow for tool-verified observables:
  1. Set up the process (proc_card) and parameters (param_card).
  2. Run MadGraph or MadDM to compute the observable.
  3. Parse the output to extract numerical results.
  4. Return the final answer in the JSON schema below.

Response schema (return EXACTLY one of these as a ```json ... ``` block):

  # Success path — tool actually ran and produced the value.
  {"status": "tool_verified",
   "value": {"sigma_SI": 7.6e-45, "sigma_SI_unit": "cm^2", "m_chi1": 132.69}}

  # Blocker path — the required tool is unavailable in this environment.
  {"status": "blocked",
   "reason": "MadDM not installed at $MADDM_PATH",
   "missing": ["MadDM"],
   "next_steps": ["export MADDM_PATH=...", "rerun with maddm available"]}

Hard rules:
- If you emit `"status": "blocked"`, the `value` field MUST be absent or empty.
  Blocking AND reporting numbers at the same time is a contract violation.
- Put the observable keys (sigma_SI, m_chi1, etc.) inside `value`, NOT at
  the top level.
- Use one of the three statuses: `tool_verified`, `blocked`, or
  `reference_only` (see opt-in section below).

The fence: if the answer key is an observable your collaborator would quote
in a paper table, MadGraph/MadDM (or the appropriate spectrum/relic tool)
computes it. Python is a thin driver, not a replacement. Use the following
allow/forbid list — do NOT self-authorize observable calculations as
"just verifying Eq. N":

ALLOWED in Python / numpy / scipy:
- Numerical eigenvalue/eigenvector decomposition of a mass matrix you type in
  from the paper (for the mass spectrum itself — NOT as an intermediate for
  computing a downstream observable in pure Python).
- Symbolic verification of blind-spot identities, sum rules, charge
  assignments, anomaly cancellations.
- Round-trips through parameterizations (Casas-Ibarra, mass-matrix inversion,
  inverse parameter reconstruction).
- Unit conversions, ratio computations, scaling-law verification.
- Driving MG5/MadDM: writing proc_card/param_card/run_card files, launching
  the binary, parsing LHE/banner output.
- Parameter-scan scripting around MG5/MadDM.

FORBIDDEN in Python (these must come from MadGraph/MadDM; if the required
tool/UFO is unavailable, stop and emit the blocker JSON above rather than
reimplementing):
- Cross sections sigma(a -> b) at any order (tree, loop, NLO).
- Decay widths Gamma(X -> YZ) at any order.
- Loop integrals (Passarino-Veltman, Bauer G-function, triangle, box, ...).
- Branching ratios.
- Relic densities Omega h^2 (Boltzmann freeze-out, co-annihilation).
- Direct-detection rates sigma_SI, sigma_SD at the "physics observable" layer.
  A Wilson-coefficient-only intermediate computation is still algebra and is
  fine; the dressed per-nucleon cross section is an observable and is not.
- Indirect-detection rates <sigma v>, photon line spectra.

Ratios, scaling identities, and symbolic limits of forbidden observables
(e.g. sigma_SI(2 m_A) / sigma_SI(m_A), G(x -> 0), ratio of two branching
ratios) are ALGEBRA and belong in Python. The forbid list above applies
only when you are asked to report an absolute observable value. If every
forbidden ingredient cancels in the ratio or is evaluated in a closed-form
limit, compute it in Python and return `status: tool_verified` — this is
exact algebra, not an estimate.

--- Recoverable tool failures — don't block prematurely ---
Real MadGraph/MadDM runs frequently hit transient/configuration errors that
look fatal but are recoverable in under a minute. Do NOT return
`status: blocked` for any of the following — try the listed recovery first:

- LHAPDF missing: try `--no-lhapdf` or warn and continue with MG5's built-in
  PDFs. For DM-only observables (sigma_SI, <sigma v>, relic density) the PDF
  set rarely matters; proceed.
- syscalc hang: add `set systematics_program none` to the run_card (or set it
  at the `launch` interactive prompt). Re-run.
- narrow-width warning on resonances: `set small_width_treatment 0` in the
  run_card, or accept the warning if you only need the on-shell rate.
- UFO Python-2 / Python-3 residue: most modern UFOs are clean; if MG5 chokes
  on a model file, grep for bare `print` statements missing parens and add
  them. Do not block — patch and retry.
- mass-ordering abort: inspect the param_card and confirm the DM candidate is
  lighter than the mediator (or the ordering your model requires). Fix the
  masses and retry.
- timeout on the first `launch`: re-run with a smaller `nevents` (e.g. 1000)
  to validate the setup, then scale up only once a short run succeeds.

`status: blocked` is reserved for genuine unrecoverable issues (missing tool
binary, missing UFO/model file, skill not implemented, task physically
impossible with available tooling). Recover from transient/configuration
errors before blocking. If you recover successfully, proceed normally and
return the computed result with `status: tool_verified`.

--- `reference_only` status (opt-in estimation) ---
A THIRD response status is available in addition to `tool_verified` and
`blocked`: `reference_only`. Use it when a closed-form / tree-level estimate
is the right answer for an explicitly pedagogical or quick-estimate task.

Opt-in requirements (ALL must hold):
1. The task has the tag `pedagogical` or `quick_estimate`, OR the user request
   contains the words "estimate", "rough", or "order of magnitude".
2. You can cite a specific closed-form equation (paper + equation number).
3. You include both `reference_method` and `caveats` in the payload.

Schema:
```json
{
  "status": "reference_only",
  "value": {"sigma_SI": 7.6e-45, "sigma_SI_unit": "cm^2"},
  "reference_method": "tree-level Higgs-portal closed-form, Eq. 5 of arXiv:2506.19062",
  "caveats": ["LO only", "no radiative corrections", "nucleon form factors from Hoferichter 2015"]
}
```

NEVER use `status: reference_only` as a workaround for a genuine blocker. If
MadGraph is missing and the task is not opted into estimation, return
`status: blocked` — do not silently fall back to a closed-form.

Unit / formatting rules:
- Report cross-sections in cm^2.
- Report masses in GeV.
- Report angles in radians.
- Report couplings as dimensionless numbers.
- Include units as separate keys (e.g. "sigma_SI_unit": "cm^2").
- If a quantity should be exactly zero, report 0.0.
- Do not round — give full numerical precision.
"""


# ---------------------------------------------------------------------------
# JSON extraction from Claude's text output (hardened in PR-A).
# ---------------------------------------------------------------------------

_OBSERVABLE_HINT_KEYS: tuple[str, ...] = ("status",)


def _iter_json_blocks(text: str) -> list[dict]:
    """Yield every parseable JSON object from `text`, in order.

    Looks at:
      1. ```json ... ``` fenced blocks.
      2. plain ``` ... ``` fenced blocks.
      3. bare top-level JSON objects.

    The order of the returned list matches document order.
    """
    out: list[dict] = []

    # 1. ```json ... ``` fenced blocks
    for m in re.finditer(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL):
        try:
            parsed = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            out.append(parsed)

    # 2. plain ``` ... ``` fenced blocks (only accept dicts)
    for m in re.finditer(r"```\s*\n(.*?)\n\s*```", text, re.DOTALL):
        body = m.group(1).strip()
        # Skip if this was already captured as a ```json block above.
        if not body:
            continue
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed not in out:
            out.append(parsed)

    # 3. bare top-level JSON objects (balanced-brace scan)
    for m in re.finditer(r"\{[^{}]*\}", text):
        try:
            parsed = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed not in out:
            out.append(parsed)

    return out


def _extract_json_block(
    text: str,
    expected_keys: tuple[str, ...] | None = None,
) -> dict[str, Any] | None:
    """Extract the best JSON object from Claude's text response.

    PR-A hardening: prefer the LAST block whose top-level keys include
    either the canonical contract key `status` OR any of the expected
    observable keys from the task's graders. If no block matches that
    preference, fall back to the last parseable block.

    (Why "last"? Agents often emit exploratory / draft JSON earlier in
    their reply and the final answer block at the bottom. The previous
    first-match behavior could pick up the scratch object.)
    """
    blocks = _iter_json_blocks(text)
    if not blocks:
        return None

    preferred_keys: set[str] = set(_OBSERVABLE_HINT_KEYS)
    if expected_keys:
        preferred_keys.update(expected_keys)

    # Walk blocks in reverse, pick the first preferred match.
    for block in reversed(blocks):
        if preferred_keys.intersection(block.keys()):
            return block

    # Fallback: the last block, whatever it is.
    return blocks[-1]


# ---------------------------------------------------------------------------
# Claude `--output-format json` stream parsing.
# ---------------------------------------------------------------------------

def _collect_tool_uses(events: list) -> list[dict]:
    """Walk a Claude JSON event stream and return every tool_use event.

    In `--output-format json`, tool_use events appear inside `assistant`
    messages as objects of the form::

        {"type": "tool_use", "name": "Bash"|"Read"|..., "input": {...}}

    We handle:
      - top-level events that ARE tool_use objects (rare, but defensive);
      - `assistant` events whose `message.content` is a list of content
        blocks (normal Claude CLI shape);
      - nested content arrays (e.g. thinking blocks that themselves
        contain nested structures).
    """
    out: list[dict] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "tool_use" and "name" in node:
                out.append(node)
            # Recurse into known nesting points + everything else defensively.
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)
        # scalars: ignore

    for ev in events:
        _walk(ev)

    return out


def _parse_claude_json_output(raw_output: str) -> dict:
    """Parse the JSON stream from `claude --output-format json`.

    Returns a dict with:
        result_text:     Claude's text response
        answer:          extracted JSON dict from the response (or {})
        tool_uses:       list of tool_use events from the stream
        total_cost_usd:  API cost
        input_tokens:    total input tokens
        output_tokens:   total output tokens
        num_turns:       number of agent turns
    """
    parsed: dict[str, Any] = {
        "result_text": "",
        "answer": {},
        "tool_uses": [],
        "total_cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "num_turns": 0,
    }

    try:
        events = json.loads(raw_output)
        if not isinstance(events, list):
            events = [events]
    except json.JSONDecodeError:
        # Fall back to line-by-line parsing (stream-json format).
        events = []
        for line in raw_output.strip().splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Collect tool_use events before we walk for result/usage so that a
    # malformed late event doesn't stop us from seeing earlier tool calls.
    parsed["tool_uses"] = _collect_tool_uses(events)

    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("type") == "result":
            parsed["result_text"] = event.get("result", "")
            parsed["total_cost_usd"] = event.get("total_cost_usd", 0.0)
            parsed["num_turns"] = event.get("num_turns", 0)
            usage = event.get("usage", {}) or {}
            parsed["input_tokens"] = usage.get("input_tokens", 0)
            parsed["output_tokens"] = usage.get("output_tokens", 0)

    # Extract structured answer from Claude's text.
    if parsed["result_text"]:
        answer = _extract_json_block(parsed["result_text"])
        if answer:
            parsed["answer"] = answer

    return parsed


class ClaudeCodeRunner(RunnerBase):
    """Executes tasks by spawning Claude Code, optionally with HEP skills."""

    def __init__(
        self,
        model: str = "sonnet",
        max_turns: int = 10,
        timeout_s: int = 300,
        max_budget_usd: float = 1.0,
        permission_mode: str = "bypassPermissions",
        plugin_dir: str | Path | None = None,
        skills: bool = True,
    ):
        self._model = model
        self._max_turns = max_turns
        self._timeout_s = timeout_s
        self._max_budget_usd = max_budget_usd
        self._permission_mode = permission_mode
        self._plugin_dir = Path(plugin_dir) if plugin_dir else PLUGIN_DIR
        self._skills = skills
        self._last_meta: dict = {}

    def run(self, task: Task) -> dict[str, Any]:
        prompt = self._build_prompt(task)
        cmd = self._build_command(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
                cwd=str(PROJECT_ROOT),
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Claude Code timed out after {self._timeout_s}s")

        if result.returncode != 0 and not result.stdout:
            raise RuntimeError(
                f"Claude Code failed (rc={result.returncode}): "
                f"{result.stderr[:500]}")

        parsed = _parse_claude_json_output(result.stdout)

        # Re-extract with task-aware expected-key hints, so the "last block
        # whose keys match" preference can use observable names too.
        if parsed["result_text"]:
            hint_keys = tuple(self._observable_keys(task))
            better = _extract_json_block(
                parsed["result_text"], expected_keys=hint_keys
            )
            if better:
                parsed["answer"] = better

        self._last_meta = {
            "total_cost_usd": parsed["total_cost_usd"],
            "input_tokens": parsed["input_tokens"],
            "output_tokens": parsed["output_tokens"],
            "num_turns": parsed["num_turns"],
            "result_text": parsed["result_text"],
            "tool_uses": parsed["tool_uses"],
            "raw_answer": parsed["answer"],
        }

        if not parsed["answer"]:
            raise RuntimeError(
                "Claude did not return a JSON answer block. "
                f"Response: {parsed['result_text'][:500]}")

        # Unwrap the {"status": "...", "value": {...}} envelope so downstream
        # graders see the observable keys directly. Applies to both
        # `tool_verified` (canonical success) and `reference_only` (opt-in
        # closed-form estimate, PR-D). For a blocker response, return the
        # envelope as-is — the outcome classifier inspects it via
        # extract_blocked().
        answer = parsed["answer"]
        if isinstance(answer, dict) and answer.get("status") in (
            "tool_verified", "reference_only"
        ):
            value = answer.get("value")
            if isinstance(value, dict):
                return value

        return answer

    @property
    def last_meta(self) -> dict:
        """Metadata from the most recent run (cost, tokens, tool_uses, etc.)."""
        return self._last_meta

    @property
    def name(self) -> str:
        tag = "skills" if self._skills else "no-skills"
        return f"claude-code ({self._model}, {tag})"

    @staticmethod
    def _observable_keys(task: Task) -> set[str]:
        keys: set[str] = set()
        for g in task.graders:
            if g.key:
                keys.add(g.key)
            if g.key_a:
                keys.add(g.key_a)
            if g.key_b:
                keys.add(g.key_b)
        return keys

    def _build_prompt(self, task: Task) -> str:
        """Construct the full prompt for Claude."""
        keys = self._observable_keys(task)
        key_hint = ", ".join(sorted(keys)) if keys else "the relevant quantities"

        return (
            f"{task.prompt}\n\n"
            f"Return your answer inside the schema in the system prompt. "
            f"The `value` object should contain at least these keys: "
            f"{key_hint}.\n"
            f"Wrap the JSON in ```json ... ``` markers."
        )

    def _build_command(self, prompt: str) -> list[str]:
        """Build the claude CLI command."""
        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "json",
            "--model", self._model,
            "--permission-mode", self._permission_mode,
            "--append-system-prompt", SYSTEM_PROMPT,
            "--max-budget-usd", str(self._max_budget_usd),
            "--no-session-persistence",
        ]

        if self._skills and self._plugin_dir.is_dir():
            cmd.extend(["--plugin-dir", str(self._plugin_dir)])

        return cmd
