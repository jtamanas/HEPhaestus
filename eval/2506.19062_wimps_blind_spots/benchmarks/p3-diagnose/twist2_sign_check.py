"""
twist2_sign_check.py — VALIDATION-ONLY, NO KERNEL, NO amplitude, NO PV heads.

Independent (numpy-only) re-derivation of the SIGN of the O_Tq <-> Hisano-twist-2
operator bridge used by the P3' campaign, to settle the twist2_sign_gate fork
(World A vs World B).  This evaluates ONLY free-spinor matrix elements of the
REFERENCE operators (the same ones sd_projection.wl builds); it never touches the
loop amplitude, LoopTools, or any protected pipeline file.

It answers exactly one question: within a single consistent metric signature, is
the map from our O_Tq coefficient to Hisano's (g^(1)+g^(2)) a POSITIVE
proportionality (=> the measured twist-2 SIGN agreement is real, World A) or does
it carry a hidden relative sign (=> agreement could mask a flip, World B)?

Convention: mostly-minus eta = diag(+,-,-,-), Dirac representation, ubar u = 2m.
This matches BOTH the pipeline (sd_projection.wl: $metric={1,-1,-1,-1}) AND
Hisano-Ishiwata-Nagata (their Dirac Lagrangian dL = (1/2) chibar(i Dslash - M)chi
is the Peskin mostly-minus form; the (i Dslash - M) structure fixes the signature).
"""
import numpy as np

# ---- Dirac algebra, mostly-minus (Dirac rep), matching sd_projection.wl -------
I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
pauli = [sx, sy, sz]
g0 = np.block([[I2, np.zeros((2, 2))], [np.zeros((2, 2)), -I2]])
gsp = [np.block([[np.zeros((2, 2)), p], [-p, np.zeros((2, 2))]]) for p in pauli]
gamma = [g0] + gsp                      # {g0,g1,g2,g3}
ETA = np.array([1., -1., -1., -1.])     # mostly-minus


def mdot(a, b):
    return a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3]


def slash(v):
    return v[0] * g0 - v[1] * gsp[0] - v[2] * gsp[1] - v[3] * gsp[2]


def onshell(p3, m):
    return np.array([np.sqrt(m * m + np.dot(p3, p3)), *p3])


def xi(s):
    return np.array([1, 0], dtype=complex) if s == +1 else np.array([0, 1], dtype=complex)


def uspinor(p, m, s):
    en = p[0]
    sp = p[1] * pauli[0] + p[2] * pauli[1] + p[3] * pauli[2]
    lower = (sp @ xi(s)) / (en + m)
    return np.sqrt(en + m) * np.concatenate([xi(s), lower])


def ubar(u):
    return np.conj(u) @ g0


def bilin(pa, ma, sa, pb, mb, sb, mat):
    return ubar(uspinor(pa, ma, sa)) @ mat @ uspinor(pb, mb, sb)


# ---- operator matrix elements (spin-summed diagonal, real parts) --------------
def scalar(pa, ma, pb, mb, spins):
    return sum(bilin(pa, ma, s, pb, mb, s, np.eye(4)) for s in spins)


def vec(pa, ma, pb, mb, s):
    return np.array([bilin(pa, ma, s, pb, mb, s, gamma[mu]) for mu in range(4)])


def O_Tq(k1, k2, k3, k4, mchi, mq, spins):
    """our single-contraction operator: (chibar chi)(qbar gamma.P_chi q), P_chi=(k1+k3)/2."""
    Pc = (k1 + k3) / 2
    tot = 0.
    for s in spins:
        chiS = bilin(k3, mchi, s, k1, mchi, s, np.eye(4))
        qv = vec(k4, mq, k2, mq, s)
        tot += chiS * mdot(Pc, qv)
    return tot


def hisano_twist2(k1, k2, k3, k4, mchi, mq, spins):
    """Hisano operator contraction ref1+ref2 (sd_projection twist2Ref1/2), C^(1)+C^(2)=1."""
    Pc = (k1 + k3) / 2
    Pq = (k2 + k4) / 2
    r1 = r2 = 0.
    for s in spins:
        cv = vec(k3, mchi, k1, mchi, s)
        qv = vec(k4, mq, k2, mq, s)
        Sc = bilin(k3, mchi, s, k1, mchi, s, np.eye(4))
        Sq = bilin(k4, mq, s, k2, mq, s, np.eye(4))
        r1 += 0.5 * (mdot(Pc, Pq) * mdot(cv, qv) + mdot(Pc, qv) * mdot(cv, Pq)) \
            - 0.25 * mdot(Pc, cv) * mq * Sq
        r2 += (Sc / mchi) * (mdot(Pc, Pq) * mdot(Pc, qv) - 0.25 * mdot(Pc, Pc) * mq * Sq)
    return r1 + r2


def report(tag, k1, k2, k3, k4, mchi, mq):
    spins = [+1, -1]
    otq = O_Tq(k1, k2, k3, k4, mchi, mq, spins).real
    his = hisano_twist2(k1, k2, k3, k4, mchi, mq, spins).real
    ratio = otq / his if his != 0 else float("nan")
    # bridge prediction: <O_Tq> = (3 m_q/4)*<ref1+ref2>  (static-limit)
    pred = 0.75 * mq  # ratio O_Tq/(ref1+ref2) predicted by the bridge
    print(f"[{tag}] <O_Tq>={otq:+.6e}  <Hisano T1+T2>={his:+.6e}  "
          f"ratio={ratio:+.6e}  bridge(3mq/4)={pred:+.6e}  "
          f"sign_map={'POSITIVE' if ratio > 0 else 'NEGATIVE'}")
    return otq, his, ratio


if __name__ == "__main__":
    mchi, mq = 495.510455, 4.67e-3   # L2 masses
    print("=== O_Tq <-> Hisano-twist-2 sign map (mostly-minus, free spinors) ===")
    # (1) exact rest frame
    k = onshell([0, 0, 0], mchi)
    q = onshell([0, 0, 0], mq)
    report("REST      ", k, q, k, q, mchi, mq)
    # (2) forward-elastic DD kinematics with transverse tilt (k1=k3, k2=k4)
    for i, (dc, dq) in enumerate([
        ([0.30, 0.00, 0.35], [0.40, 0.10, 0.00]),
        ([0.00, 0.40, 0.20], [0.10, 0.30, 0.20]),
        ([0.25, 0.25, 0.20], [0.20, 0.20, 0.25])]):
        kc = onshell(np.array(dc) * mchi, mchi)
        kq = onshell(np.array(dq) * mq, mq)
        report(f"DD-cfg-{i}  ", kc, kq, kc, kq, mchi, mq)
    print("\nInterpretation: a uniformly POSITIVE sign_map at every config means the")
    print("O_Tq coefficient and Hisano's (g1+g2) share sign => the campaign's twist-2")
    print("sign agreement is REAL (not a bridge sign artifact) => WORLD A.")
