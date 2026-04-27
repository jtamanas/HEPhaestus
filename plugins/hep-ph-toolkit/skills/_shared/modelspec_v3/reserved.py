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

RENDERER_ALIASES = {'eEM': 'e', 'vEW': 'v'}


def is_reserved(name: str) -> bool:
    """True if `name` cannot be used as a declared identifier."""
    if name in RENDERER_ALIASES:
        return False  # alias source is allowed
    return (
        name in MATHEMATICA_BUILTINS
        or name in SARAH_RESERVED
        or name in SINGLE_LETTERS
    )
