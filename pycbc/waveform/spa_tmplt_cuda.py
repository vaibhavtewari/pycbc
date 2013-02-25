#  
#  Apapted from code in LALSimInpspiralTaylorF2.c 
# 
#  Copyright (C) 2007 Jolien Creighton, B.S. Sathyaprakash, Thomas Cokelaer
#  Copyright (C) 2012 Leo Singer, Alex Nitz
#  Adapted from code found in:
#    - LALSimInspiralTaylorF2.c
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with with program; see the file COPYING. If not, write to the
#  Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#  MA  02111-1307  USA

import lal
import numpy
from numpy import sqrt, log
from math import frexp

import pycuda.tools
from pycuda.elementwise import ElementwiseKernel
from pycuda.gpuarray import to_gpu

from pycbc.setuputils import pkg_config_header_strings
from pycbc.types import FrequencySeries, zeros, Array, complex64
import pycbc.pnutils

preamble = """
#include <lal/LALConstants.h>
"""
 
taylorf2_text = """
    const float f = (i + kmin ) * delta_f;
    const float v =  __powf(piM*f, 1.0/3.0);
    const float v2 = v * v;
    const float v3 = v2 * v;
    const float v4 = v2 * v2;
    const float v5 = v2 * v3;
    const float v6 = v3 * v3;
    const float v7 = v3 * v4;
    float phasing = 0.;
    float shft = -LAL_TWOPI * tC;
    
    float log4 = 1.386294361;
    float logv = __logf(v);

    switch (phase_order)
    {
        case -1:
        case 7:
            phasing += pfa7 * v7;
        case 6:
            phasing += (pfa6 + pfl6 * (logv + log4) ) * v6;
        case 5:
            phasing += (pfa5 + pfl5 * (logv - lv0) ) * v5;
        case 4:
            phasing += pfa4 * v4;
        case 3:
            phasing += pfa3 * v3;
        case 2:
            phasing += pfa2 * v2;
        case 0:
            phasing += 1.;
            break;
        default:
            break;
    }
    phasing *= pfaN / v5;
    phasing += shft * f + LAL_PI_4;
    phasing -= int(phasing / (LAL_TWOPI)) * LAL_TWOPI;

    float pcos;
    float psin;
    __sincosf(phasing, &psin, &pcos);

    htilde[i]._M_re = pcos;
    htilde[i]._M_im = - psin;

"""

taylorf2_kernel = ElementwiseKernel("""pycuda::complex<float> *htilde, int kmin, int phase_order,
                                       float delta_f, float piM, float pfaN, 
                                       float pfa2, float pfa3, float pfa4, float pfa5, float pfl5,
                                       float pfa6, float pfl6, float pfa7, float tC, float lv0""",
                    taylorf2_text, "SPAtmplt",
                    preamble=preamble, options=pkg_config_header_strings(['lal']))

def spa_tmplt_engine(htilde,  kmin,  phase_order,
                    delta_f,  piM,  pfaN, 
                    pfa2,  pfa3,  pfa4,  pfa5,  pfl5,
                    pfa6,  pfl6,  pfa7, tC, v0):
    """ Calculate the spa tmplt phase 
    """
    taylorf2_kernel(htilde.data,  kmin,  phase_order,
                    delta_f,  piM,  pfaN, 
                    pfa2,  pfa3,  pfa4,  pfa5,  pfl5,
                    pfa6,  pfl6,  pfa7, tC, log(v0))
