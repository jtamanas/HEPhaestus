# DESIGN-ITEM4-AMENDMENT2R1 — Majorana-crossed correction (post probe7/probe8)

Amends AMENDMENT2.md against the FINAL pr35-rereview/REVIEW.md. Accepted: the
crossing (k3-k2)(k4-k1) mixed sector IS Fierz-equivalent to χ⊗q (probe7); the
irreducible content is exactly the Majorana-crossed monomials F5*F6, F7*F8
(0.186 each, probe8), whose chains pair incoming-together/outgoing-together
with the incoming χ leg barred.

## R1 — Amendment-2 rotation as specced is INSUFFICIENT for the crossed pair;
amend to the C-conjugation-aware variant. Guard confirmed adequate either way.

The 16-Γ trace-completeness rearrangement I specced re-pairs barred with
UNbarred slots. F5*F6/F7*F8 have BOTH χ legs barred ((ū_χ(k1) A u_q(k2)) ×
(ū_χ(k3) B u_q(k4))): no re-pairing reaches the standard assignment
(ū_χ(k3)…u_χ(k1))(ū_q(k4)…u_q(k2)) without flipping a barred leg — plain Fierz
cannot do that. **Amended spec:** for the crossed monomials ONLY, first thread
the charge-conjugation matrix through one chain (the transposition identity
ū(k1) Γ u(k2) = ū^c(k2) (C Γ^T C⁻¹) u^c(k1), with C explicit in the Dirac rep
and the Majorana self-conjugacy u^c_χ = phase·u_χ for the χ legs
`[VERIFY phase against the FeynArts Majorana convention — the exactness guard
adjudicates it numerically]`), THEN apply the standard 16-Γ Fierz. Still
machine-evaluated per monomial (trace algebra + explicit C), norms-clean under
A2. **Guard adequacy, confirmed:** the <1e-12 per-config exactness guard
compares rotated-vs-original ON THE SAME config values, so a wrong-pairing
rotation (an expression that is not identically the original monomial) fails
loudly at SD-FIERZ-ROTATION-INEXACT; and an unrotated crossed monomial fails
the completeness guard at 0.186. No silent path exists in either failure mode
— but the spec fix is still mandatory, since a guard that always fires is a
blocked pipeline, not a working one.

## R2 — C-conjugate-then-rotate; crossed reference columns REJECTED, same
undercounting argument, applied with MORE force

The crossed monomials are the IRR-4 crossed box — half the box physics, and
the piece that IS the Majorana structure (Decision 3.4). Crossed reference
columns would match M's own monomials exactly (constant coefficients), park
their content as diagnostics, and the crossed box's real SI-scalar strength
would never reach C_scalar: a green-guarded floor missing ~half its box
contribution. The undercounting ruling of AMENDMENT2 Ruling 1 applies
unchanged and more forcefully. Decided: C-conjugate-then-rotate.

## R3 — Predictions survive; reopen trigger stands (expectation now ~nil)

Pre-registered numbers unchanged: post-fix completeness < 1e-10 (now genuinely
reachable — probe8 has 14/16 monomials in span at ~2e-15 and the two crossed
ones become spannable by construction after C-rotation); |C_scalar| ∈
[0.5, 5]×1e-7; si_shift < 1%; v-drift < 1% (current 12.4 and 97.9 are
artifacts of the defective instrument, carrying no update). Refutation bound
unchanged: residual > 1e-6 with rotation-exactness + rank + identifiability
guards green reopens per-config kinematics — though REVIEW.md Claim 2(e) now
makes that logically near-impossible (fixed scalars × real bilinears cannot be
a kinematic-consistency artifact), the trigger stays pre-registered rather
than deleted; that discipline is what caught the last three wrong narratives.
**New committed diagnostic (probe8 made permanent):** each of the 16
F-monomials must INDIVIDUALLY project onto the reference basis to < 1e-10;
any future out-of-span content is thereby localized to a named monomial, not
a mystery residual.

## R4 — Direct-monomial non-interference and triangle bit-identity: BINDING

Confirmed unchanged: the rotation (C-conjugation included) applies ONLY to
F5*F6 and F7*F8; the 14 in-span monomials pass through untouched; and
triangle-only must keep reproducing −1.2831509485455282e-7 bit-for-bit (the F3
fixture). Any drift there = construction error, stop. RF2 disposition: with
the crossed operators handled, the "rotated-complete" < 1e-8 bar is
satisfiable by construction; keep the AMENDMENT2 label and rename away from
"Fierz-complete" as the re-review demands.
