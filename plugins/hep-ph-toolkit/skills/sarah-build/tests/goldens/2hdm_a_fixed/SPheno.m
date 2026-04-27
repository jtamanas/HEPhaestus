(* SPheno.m — minimal SPheno interface for TwoHdmAfix *)
(* Based on PortalDM SPheno.m structure *)

OnlyLowEnergySPheno = True;

MINPAR = {
    {1, mchi},
    {2, gchi}
};

EXTPAR = {
    {1, mchi},
    {2, gchi},
    {3, lam1},
    {4, lam2},
    {5, lam3},
    {6, lam4},
    {7, lam5r},
    {8, maSq},
    {9, lamP}
};

RenormalizationScaleFirstGuess = 1000^2;
RenormalizationScale = 1000^2;

UseHiggsMassInsteadOfMu = False;

ListDecayParticles = {Fchi, hh, Ah};
ListDecayParticles3B = {};

(*--- Low-energy constraints ---*)
AddSMConstraints = True;
