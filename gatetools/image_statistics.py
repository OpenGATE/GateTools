# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides basic affine transformation and resampling methods for images.
"""

import gatetools as gt
import itk
import numpy as np
import logging
logger=logging.getLogger(__name__)

def imageStatistics(input=None, mask=None, resample=False, histogramBins=1000):

    if input is None:
        logger.error("Set an input")
        sys.exit(1)

    inputArray = itk.array_from_image(input)
    outputStats = {}
    outputStats["nbPixel"] = inputArray.size
    if not mask is None:
        if resample:
            mask = gt.applyTransformation(input=mask, like=input, force_resample=True)
        if not np.allclose(mask.GetSpacing(), input.GetSpacing()):
            logger.error("Input and mask do not have the same spacing")
            sys.exit(1)
        if not np.allclose(mask.GetOrigin(), input.GetOrigin()):
            logger.error("Input and mask do not have the same origin")
            sys.exit(1)
        if not np.allclose(itk.array_from_matrix(mask.GetDirection()), itk.array_from_matrix(input.GetDirection())):
            logger.error("Input and mask do not have the same direction")
            sys.exit(1)
        if not np.allclose(mask.GetLargestPossibleRegion().GetSize(),  input.GetLargestPossibleRegion().GetSize()):
            logger.error("Input and mask do not have the same size")
            sys.exit(1)

        maskArray = itk.array_from_image(mask)
        if len(np.where(maskArray > 1)[0]) >0:
            logger.error("The mask seems to be a non-binary image")
        index = np.where(maskArray == 1)
        outputStats["nbPixel"] = len(index[0])
        inputArray = inputArray[index]

    outputStats["minimum"] = np.amin(inputArray)
    outputStats["maximum"] = np.amax(inputArray)
    outputStats["sum"] = np.sum(inputArray)
    outputStats["median"] = np.median(inputArray)
    outputStats["mean"] = np.mean(outputStats["sum"]/outputStats["nbPixel"])
    outputStats["variance"] = np.var(inputArray)
    outputStats["sigma"] = np.sqrt(outputStats["variance"])
    outputStats["hist"] = np.histogram(inputArray, histogramBins)

    return outputStats
    

#####################################################################################
import unittest
import sys
from datetime import datetime
import tempfile
import hashlib
import shutil
from .logging_conf import LoggedTestCase

def createImageExample():
    x = np.arange(-10, 10, 1)
    y = np.arange(-12, 15, 1)
    z = np.arange(-13, 10, 1)
    xx, yy, zz = np.meshgrid(x, y, z)
    image = itk.image_from_array(np.int16(xx))
    image.SetOrigin([7, 3.4, -4.6])
    image.SetSpacing([4, 2, 3.6])
    return image

class Test_Image_Statistics(LoggedTestCase):
    def test_image_statistics(self):
        logger.info('Test_Image_Statistics test_image_statistics')
        image = createImageExample()
        outputStats = imageStatistics(input=image, histogramBins=10)
        self.assertTrue(outputStats["nbPixel"] == 12420)
        self.assertTrue(outputStats["mean"] == -0.5)
        self.assertTrue(outputStats["median"] == -0.5)
        self.assertTrue(outputStats["sum"] == -6210)
        self.assertTrue(outputStats["minimum"] == -10)
        self.assertTrue(outputStats["maximum"] == 9)
        self.assertTrue(outputStats["variance"] == 33.25)
        self.assertTrue(outputStats["sigma"] == 5.766281297335398)
        self.assertTrue(np.allclose(outputStats["hist"][0], [1242, 1242, 1242, 1242, 1242, 1242, 1242, 1242, 1242, 1242]))
        self.assertTrue(np.allclose(outputStats["hist"][1], [-10. , -8.1, -6.2, -4.3, -2.4, -0.5, 1.4, 3.3, 5.2, 7.1, 9.]))

    def test_image_statistics_with_mask(self):
        logger.info('Test_Image_Statistics test_image_statistics_with_mask')
        image = createImageExample()
        mask = createImageExample()
        x = np.arange(-10, 10, 1)
        y = np.arange(-12, 15, 1)
        z = np.arange(-13, 10, 1)
        xx, yy, zz = np.meshgrid(x, y, z)
        mask = np.int16(xx)
        mask[:] = 0
        mask[:, 11, :] = 1
        mask = itk.image_from_array(mask)
        mask.SetOrigin([7, 3.4, -4.6])
        mask.SetSpacing([4, 2, 3.6])
        outputStats = imageStatistics(input=image, mask=mask, histogramBins=5)
        self.assertTrue(outputStats["nbPixel"] == 621)
        self.assertTrue(outputStats["mean"] == 1)
        self.assertTrue(outputStats["median"] == 1)
        self.assertTrue(outputStats["sum"] == 621)
        self.assertTrue(outputStats["minimum"] == 1)
        self.assertTrue(outputStats["maximum"] == 1)
        self.assertTrue(outputStats["variance"] == 0)
        self.assertTrue(outputStats["sigma"] == 0)
        self.assertTrue(np.allclose(outputStats["hist"][0], [0, 0, 621, 0, 0]))
        self.assertTrue(np.allclose(outputStats["hist"][1], [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]))

    def test_image_statistics_with_mask_and_resample(self):
        logger.info('Test_Image_Statistics test_image_statistics_with_mask')
        image = createImageExample()
        mask = createImageExample()
        x = np.arange(-10, 10, 1)
        y = np.arange(-12, 15, 1)
        z = np.arange(-13, 10, 1)
        xx, yy, zz = np.meshgrid(x, y, z)
        mask = np.int16(xx)
        mask[:] = 0
        mask[:, 11, :] = 1
        mask = itk.image_from_array(mask)
        mask.SetOrigin([3, 3.4, -4.6])
        mask.SetSpacing([4, 2, 3.6])
        outputStats = imageStatistics(input=image, mask=mask, resample=True, histogramBins=7)
        self.assertTrue(outputStats["nbPixel"] == 594)
        self.assertTrue(outputStats["mean"] == 1)
        self.assertTrue(outputStats["median"] == 1)
        self.assertTrue(outputStats["sum"] == 594)
        self.assertTrue(outputStats["minimum"] == 1)
        self.assertTrue(outputStats["maximum"] == 1)
        self.assertTrue(outputStats["variance"] == 0)
        self.assertTrue(outputStats["sigma"] == 0)
        self.assertTrue(np.allclose(outputStats["hist"][0], [0, 0, 0, 594, 0, 0, 0]))
        self.assertTrue(np.allclose(outputStats["hist"][1], [0.5, 0.64285714, 0.78571429, 0.92857143, 1.07142857, 1.21428571, 1.35714286, 1.5]))
