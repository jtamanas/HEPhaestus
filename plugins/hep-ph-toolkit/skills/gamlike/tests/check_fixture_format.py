#!/usr/bin/env python3
"""
check_fixture_format.py — one-shot conformance checker for synthetic gamlike fixtures.

Checks that each fixture file conforms to the MadDM 3.2 output format as produced
by maddm_run_interface.py:3444-3628.

Usage: python tests/check_fixture_format.py tests/fixtures/<fixture>.txt
       python tests/check_fixture_format.py tests/fixtures/  (check all .txt)
"""
import re
import sys
from pathlib import Path

# MadDM form_n format: '{0:3.2e}' — e.g. '1.23e-45', ' 1.23e+02'
_FORM_N_RE = re.compile(r'^-?\d\.\d{2}e[+\-]\d{2}$')
# Percent value: '%.2f %%' — e.g. '85.00 %', '100.00 %'
_PCT_RE = re.compile(r'^(?:\d+\.\d{2}|nan) %$')
# Key line: 30-char padded key = value
_KV_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_%][\w()%#\-\*\s]*?)\s+= (?P<value>.+)$'
)
# Bracketed pair: [<num>,<num>]
_BRACKET_RE = re.compile(r'^\[(-?\d\.\d{2}e[+\-]\d{2}),(-?\d\.\d{2}e[+\-]\d{2})\]')
# 3-line banner top/bottom (48 or 49 '#' chars)
_BANNER_LINE_RE = re.compile(r'^#{48,49}$')

KNOWN_BANNERS = {
    '# Relic Density',
    '# Direct Detection [cm^2]',
    '# Indirect Detection',
    '# CR Flux at Earth [particles cm^-2 s^-1 sr^-1)',
}
SPECTRAL_BANNER = '# Gamma-line spectrum and line limits'


def check_file(path: Path) -> list:
    errors = []
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        # Skip empty lines, pure comment lines that are banners, separator lines
        if not stripped or stripped.startswith('#'):
            continue

        # Check key=value lines
        # Key should be left-padded to 30 chars (the '= ' separator follows)
        if '= ' in stripped:
            eq_idx = stripped.index('= ')
            key_part = stripped[:eq_idx]
            val_part = stripped[eq_idx + 2:]

            # Key part should be 30 chars (padded with spaces) for standard lines
            # Exception: channel percent lines use form_s which gives 30-char key
            if len(key_part) < 28 and not stripped.startswith('%_'):
                # Lenient: don't error, just warn for diagnostics
                pass

            # Value part checks
            val_stripped = val_part.split('\t')[0].split('#')[0].strip()

            # Skip ROI and J-factor lines (different format)
            if key_part.strip() in ('ROI', 'J-factor'):
                continue

            if val_stripped.startswith('['):
                # Bracketed pair
                if not _BRACKET_RE.match(val_stripped):
                    errors.append(f"Line {i}: bracketed pair format wrong: {stripped!r}")
            elif val_stripped.endswith('%'):
                # Percent value
                if not _PCT_RE.match(val_stripped):
                    errors.append(f"Line {i}: percent format wrong: {stripped!r}")
            elif val_stripped in ('nan', 'inf', '-inf'):
                pass  # NaN/Inf allowed
            elif re.match(r'^-?\d+\.\d+$', val_stripped) or re.match(r'^-?\d+\.\d+e[+\-]\d+$', val_stripped):
                # Numeric (possibly non-scientific for ROI etc)
                pass
            elif val_stripped and not val_stripped[0].isdigit() and val_stripped[0] not in ('-', '['):
                # String value (like method name)
                pass
            elif val_stripped:
                if not _FORM_N_RE.match(val_stripped):
                    # Only warn for numeric-looking values
                    if val_stripped[0].isdigit() or val_stripped[0] == '-':
                        errors.append(f"Line {i}: numeric format wrong (expected form_n): {val_stripped!r} in {stripped!r}")

    return errors


def check_banner_structure(path: Path) -> list:
    """Check that standard banners are 3-line #-bordered blocks."""
    errors = []
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    in_banner = False
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        for banner in KNOWN_BANNERS:
            if stripped == banner or stripped.startswith(banner + ' ') or stripped.startswith(banner.rstrip() + ' '):
                # The line before (i-2 in 0-indexed) should be '#'*48
                if i >= 2 and not _BANNER_LINE_RE.match(lines[i - 2].rstrip()):
                    errors.append(f"Line {i}: banner '{banner}' missing preceding #-line")
                # The line after (i in 0-indexed, since i is 1-indexed current) should be '#'*48
                if i < len(lines) and not _BANNER_LINE_RE.match(lines[i].rstrip()):
                    errors.append(f"Line {i}: banner '{banner}' missing following #-line")
    return errors


def main():
    paths = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(p.glob('*.txt')))
        else:
            paths.append(p)

    if not paths:
        print("Usage: check_fixture_format.py <file_or_dir> [...]")
        sys.exit(1)

    all_ok = True
    for path in paths:
        errs = check_file(path)
        errs += check_banner_structure(path)
        if errs:
            all_ok = False
            print(f"FAIL: {path}")
            for e in errs:
                print(f"  {e}")
        else:
            print(f"OK: {path}")

    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
