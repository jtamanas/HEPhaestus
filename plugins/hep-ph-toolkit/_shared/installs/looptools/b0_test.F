* b0_test.F — minimal smoke test for LoopTools full-smoke mode.
*
* Build (with LoopTools installed at $PREFIX):
*   gfortran -I$PREFIX/include b0_test.F -L$PREFIX/lib -looptools -o b0_test
*
* Expected output on stdout (from LoopTools 2.16 User's Guide §2.1, p. 26):
*   B0 = (-4.40593283, 2.7041431)
*
* The install.sh validator matches the first 4 decimal places of both the
* real and imaginary parts against those reference values.
*
* Note: file extension MUST be .F (capital) so gfortran runs cpp on the
* #include below. A lowercase .f extension will fail to parse.
      program b0_test
      implicit none
#include "looptools.h"
      double complex result
      call ltini
      result = B0(1000D0, 50D0, 80D0)
      print '(A,2(1X,F15.7))', 'B0_SMOKE', DBLE(result), DIMAG(result)
      call ltexi
      end
