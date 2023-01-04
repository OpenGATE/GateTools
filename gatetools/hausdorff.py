# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import os
import itk
import numpy as np
import logging
logger=logging.getLogger(__name__)

def computeMaxDistance(mask1, mask2, percentile):
  OutputPixelType = itk.ctype('float')
  OutputImageType = itk.Image[OutputPixelType, mask1.GetImageDimension()]
  caster1 = itk.CastImageFilter[type(mask1), OutputImageType].New()
  caster1.SetInput(mask1)
  caster1.Update()
  masks1_float = caster1.GetOutput()
  caster2 = itk.CastImageFilter[type(mask2), OutputImageType].New()
  caster2.SetInput(mask2)
  caster2.Update()
  masks2_float = caster2.GetOutput()

  SignedMaurerDistanceMapImageFilter = itk.SignedMaurerDistanceMapImageFilter[itk.Image[itk.F, 3], itk.Image[itk.F, 3]].New()
  SignedMaurerDistanceMapImageFilter.InsideIsPositiveOff()
  SignedMaurerDistanceMapImageFilter.SetInput(masks2_float)
  SignedMaurerDistanceMapImageFilter.SquaredDistanceOff()
  SignedMaurerDistanceMapImageFilter.UseImageSpacingOn()
  SignedMaurerDistanceMapImageFilter.Update()
  distMap2 = SignedMaurerDistanceMapImageFilter.GetOutput()

  distInterp2 = itk.BSplineInterpolateImageFunction[type(distMap2), itk.D, itk.F].New()
  distInterp2.SetInputImage(distMap2)
  distInterp2.SetSplineOrder(3)

  distances = []
  index = np.where(itk.array_from_image(masks1_float) != 0)
  for i in range(len(index[0])):
    itkIndex = [int(index[2][i]), int(index[1][i]), int(index[0][i])]
    point = masks1_float.TransformIndexToPhysicalPoint(itkIndex)
    distance = distInterp2.Evaluate(point)
    if distance >= 0:
      distances.append(distance)
  distances.sort()
  if len(distances) == 0:
      distances.append(0.0)
  return(distances[int(percentile*(len(distances)-1))])

def computeHausdorff(mask1, mask2, percentile):
  d12 = computeMaxDistance(mask1, mask2, percentile)
  d21 = computeMaxDistance(mask2, mask1, percentile)
  if d12 > d21:
    return d12
  else:
    return d21


#####################################################################################
import unittest
import sys
from datetime import datetime
import tempfile
import hashlib
import shutil
import wget
import pydicom
import gatetools as gt
from matplotlib import pyplot as plt
from .logging_conf import LoggedTestCase

def createSphereExample(x0, y0, z0):
    size = 20 #px
    array = np.zeros((size, size, size))
    radius = 3 #px
    for i in range(size):
        for j in range(size):
            for k in range(size):
                if (i - x0)*(i - x0) + (j - y0)*(j - y0) + (k - z0)*(k - z0)<= radius * radius:
                    array[i, j, k] = 1
    
    image = itk.image_from_array(np.int16(array))
    image.SetOrigin([7, 3.4, -4.6])
    image.SetSpacing([4, 2, 3.6])
    return image

class Test_HAUSDORFF(LoggedTestCase):
    def test_hausdorff(self):
        logger.info('Test_HAUSDORFF test_hausdorff')
        mask1 = createSphereExample(10, 10, 10)
        mask2 = createSphereExample(10, 11, 10)
        hausdorffDistance = computeHausdorff(mask1, mask2, 1.0)
        self.assertTrue(np.isclose(hausdorffDistance, 2.0))


