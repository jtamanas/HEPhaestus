modname = SingletDoubletB  # as an example  
PreDef = -DGENERATIONMIXING -DONLYDOUBLE
# setting various paths  
InDir = ../include
Mdir = ${InDir}
VPATH = 3-Body-Decays:LoopDecays:TwoLoopMasses:Observables:SM 
name = ../lib/libSPhenoSingletDoubletB.a
 
# check if SARAH module and SPheno are compatibel  
minV=330.00 
cVersion =$(shell expr $(version) \>= $(minV))
#  
# options for various compilers  
#  
# Default Compiler  
F90=gfortran
comp= -c -O -module ${Mdir} -I${InDir}  
LFlagsB= -O  
# Intels ifort,debug modus  
ifeq (${F90},ifortg)  
F90=ifort  
comp= -c -g -module ${Mdir} -I${InDir}  
LFlagsB= -g  
endif  
# gfortran  
ifeq (${F90},gfortran)  
comp= -c -g -ffree-line-length-none -J${Mdir} -I${InDir}  
LFlagsB= -g  
endif  
# g95  
ifeq (${F90},g95)  
comp= -c -O -fmod=${Mdir} -I${InDir}  
LFlagsB= -O  
endif  
# Lahey F95 compiler  
ifeq (${F90},lf95)  
comp=-c -O -M ${Mdir} -I${InDir}  
LFlagsB=-O  
endif  
# NAG f95/2003  
ifeq (${F90},nagfor)  
comp= -c -O -mdir ${Mdir} -I${InDir}  
LFlagsB= -O -DONLYDOUBLE -mdir ${MDir} -I${InDir}  
endif   
.SUFFIXES : .o .ps .f90 .F90 .a 
bin/SPhenoSingletDoubletB:
ifeq (${cVersion},1)
	 cd ../src ; ${MAKE} F90=${F90} 
	 ${MAKE} F90=${F90} ${name} 
	 ${MAKE} F90=${F90} SPhenoSingletDoubletB.o 
	 ${F90} -o SPhenoSingletDoubletB ${LFlagsB} SPhenoSingletDoubletB.o ../lib/libSPhenoSingletDoubletB.a ../lib/libSPheno.a
	 mv SPhenoSingletDoubletB ../bin
	 rm SPhenoSingletDoubletB.o  
${name}:  ${name}(Settings.o) ${name}(Model_Data_SingletDoubletB.o)  \
 ${name}(RGEs_SingletDoubletB.o)   \
 ${name}(Couplings_SingletDoubletB.o) ${name}(TreeLevelMasses_SingletDoubletB.o) ${name}(TadpoleEquations_SingletDoubletB.o) \
 ${name}(LoopCouplings_SingletDoubletB.o) ${name}(CouplingsForDecays_SingletDoubletB.o) \
 ${name}(TreeLevel_Decays_SingletDoubletB.o) \
 ${name}(Fu.o)  ${name}(Fe.o)  ${name}(Fd.o)  \
${name}(AddLoopFunctions.o) ${name}(Kinematics.o) \
 ${name}(2LPoleFunctions.o) ${name}(2LPole_SingletDoubletB.o) \
 ${name}(LoopMasses_SingletDoubletB.o) \
 ${name}(RGEs_SM_HC.o) ${name}(Couplings_SM_HC.o) ${name}(TreeLevelMasses_SM_HC.o) ${name}(LoopMasses_SM_HC.o)   \
${name}(CouplingsCT_SingletDoubletB.o) \
${name}(Bremsstrahlung.o) ${name}(DecayFFS.o) ${name}(DecayFFV.o) ${name}(DecaySSS.o) ${name}(DecaySSV.o) ${name}(DecaySFF.o) ${name}(DecaySVV.o) \
 ${name}(LoopDecayFu_SingletDoubletB.o)  ${name}(LoopDecayFe_SingletDoubletB.o)  ${name}(LoopDecayFd_SingletDoubletB.o)  ${name}(LoopDecayhh_SingletDoubletB.o)  ${name}(LoopDecayChi_SingletDoubletB.o)  ${name}(LoopDecayChiM_SingletDoubletB.o) \
 ${name}(Wrapper_LoopDecay_Fu_SingletDoubletB.o)  ${name}(Wrapper_LoopDecay_Fe_SingletDoubletB.o)  ${name}(Wrapper_LoopDecay_Fd_SingletDoubletB.o)  ${name}(Wrapper_LoopDecay_hh_SingletDoubletB.o)  ${name}(Wrapper_LoopDecay_Chi_SingletDoubletB.o)  ${name}(Wrapper_LoopDecay_ChiM_SingletDoubletB.o) ${name}(OneLoopDecays_SingletDoubletB.o) \
 ${name}(BranchingRatios_SingletDoubletB.o) ${name}(HiggsCS_SingletDoubletB.o) ${name}(RunSM_SingletDoubletB.o) \
${name}(FlavorKit_LFV_SingletDoubletB.o) ${name}(FlavorKit_QFV_SingletDoubletB.o) ${name}(FlavorKit_Observables_SingletDoubletB.o)\
 ${name}(LowEnergy_SingletDoubletB.o) \
 ${name}(Boundaries_SingletDoubletB.o)  ${name}(InputOutput_SingletDoubletB.o) 
else 
	 @echo -------------------------------------------------------------------  
	 @echo ERROR:  
	 @echo The installed SPheno is version not compatibel with this module 
	 @echo Please, upgrade at least to SPheno version 3.3.0.  
	 @echo The current SPheno version can be downloaded from 
	 @echo http://www.hepforge.org/downloads/spheno 
	 @echo ------------------------------------------------------------------- 
endif 
clean: 
	 rm -f *.o *~ */*.o */*~
cleanall: 
	 rm -f bin/SPheno3 lib/*.a *~ */*.o */*~ include/*
#
# Suffix rules
#
.f90.a:
	 ${F90} ${comp} $< 
	 ar -ruc -U $@ $*.o
	 rm -f $*.o
.F90.a:
	 ${F90} ${comp} ${PreDef} $< 
	 ar -ruc -U $@ $*.o
	 rm -f $*.o
.f90.o:
	 ${F90} ${comp} $<
.f90.ps:
	 a2ps -o $*.ps $<
.h.ps:
	 a2ps -o $*.ps $<
