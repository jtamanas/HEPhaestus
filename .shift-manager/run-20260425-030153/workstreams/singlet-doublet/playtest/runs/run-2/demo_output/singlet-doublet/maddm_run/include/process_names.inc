C     List of the process names in order of dmi, dmj, nprocesses(dmi,
C      dmj)
C     Annihilation process names
C     Number of annihilation processes for each DM pair
      PROCESS_NAMES(1) = 'chi1chi1_zz'
      PROCESS_NAMES(2) = 'chi1chi1_zh'
      PROCESS_NAMES(3) = 'chi1chi1_hh'
      PROCESS_NAMES(4) = 'chi1chi1_wpwm'
      PROCESS_NAMES(5) = 'chi1chi1_ddx'
      PROCESS_NAMES(6) = 'chi1chi1_uux'
      PROCESS_NAMES(7) = 'chi1chi1_ssx'
      PROCESS_NAMES(8) = 'chi1chi1_ccx'
      PROCESS_NAMES(9) = 'chi1chi1_bbx'
      PROCESS_NAMES(10) = 'chi1chi1_ttx'
      PROCESS_NAMES(11) = 'chi1chi1_emep'
      PROCESS_NAMES(12) = 'chi1chi1_mummup'
      PROCESS_NAMES(13) = 'chi1chi1_tamtap'
      PROCESS_NAMES(14) = 'chi1chi1_gg'
      PROCESS_NAMES(15) = 'chi1chi1_aa'
      PROCESS_NAMES(16) = 'chi1chi1_vevex'
      PROCESS_NAMES(17) = 'chi1chi1_dsx'
      PROCESS_NAMES(18) = 'chi1chi1_dbx'
      PROCESS_NAMES(19) = 'chi1chi1_ucx'
      PROCESS_NAMES(20) = 'chi1chi1_utx'
      PROCESS_NAMES(21) = 'chi1chi1_sdx'
      PROCESS_NAMES(22) = 'chi1chi1_sbx'
      PROCESS_NAMES(23) = 'chi1chi1_cux'
      PROCESS_NAMES(24) = 'chi1chi1_ctx'
      PROCESS_NAMES(25) = 'chi1chi1_bdx'
      PROCESS_NAMES(26) = 'chi1chi1_bsx'
      PROCESS_NAMES(27) = 'chi1chi1_tux'
      PROCESS_NAMES(28) = 'chi1chi1_tcx'
      PROCESS_NAMES(29) = 'chi1chi1_emmup'
      PROCESS_NAMES(30) = 'chi1chi1_emtap'
      PROCESS_NAMES(31) = 'chi1chi1_mumep'
      PROCESS_NAMES(32) = 'chi1chi1_mumtap'
      PROCESS_NAMES(33) = 'chi1chi1_tamep'
      PROCESS_NAMES(34) = 'chi1chi1_tammup'
C     DM/SM scattering process names
C     Total number of processes for each category
      NUM_PROCESSES = 34

      ANN_NUM_PROCESSES = 34

      DM2DM_NUM_PROCESSES = 0

      SCATTERING_NUM_PROCESSES = 0

C     Boolean operators for identical particles in the initial state
C     Annihilation diagrams
      ANN_PROCESS_IDEN_INIT(1,1,1) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,2) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,3) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,4) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,5) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,6) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,7) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,8) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,9) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,10) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,11) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,12) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,13) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,14) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,15) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,16) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,17) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,18) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,19) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,20) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,21) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,22) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,23) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,24) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,25) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,26) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,27) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,28) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,29) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,30) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,31) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,32) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,33) = .TRUE.
      ANN_PROCESS_IDEN_INIT(1,1,34) = .TRUE.
C     Boolean flags for photon in final state:
C     true means that the process has at least one photon
C     in the final state
      IS_LINE_PROCESS(1) = .FALSE.
      IS_LINE_PROCESS(2) = .FALSE.
      IS_LINE_PROCESS(3) = .FALSE.
      IS_LINE_PROCESS(4) = .FALSE.
      IS_LINE_PROCESS(5) = .FALSE.
      IS_LINE_PROCESS(6) = .FALSE.
      IS_LINE_PROCESS(7) = .FALSE.
      IS_LINE_PROCESS(8) = .FALSE.
      IS_LINE_PROCESS(9) = .FALSE.
      IS_LINE_PROCESS(10) = .FALSE.
      IS_LINE_PROCESS(11) = .FALSE.
      IS_LINE_PROCESS(12) = .FALSE.
      IS_LINE_PROCESS(13) = .FALSE.
      IS_LINE_PROCESS(14) = .FALSE.
      IS_LINE_PROCESS(15) = .TRUE.
      IS_LINE_PROCESS(16) = .FALSE.
      IS_LINE_PROCESS(17) = .FALSE.
      IS_LINE_PROCESS(18) = .FALSE.
      IS_LINE_PROCESS(19) = .FALSE.
      IS_LINE_PROCESS(20) = .FALSE.
      IS_LINE_PROCESS(21) = .FALSE.
      IS_LINE_PROCESS(22) = .FALSE.
      IS_LINE_PROCESS(23) = .FALSE.
      IS_LINE_PROCESS(24) = .FALSE.
      IS_LINE_PROCESS(25) = .FALSE.
      IS_LINE_PROCESS(26) = .FALSE.
      IS_LINE_PROCESS(27) = .FALSE.
      IS_LINE_PROCESS(28) = .FALSE.
      IS_LINE_PROCESS(29) = .FALSE.
      IS_LINE_PROCESS(30) = .FALSE.
      IS_LINE_PROCESS(31) = .FALSE.
      IS_LINE_PROCESS(32) = .FALSE.
      IS_LINE_PROCESS(33) = .FALSE.
      IS_LINE_PROCESS(34) = .FALSE.
C     DM -> DM diagrams
C     Final state information for all the DM -> DM processes
C     Initial state degrees of freedom for all the DM/SM scattering
C      processes
C     And Total initial state degrees of freedom for all the DM/SM
C      scattering processes
C     Total number of Direct Detection processes
      DD_NUM_PROCESSES = 0

C     Processes relevant for Direct Detection
C     Processes relevant for Direct Detection (effective vertices)
C     Processes relevant for Direct Detection (effective vertices +
C      full vertices)
