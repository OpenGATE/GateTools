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

def computeDistance(mask1, mask2):
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
  return(distances)

def getHausdorffPercentile(distances12, distances21, percentile):
  d12 = distances12[int(percentile*(len(distances12)-1))]
  d21 = distances21[int(percentile*(len(distances21)-1))]
  if d12 > d21:
    return d12
  else:
    return d21

def computeHausdorff(mask1, mask2, percentile):
  d12 = computeDistance(mask1, mask2)
  d21 = computeDistance(mask2, mask1)
  return(getHausdorffPercentile(d12, d21, percentile))


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
    def test_hausdorff_percentile(self):
        logger.info('Test_HAUSDORFF test_hausdorff_percentile')
        #square image
        size = 100 #px
        array1 = np.zeros((size, size, size))
        array1[10:35, 10:35, 50] = 1
        mask1 = itk.image_from_array(np.int16(array1))
        mask1.SetOrigin([7, 3.4, -4.6])
        mask1.SetSpacing([1, 1, 3.6])
        itk.imwrite(mask1, "mask1.mhd")

        array2 = np.zeros((size, size, size))
        array2[10:35, 10:35, 50] = 1
        array2[20:21, 35:75, 50] = 1
        mask2 = itk.image_from_array(np.int16(array2))
        mask2.SetOrigin([7, 3.4, -4.6])
        mask2.SetSpacing([1, 1, 3.6])
        itk.imwrite(mask2, "mask2.mhd")

        d12 = computeDistance(mask1, mask2)
        d21 = computeDistance(mask2, mask1)
        hausdorffDistance = getHausdorffPercentile(d12, d21, 1.0)
        print(hausdorffDistance)
        self.assertTrue(np.isclose(hausdorffDistance, 80.0))
        #print(d12)
        #print(d21)
        hausdorffDistance = getHausdorffPercentile(d12, d21, 0.95)
        print(hausdorffDistance)
        #self.assertTrue(np.isclose(hausdorffDistance, 0.0, atol=1e-7))

        #pymia
        '''
        import pymia.evaluation.metric as metric
        import pymia.evaluation.evaluator as eval_
        labels = {1: "ROI" }
        metrics = [metric.HausdorffDistance(percentile=100, metric='HDmax'),metric.HausdorffDistance(percentile=95, metric='HD95')]
        evaluator = eval_.SegmentationEvaluator(metrics, labels)
        evaluator.evaluate(itk.array_from_image(mask1), itk.array_from_image(mask2), "T")
        for r in evaluator.results:
          print(r.value)
        '''

