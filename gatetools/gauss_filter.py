# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides basic gauss filtering for images.
"""

import os
import itk
import numpy as np
import math
import logging
logger=logging.getLogger(__name__)

def gaussFilter(input=None, sigma=None, sigma_mm=None, float=False):

    if input is None:
        logger.error("Set the input")
        sys.exit(1)
    if sigma is None and sigma_mm is None:
        logger.error("Choose between sigma and sigma_mm options")
        sys.exit(1)
    if sigma is not None and sigma_mm is not None:
        logger.error("Choose between sigma and sigma_mm")
        sys.exit(1)

    imageDimension = input.GetImageDimension()
    if sigma_mm is None:
        sigma_mm = [0]*imageDimension
        for i in range(0, imageDimension):
            sigma_mm[i] = sigma[i]*input.GetSpacing()[i]

    tempImageType = itk.Image[itk.F, imageDimension]
    castImageFilter = itk.CastImageFilter[type(input), tempImageType].New()
    castImageFilter.SetInput(input)
    castImageFilter.Update()

    duplicator = itk.ImageDuplicator[tempImageType].New()
    duplicator.SetInputImage(castImageFilter.GetOutput())
    duplicator.Update()
    outputImage = duplicator.GetOutput()
    for i in range(0, imageDimension):
        if sigma_mm[i] >0:
            gaussFilter = itk.RecursiveGaussianImageFilter[tempImageType, tempImageType].New()
            gaussFilter.SetInput(outputImage)
            gaussFilter.SetDirection(i)
            gaussFilter.SetOrder(0)
            gaussFilter.SetNormalizeAcrossScale(False)
            gaussFilter.SetSigma(sigma_mm[i]) # in mm
            gaussFilter.Update()
            outputImage = gaussFilter.GetOutput()
    if not float:
        castImageFilter2 = itk.CastImageFilter[tempImageType, type(input)].New()
        castImageFilter2.SetInput(outputImage)
        castImageFilter2.Update()
        outputImage = castImageFilter2.GetOutput()

    return outputImage

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

class Test_Image_Gauss(LoggedTestCase):
    def test_image_gauss(self):
        logger.info('Test_Image_Gauss test_image_gauss')
        image = createImageExample()
        transformImage = gaussFilter(input=image, sigma_mm=[0, 2, 0])
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testGauss.mha"))
        with open(os.path.join(tmpdirpath, "testGauss.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("c0b6c44826308f94a76192ee6c32ba173f180a627a0e82b8651f899b3545f230" == new_hash)
        shutil.rmtree(tmpdirpath)
