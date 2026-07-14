#!/usr/bin/env python3
"""Pairing-vs-diagram census of raw FeynArts FeynAmpList artifacts (AMENDMENT9 item 1).

Pure text analysis (no Wolfram kernel). For each FeynAmp[GraphID[...],...]:
  - extract the scalar prefactor preceding the first FermionChain/MatrixTrace
  - list each external FermionChain's spinor content, order, and momentum signs
  - attribute prefactor-sign variation via (-1)^(#V + closed-fermion-loop + ghost-loop)

Usage: parse_feynamp_signs.py <FeynAmpList.m>
Evidence produced for EVIDENCE-PAIRING-VS-DIAGRAM.md from the production artifact
  .../loopset-step2/loop1_full_chi1/FeynAmpList.m  (164/164 uniform pairing;
  162/164 sign-law match, residuals T7 G12/G13 = 4-point-vertex generics).
"""
import re
import sys
from collections import Counter, defaultdict


def balanced_end(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                return i
    return -1


def entries(src):
    out = []
    for m in re.finditer(r'FeynAmp\[GraphID', src):
        j = balanced_end(src, m.start() + 7)
        out.append(src[m.start():j + 1])
    return out


def analyze(e):
    gid = re.search(r'GraphID\[Topology == (\d+), Generic == (\d+)\]', e)
    topo, gen = int(gid.group(1)), int(gid.group(2))
    ip = e.find('Integral[')
    expr = e[balanced_end(e, ip + 8) + 2:].strip()
    cut = min(x for x in (expr.find('FermionChain'), expr.find('MatrixTrace')) if x >= 0)
    pref = re.sub(r'\s+', '', expr[:cut])
    neg = pref.startswith('((-') or pref.startswith('-')
    chains, idx = [], 0
    while True:
        p = expr.find('FermionChain[', idx)
        if p < 0:
            break
        j = balanced_end(expr, p + 12)
        chains.append(expr[p:j + 1])
        idx = j + 1
    orders = []
    for ch in chains:
        sp = re.findall(r'(MajoranaSpinor|DiracSpinor)\[\s*(-?)\s*FourMomentum\[(Incoming|Outgoing),\s*(\d)\]', ch)
        orders.append(tuple(f"{k[0][0]}{'-' if k[1] else ''}{k[2][:3]}{k[3]}" for k in sp))
    loop_fields = set(re.findall(r'Mass\[([SFVU])\[Index\[Generic, (\d+)\]', e))
    n_v = sum(1 for t, _ in loop_fields if t == 'V')
    ghost = 1 if any(t == 'U' for t, _ in loop_fields) else 0
    n_mt = 1 if 'MatrixTrace' in expr else 0
    return dict(topo=topo, gen=gen, pref=pref, neg=neg, orders=tuple(orders),
                law_neg=(n_v + ghost + n_mt) % 2 == 1, loop_fields=sorted(loop_fields))


def main(path):
    rows = [analyze(e) for e in entries(open(path).read())]
    pairings = Counter(tuple(sorted(tuple(sorted(o)) for o in r['orders'])) for r in rows)
    print(f"FeynAmps: {len(rows)}")
    print("pairing census (sorted external-spinor sets per chain):")
    for k, v in pairings.items():
        print(f"  {k}: {v}")
    ok = sum(1 for r in rows if r['neg'] == r['law_neg'])
    print(f"sign law (-1)^(#V+floop+ghost): {ok}/{len(rows)} match")
    for r in rows:
        if r['neg'] != r['law_neg']:
            print(f"  residual: T{r['topo']} G{r['gen']} pref={r['pref'][:24]} lf={r['loop_fields']}")
    bytopo = defaultdict(set)
    for r in rows:
        bytopo[r['topo']].add((r['pref'][:12], r['orders']))
    print("per-topology prefactor/pairing variants:")
    for t in sorted(bytopo):
        print(f"  T{t}: {len(bytopo[t])} variants")


if __name__ == '__main__':
    main(sys.argv[1])
