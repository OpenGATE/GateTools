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

def read_dicom(dicomFiles):
    """

    Read dicom files and return an float 3D image
    """
    files = []
    #Load dicom files
    for file in dicomFiles:
        files.append(pydicom.read_file(file))

    # skip files with no SliceLocation (eg scout views)
    slices = []
    skipcount = 0
    if len(files) > 1:
        for f in files:
            if hasattr(f, 'SliceLocation'):
                slices.append(f)
            else:
                skipcount = skipcount + 1

        if skipcount >0:
            logger.info("skipped, no SliceLocation: {}".format(skipcount))

        # ensure they are in the correct order
        slices = sorted(slices, key=lambda s: s.SliceLocation)
    else:
        logger.error('no file available')
        return


    # pixel aspects, assuming all slices are the same
    ps = slices[0].PixelSpacing
    ss = slices[0].SliceThickness
    spacing = [ps[0], ps[1], ss]
    if Tag(0x20, 0x32) in slices[0]:
        ip = slices[0][0x20, 0x32].value #Image Position
    else:
        ip = slices[0][0x54, 0x22][0][0x20, 0x32].value #Image Position
    origin = [ip[0], ip[1], ip[2]]
    if Tag(0x20, 0x37) in slices[0]:
        io = slices[0][0x20, 0x37].value #Image Orientation
    else:
        io = slices[0][0x54, 0x22][0][0x20, 0x37].value #Image Orientation
    #orientation = [io[0], io[1], io[2], io[3], io[4], io[5]]
    if Tag(0x28, 0x1052) in slices[0]:
        ri = slices[0][0x28, 0x1052].value #Rescale Intercept
        rs = slices[0][0x28, 0x1053].value #Rescale Slope
    elif Tag(0x11, 0x103b) in slices[0]:
        rs = slices[0][0x11, 0x103b].value #Rescale Intercept
        ri = slices[0][0x11, 0x103c].value #Rescale Slope
    elif Tag(0x40, 0x9096) in slices[0]:
        ri = slices[0][0x40, 0x9096][0][0x40, 0x9224].value #Rescale Intercept
        rs = slices[0][0x40, 0x9096][0][0x40, 0x9225].value #Rescale Slope

    # create 3D array
    img_shape = list(slices[0].pixel_array.shape)
    img_shape[0] = len(slices)
    img_shape.append(slices[0].pixel_array.shape[0])
    img3d = np.zeros(img_shape)

    # fill 3D array with the images from the files
    for i, s in enumerate(slices):
        img2d = s.pixel_array
        img3d[i, :, :] = img2d
    img3d = rs*img3d+ri

    img_result = itk.image_from_array(np.float32(img3d))
    img_result.SetSpacing(spacing)
    img_result.SetOrigin(origin)
    arrayDirection = np.zeros([3,3], np.float64)
    arrayDirection[0,0] = io[0]
    arrayDirection[0,1] = io[1]
    arrayDirection[0,2] = io[2]
    arrayDirection[1,0] = io[3]
    arrayDirection[1,1] = io[4]
    arrayDirection[1,2] = io[5]
    arrayDirection[2,2] = 1.0
    matrixItk = itk.Matrix[itk.D,3,3](itk.GetVnlMatrixFromArray(arrayDirection))
    img_result.SetDirection(matrixItk)
    return img_result

def read_3d_dicom(dicomFile):
    """

    Read dicom file and return an float 3D image
    """
    files = []
    files.append(pydicom.read_file(dicomFile[0]))

    # skip files with no SliceLocation (eg scout views)
    slices = []
    if len(files) == 1:
        slices.append(files[0])
    else:
        logger.error('no file available')
        return


    # pixel aspects, assuming all slices are the same
    ps = slices[0].PixelSpacing
    ss = slices[0].SliceThickness
    spacing = [ps[0], ps[1], ss]
    if Tag(0x20, 0x32) in slices[0]:
        ip = slices[0][0x20, 0x32].value #Image Position
    else:
        ip = slices[0][0x54, 0x22][0][0x20, 0x32].value #Image Position
    origin = [ip[0], ip[1], ip[2]]
    if Tag(0x20, 0x37) in slices[0]:
        io = slices[0][0x20, 0x37].value #Image Orientation
    else:
        io = slices[0][0x54, 0x22][0][0x20, 0x37].value #Image Orientation
    rs = 1.0
    ri = 0.0
    if Tag(0x28, 0x1052) in slices[0]:
        ri = slices[0][0x28, 0x1052].value #Rescale Intercept
        rs = slices[0][0x28, 0x1053].value #Rescale Slope
    elif Tag(0x11, 0x103b) in slices[0]:
        rs = slices[0][0x11, 0x103b].value #Pixel Scale
        ri = slices[0][0x11, 0x103c].value #Pixel Offset
    elif Tag(0x40, 0x9096) in slices[0]:
        ri = slices[0][0x40, 0x9096][0][0x40, 0x9224].value #Rescale Intercept
        rs = slices[0][0x40, 0x9096][0][0x40, 0x9225].value #Rescale Slope

    # create 3D array
    img_shape = list(slices[0].pixel_array.shape)
    img3d = np.zeros(img_shape)

    # fill 3D array with the images from the files
    img3d[:, :, :] = slices[0].pixel_array
    img3d = rs*img3d+ri

    img_result = itk.image_from_array(np.float32(img3d))
    img_result.SetSpacing(spacing)
    img_result.SetOrigin(origin)
    arrayDirection = np.zeros([3,3], np.float64)
    arrayDirection[0,0] = io[0]
    arrayDirection[0,1] = io[1]
    arrayDirection[0,2] = io[2]
    arrayDirection[1,0] = io[3]
    arrayDirection[1,1] = io[4]
    arrayDirection[1,2] = io[5]
    if slices[0][0x18, 0x88].value <0:
        arrayDirection[2,2] = -1.0
    else:
        arrayDirection[2,2] = 1.0
    matrixItk = itk.Matrix[itk.D,3,3](itk.GetVnlMatrixFromArray(arrayDirection))
    img_result.SetDirection(matrixItk)
    return img_result

def image_convert(inputImage, pixeltype=None):
    """
    Compute relative statistical uncertainty 

    - inputImage: input itk image to convert
    - pixeltype: string representing the type of the output pixel:
        - unsigned char
        - signed short
        - unsigned short
        - float
    """

    #If pixel type is not None, convert it,
    #If None it could be a type conversion without pixel conversion
    if pixeltype is not None:
        InputType = type(inputImage)
        OutputType = itk.Image[itk.ctype(pixeltype), inputImage.GetImageDimension()]
        castFilter = itk.CastImageFilter[InputType, OutputType].New()
        castFilter.SetInput(inputImage)
        return castFilter

    return inputImage

#####################################################################################
import unittest
import hashlib
import os
import tempfile
import shutil
from .logging_conf import LoggedTestCase

class Test_Convert(LoggedTestCase):
    def test_convert(self):
        x = np.arange(-10, 10, 1)
        y = np.arange(-12, 15, 1)
        z = np.arange(-13, 10, 1)
        xx, yy, zz = np.meshgrid(x, y, z)
        image = itk.image_from_array(np.float32(xx))
        convertedImage = image_convert(image, "unsigned char")
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("da57bf05ec62b9b5ee2aaa71aacbf7dbca8acbf2278553edc499a3af8007dd44" == new_hash)
        shutil.rmtree(tmpdirpath)
