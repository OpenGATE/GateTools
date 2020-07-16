# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides resizing (pad or crop) for images.
"""

import os
import itk
import numpy as np
import math
import gatetools as gt
import logging
logger=logging.getLogger(__name__)

def imageResize(input=None, newsize=None,  newsize_mm=None, pad=None):
    if input is None:
        logger.error("Set the input")
        sys.exit(1)
    if newsize is None and newsize_mm is None:
        logger.error("Choose between newsize and newsize_mm options")
        sys.exit(1)
    if newsize is not None and newsize_mm is not None:
        logger.error("Choose between newsize and newsize_mm")
        sys.exit(1)

    if pad is None:
        pad = 0.0

    imageDimension = input.GetImageDimension()
    itkSize = itk.Size[imageDimension]()
    if newsize is None:
        for i in range(imageDimension):
            itkSize[i] = int(round(newsize_mm[i]/input.GetSpacing()[i], 0))
    else:
        for i in range(imageDimension):
            itkSize[i] = newsize[i]

    differenceSize = [0]*imageDimension
    for i in range(imageDimension):
        differenceSize[i] = itkSize[i] - input.GetLargestPossibleRegion().GetSize()[i]

    newSize = itk.Size[imageDimension]()
    newOrigin = itk.Point[itk.F, imageDimension]()
    newTranslation = itk.Point[itk.F, imageDimension]()
    for i in range(imageDimension):
        if differenceSize[i] > 0:
            newSize[i] = itkSize[i]
            if differenceSize[i]%2 ==0:
                newTranslation[i] = -differenceSize[i]/2*input.GetSpacing()[i]
            else:
                newTranslation[i] = -(differenceSize[i]+1)/2*input.GetSpacing()[i]
            newOrigin[i] = input.GetOrigin()[i] + newTranslation[i]
        elif differenceSize[i] < 0:
            newSize[i] = itkSize[i]
            if differenceSize[i]%2 ==0:
                newTranslation[i] = -differenceSize[i]/2*input.GetSpacing()[i]
            else:
                newTranslation[i] = -(differenceSize[i]+1)/2*input.GetSpacing()[i]
            newOrigin[i] = input.GetOrigin()[i] + newTranslation[i]
        else:
            newSize[i] = input.GetLargestPossibleRegion().GetSize()[i]
            newTranslation[i] = 0
            newOrigin[i] = input.GetOrigin()[i]
    outputImage = gt.applyTransformation(input, newsize = newSize, force_resample = True, translation = newTranslation, pad = pad)
    outputImage = gt.applyTransformation(outputImage, neworigin = newOrigin)

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

class Test_Image_Resize(LoggedTestCase):
    def test_image_resize(self):
        logger.info('Test_Image_resize test_image_resize')
        image = createImageExample()
        itkSize = itk.Size[3]()
        itkSize[0] = 30
        itkSize[1] = 16
        itkSize[2] = 27
        transformImage = imageResize(input=image, newsize=itkSize, pad=30)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testImageResample.mha"))
        with open(os.path.join(tmpdirpath, "testImageResample.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("40c6f1505e19c76a5a12c138cc8028e84be0ae98607aeb0c151a6240600eae48" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_image_resize_mm(self):
        logger.info('Test_Image_resize test_image_resize_mm')
        image = createImageExample()
        itkSize = itk.Point[itk.F, 3]()
        itkSize[0] = 120
        itkSize[1] = 32
        itkSize[2] = 97.2
        transformImage = imageResize(input=image, newsize_mm=itkSize, pad=30)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testImageResample.mha"))
        itk.imwrite(image, os.path.join(tmpdirpath, "input.mha"))
        with open(os.path.join(tmpdirpath, "testImageResample.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("40c6f1505e19c76a5a12c138cc8028e84be0ae98607aeb0c151a6240600eae48" == new_hash)
        shutil.rmtree(tmpdirpath)
