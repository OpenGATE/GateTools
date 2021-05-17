# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""

This module provides a function to convert image from one type to another:

"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import itk
import pydicom
from pydicom.tag import Tag
import gatetools as gt
import numpy as np
import logging
logger=logging.getLogger(__name__)

def convertRadiusToPx(radius, spacing):
    newRadius = []
    for r, s in zip(radius, spacing):
        newRadius.append(int(r/s))
    return(newRadius)


def morpho_math(inputImage, morphotype, radius):
    """
    Compute morpho operation
    """
    ImageType = type(inputImage)

    #Set the kernel element
    StructuringElementType = itk.FlatStructuringElement[inputImage.GetImageDimension()]
    structuringElement = StructuringElementType.Ball(radius)
    structuringElement.SetRadiusIsParametric(True)

    #Choose the morphological operation
    if morphotype == 0:
        MorphoFilterType = itk.BinaryDilateImageFilter[ImageType, ImageType, StructuringElementType]
    elif morphotype == 1:
        MorphoFilterType = itk.BinaryErodeImageFilter[ImageType, ImageType, StructuringElementType]
    elif morphotype == 2:
        MorphoFilterType = itk.BinaryMorphologicalClosingImageFilter[ImageType, ImageType, StructuringElementType]
    elif morphotype == 3:
        MorphoFilterType = itk.BinaryMorphologicalOpeningImageFilter[ImageType, ImageType, StructuringElementType]
    else:
        print("Error: choose a correct morpho type")
        return None

    #Compute the operation
    morphoFilter = MorphoFilterType.New()
    morphoFilter.SetInput(inputImage)
    morphoFilter.SetKernel(structuringElement)
    morphoFilter.SetForegroundValue(1)
    morphoFilter.Update()
    output = morphoFilter.GetOutput()
    output.CopyInformation(inputImage)
    return (output)



#####################################################################################
import unittest
import hashlib
import os
import tempfile
import shutil
import wget
from .logging_conf import LoggedTestCase

def createImage():
        Dimension = 3
        PixelType = itk.ctype('unsigned char')
        ImageType = itk.Image[PixelType, Dimension]

        image = ImageType.New()
        start = itk.Index[Dimension]()
        start[0] = 0
        start[1] = 0
        start[2] = 0
        size = itk.Size[Dimension]()
        size[0] = 200
        size[1] = 200
        size[2] = 200
        region = itk.ImageRegion[Dimension]()
        region.SetSize(size)
        region.SetIndex(start)
        image.SetRegions(region)
        image.Allocate()
        image.FillBuffer(0)
        npView = itk.array_from_image(image)
        npView[10:52, 42:192, 124:147] =1
        npView[26:30, 42:149, 132:138] =0
        npView[26:30, 151:192, 132:138] =0
        image = itk.image_from_array(npView)
        return image

class Test_Morpho_Math(LoggedTestCase):
    def test_morpho_math_dilatation(self):
        image = createImage()
        output = morpho_math(image, 0, [2, 3, 4])
        outputStats = gt.imageStatistics(input=output)
        self.assertTrue(outputStats["sum"] == 208836)
    def test_morpho_math_dilatation_mm(self):
        image = createImage()
        image.SetSpacing([2, 3, 4])
        radius = [2, 3, 4]
        newRadius = convertRadiusToPx(radius, image.GetSpacing())
        output = morpho_math(image, 0, newRadius)
        outputStats = gt.imageStatistics(input=output)
        self.assertTrue(outputStats["sum"] == 166008)
    def test_morpho_math_erosion(self):
        image = createImage()
        output = morpho_math(image, 1, [2, 3, 4])
        outputStats = gt.imageStatistics(input=output)
        self.assertTrue(outputStats["sum"] == 76904)
    def test_morpho_math_closing(self):
        image = createImage()
        output = morpho_math(image, 2, [2, 3, 4])
        outputStats = gt.imageStatistics(input=output)
        self.assertTrue(outputStats["sum"] == 144900)
    def test_morpho_math_opening(self):
        image = createImage()
        output = morpho_math(image, 3, [2, 3, 4])
        outputStats = gt.imageStatistics(input=output)
        self.assertTrue(outputStats["sum"] == 139576)

