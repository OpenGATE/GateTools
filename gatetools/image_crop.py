# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""

This module provides a function to crop image

"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import itk
import gatetools as gt
import numpy as np
import logging
logger=logging.getLogger(__name__)

def image_auto_crop(img, bg=0):
    """
    Crop an image according to a background value. Only for integer PixelType
    """

    # Img image type
    ImageType = type(img)
    Dim = 3
    dims = np.array(img.GetLargestPossibleRegion().GetSize())
    if len(dims) != 3:
        logger.error('only 3D image supported')
        exit(0)

    # check image type: LabelImageToLabelMapFilter only allow unsigned short/char
    # for float -> cannot do it
    # for int   -> cannot do it
    # for char/short -> offset if negative value
    PixelType = itk.template(img)[1][0]

    if PixelType == itk.ctype('float'):
        logger.error('Cannot crop for float or double PixelType. Only char/short supported')
        exit(0)

    if PixelType == itk.ctype('int'):
        logger.error('Cannot crop for int PixelType. Only char/short supported')
        exit(0)

    # special case for negative value
    img_array = itk.array_view_from_image(img)
    minv = np.min(img_array)
    bg = int(bg)
    if minv<0:
        img_array -= minv
        bg -= minv
    # force to integer
    bg = int(bg)
    #print(itk.LabelImageToLabelMapFilter.GetTypes())
    #print(itk.StatisticsLabelObject.GetTypes())

    # Cast to an image type which is compatible (ushort)
    OutputPixelType = itk.ctype('unsigned short')
    OutputImageType = itk.Image[OutputPixelType, Dim]
    caster = itk.CastImageFilter[ImageType, OutputImageType].New()
    caster.SetInput(img)
    caster.Update()
    img = caster.GetOutput()
    TempImageType = type(img)

    # create filters for crop
    LabelType = itk.ctype('unsigned long')
    LabelObjectType = itk.StatisticsLabelObject[LabelType, Dim]
    LabelMapType = itk.LabelMap[LabelObjectType]
    converter = itk.LabelImageToLabelMapFilter[TempImageType, LabelMapType].New()
    converter.SetBackgroundValue(bg);
    converter.SetInput(img);
    autocrop = itk.AutoCropLabelMapFilter[LabelMapType].New()
    autocrop.SetInput(converter.GetOutput())
    remap = itk.LabelMapToLabelImageFilter[LabelMapType, TempImageType].New()
    remap.SetInput(autocrop.GetOutput())

    # recast to initial type
    endcaster = itk.CastImageFilter[TempImageType, ImageType].New()
    endcaster.SetInput(remap.GetOutput())

    # Go !
    endcaster.Update()
    output = endcaster.GetOutput()

    # Offset if negative
    if minv<0:
        img_array = itk.array_view_from_image(output)
        img_array += minv

    return output



def image_crop_with_bb(img, bb):
    """
    Crop an image according to a bounding box (see "bounding_box" module).
    """
    dims = np.array(img.GetLargestPossibleRegion().GetSize())
    if len(dims) != 3:
        logger.error('only 3D image supported')
        exit(0)
    #inclusive
    from_index = np.maximum(np.zeros(3,dtype=int),np.array(img.TransformPhysicalPointToIndex(bb.mincorner)))
    #exclusive
    to_index = np.minimum(dims,np.array(img.TransformPhysicalPointToIndex(bb.maxcorner))+1)
    cropper = itk.RegionOfInterestImageFilter.New(Input=img)
    region = cropper.GetRegionOfInterest()
    indx=region.GetIndex()
    size=region.GetSize()
    for j in range(3):
        indx.SetElement(j,int(from_index[j]))
        size.SetElement(j,int(to_index[j]-from_index[j]))
    region.SetIndex(indx)
    region.SetSize(size)
    cropper.SetRegionOfInterest(region)
    cropper.Update()
    return cropper.GetOutput()

#####################################################################################
import unittest
from .logging_conf import LoggedTestCase

class Test_Crop(LoggedTestCase):
    def test_auto_crop(self):
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
        image = itk.image_from_array(npView)
        autoCrop = image_auto_crop(image)
        autoCropSize = autoCrop.GetLargestPossibleRegion().GetSize()
        self.assertTrue(np.allclose(autoCropSize[0], 23))
        self.assertTrue(np.allclose(autoCropSize[1], 150))
        self.assertTrue(np.allclose(autoCropSize[2], 42))
        self.assertTrue(np.allclose(itk.array_from_image(autoCrop)[0, 0, 0], 1))
    def test_crop(self):
        x = np.arange(-10, 10, 0.1)
        y = np.arange(-12, 15, 0.1)
        z = np.arange(-13, 10, 0.1)
        xx, yy, zz = np.meshgrid(x, y, z)
        image = itk.image_from_array(np.float32(xx))
        croppedImage = image_crop_with_bb(image, gt.bounding_box(xyz=[10.0, 12.0, 0.0, 7.0, 6.0, 15.0]))
        croppedImageSize = croppedImage.GetLargestPossibleRegion().GetSize()
        self.assertTrue(np.allclose(croppedImageSize[0], 3))
        self.assertTrue(np.allclose(croppedImageSize[1], 8))
        self.assertTrue(np.allclose(croppedImageSize[2], 10))
        self.assertTrue(np.allclose(itk.array_from_image(croppedImage)[0, 0, 0], -10))
