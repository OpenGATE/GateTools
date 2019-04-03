"""

This module provides a function to compute relative statistical
uncertainty (typically for Edep or Dose), with the history by history
method as explained for example in [Chetty2006]

"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import itk
import gatetools as gt
from functools import reduce
import operator
import numpy as np

def image_uncertainty(img_list=[], img_squared_list=[], N=0):
    """
    Compute relative statistical uncertainty 

    - img_list and img_squared_list: lists of itk images
    - N: number of primary events
    """

    # Check size  # FIXME --> should use a similar function than the one in image_arithm. To put in gate_helpers
    first = img_list[0]
    origin = first.GetOrigin()
    spacing = first.GetSpacing()
    size = first.GetLargestPossibleRegion().GetSize()
    for img in img_list+img_squared_list:
        o = img.GetOrigin()
        sp = img.GetSpacing()
        si = img.GetLargestPossibleRegion().GetSize()
        b = np.allclose(o, origin) and np.allclose(sp,spacing) and (si == size)
        if not b:
            raise RuntimeError('Error: all images must have same origin/spacing/size. I expected {} {} {} and found {} {} {}'
                               .format(origin, spacing, size, o, sp, si))


    # Check N
    N = float(N)
    if N<0:
        raise RuntimeError('ERROR: N  must be positive')
    
    # view as np
    np_list = [ itk.GetArrayViewFromImage(img) for img in img_list]
    np_sq_list = [ itk.GetArrayViewFromImage(img) for img in img_squared_list]

    # sum # FIXME --> should use image_sum (but currently use sitk not itk)
    np_sum = reduce(operator.add, np_list)
    np_sq_sum = reduce(operator.add, np_sq_list)
    
    # debug --> OK
    if False:
        img_sum = itk.GetImageViewFromArray(np_sum)
        img_sum.CopyInformation(img_list[0])
        itk.imwrite(img_sum, 'sum.mhd')
        img_sq = itk.GetImageViewFromArray(np_sq_sum)
        img_sq.CopyInformation(img_list[0])
        itk.imwrite(img_sq, 'sq.mhd')

    # compute relative uncertainty [Chetty 2006]
    uncertainty = np.sqrt((N*np_sq_sum - np_sum*np_sum) / (N-1))/np_sum

    # np is double, convert to float32
    uncertainty = uncertainty.astype(np.float32)

    # create and return itk image
    img_uncertainty = itk.GetImageFromArray(uncertainty)
    img_uncertainty.CopyInformation(img_list[0]) 
    return img_uncertainty
