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


class dicom_properties:
    def __init__(self):
        self.spacing = [1.0, 1.0, 1.0]
        self.origin = [0.0, 0.0, 0.0]
        self.io = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.rs = 1.0
        self.ri = 0.0
        self.image_shape = []

    def read_dicom_slop_intercept(self, slice):
        if Tag(0x28, 0x1052) in slice:
            self.ri = slice[0x28, 0x1052].value #Rescale Intercept
            self.rs = slice[0x28, 0x1053].value #Rescale Slope
        elif Tag(0x11, 0x103b) in slice:
            self.rs = slice[0x11, 0x103b].value #Pixel Scale
            self.ri = slice[0x11, 0x103c].value #Pixel Offset
        elif Tag(0x40, 0x9096) in slice and Tag(0x40, 0x9224) in slice[0x40, 0x9096][0]:
            self.ri = slice[0x40, 0x9096][0][0x40, 0x9224].value #Rescale Intercept
            self.rs = slice[0x40, 0x9096][0][0x40, 0x9225].value #Rescale Slope
        elif Tag(0x3004, 0x000e) in slice:
            self.rs = slice[0x3004, 0x000e].value #Rescale Slope
        if hasattr(self.ri, '__len__'):
            self.ri = self.ri[0]
        if hasattr(self.rs, '__len__'):
            self.rs = self.rs[0]

    def read_dicom_properties(self, slice, nextSlice=None):
        # pixel aspects, assuming all slices are the same

        ps = [1.0, 1.0]
        if Tag(0x28, 0x30) in slice:
            ps = slice.PixelSpacing
        ss = None
        if Tag(0x18, 0x88) in slice:
            ss = abs(float(slice[(0x0018,0X0088)].value))
        if ss == '' or ss is None:
            if Tag(0x3004, 0x000c) in slice:
                ss = slice[0x3004, 0x000c][1] - slice[0x3004, 0x000c][0]
        if ss == '' or ss is None:
            if not nextSlice is None and Tag(0x0020, 0x0032) in slice and Tag(0x0020, 0x0032) in nextSlice:
                ss = abs(nextSlice[0x0020, 0x0032][2] - slice[0x0020, 0x0032][2])
            if ss == '' or ss is None:
                ss = 1.0
        self.spacing = [ps[1], ps[0], ss]
        ip = [0.0, 0.0, 0.0]
        if Tag(0x20, 0x32) in slice:
            ip = slice[0x20, 0x32].value #Image Position
        elif Tag(0x54, 0x22) in slice and Tag(0x20, 0x32) in slice[0x54, 0x22][0]:
            ip = slice[0x54, 0x22][0][0x20, 0x32].value #Image Position
        self.origin = [ip[0], ip[1], ip[2]]
        if Tag(0x20, 0x37) in slice:
            self.io = slice[0x20, 0x37].value #Image Orientation
        elif Tag(0x54, 0x22) in slice and Tag(0x20, 0x37) in slice[0x54, 0x22][0]:
            self.io = slice[0x54, 0x22][0][0x20, 0x37].value #Image Orientation
        if self.io == "" or self.io == None:
            self.io = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        #orientation = [io[0], io[1], io[2], io[3], io[4], io[5]]
        self.read_dicom_slop_intercept(slice)


        self.img_shape = list(slice.pixel_array.shape)


def read_dicom(dicomFiles):
    """

    Read dicom files and return an float 3D image
    """
    files = []
    #Load dicom files
    for file in dicomFiles:
        try:
            files.append(pydicom.read_file(file))
        except pydicom.errors.InvalidDicomError:
            ds = pydicom.read_file(file, force=True)
            ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            files.append(ds)

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

        # ensure they are in the correct order. Sort according Image Position along z
        slices = sorted(slices, key=lambda s: s[0x0020, 0x0032][2])
    else:
        logger.error('no file available')
        return

    if len(slices) == 0:
        logger.error('no slice available')
        return

    dicomProperties = dicom_properties()
    if len(slices) >= 2:
        dicomProperties.read_dicom_properties(slices[0], slices[1])
    else:
        dicomProperties.read_dicom_properties(slices[0])

    # create 3D array
    dicomProperties.img_shape[0] = len(slices)
    dicomProperties.img_shape.append(slices[0].pixel_array.shape[0])
    img3d = np.zeros(dicomProperties.img_shape)

    # fill 3D array with the images from the files
    for i, s in enumerate(slices):
        img2d = s.pixel_array
        dicomPropertiesSlice = dicom_properties()
        dicomPropertiesSlice.read_dicom_slop_intercept(s)
        img3d[i, :, :] = dicomPropertiesSlice.rs*img2d+dicomPropertiesSlice.ri

    img_result = itk.image_from_array(np.float32(img3d))
    img_result.SetSpacing(dicomProperties.spacing)
    img_result.SetOrigin(dicomProperties.origin)
    arrayDirection = np.zeros([3,3], np.float64)
    arrayDirection[0,0] = dicomProperties.io[0]
    arrayDirection[0,1] = dicomProperties.io[1]
    arrayDirection[0,2] = dicomProperties.io[2]
    arrayDirection[1,0] = dicomProperties.io[3]
    arrayDirection[1,1] = dicomProperties.io[4]
    arrayDirection[1,2] = dicomProperties.io[5]
    arrayDirection[2,:] = np.cross(arrayDirection[0,:], arrayDirection[1,:])
    matrixItk = itk.Matrix[itk.D,3,3](itk.GetVnlMatrixFromArray(arrayDirection))
    img_result.SetDirection(matrixItk)
    return img_result


def read_3d_dicom(dicomFile, flip=False):
    """

    Read dicom file and return an float 3D image
    """
    files = []
    try:
        files.append(pydicom.read_file(dicomFile[0]))
    except pydicom.errors.InvalidDicomError:
        ds = pydicom.read_file(dicomFile[0], force=True)
        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
        files.append(ds)

    # skip files with no SliceLocation (eg scout views)
    slices = []
    if len(files) == 1:
        slices.append(files[0])
    else:
        logger.error('no file available')
        return

    dicomProperties = dicom_properties()
    dicomProperties.read_dicom_properties(slices[0])

    # create 3D array
    if len(slices[0].pixel_array.shape) == 2:
        dicomProperties.img_shape = [1] + dicomProperties.img_shape
    img3d = np.zeros(dicomProperties.img_shape)

    # fill 3D array with the images from the files
    if len(slices[0].pixel_array.shape) == 2:
        img3d[0, :, :] = slices[0].pixel_array
    else:
        img3d[:, :, :] = slices[0].pixel_array
    img3d = dicomProperties.rs*img3d+dicomProperties.ri

    img_result = itk.image_from_array(np.float32(img3d))
    img_result.SetSpacing(dicomProperties.spacing)
    img_result.SetOrigin(dicomProperties.origin)
    arrayDirection = np.zeros([3,3], np.float64)
    arrayDirection[0,0] = dicomProperties.io[0]
    arrayDirection[0,1] = dicomProperties.io[1]
    arrayDirection[0,2] = dicomProperties.io[2]
    arrayDirection[1,0] = dicomProperties.io[3]
    arrayDirection[1,1] = dicomProperties.io[4]
    arrayDirection[1,2] = dicomProperties.io[5]
    arrayDirection[2,:] = np.cross(arrayDirection[0,:], arrayDirection[1,:])
    if Tag(0x18, 0x88) in slices[0] and slices[0][0x18, 0x88].value <0:
        arrayDirection[2,2] = -1.0
    else:
        flip = False
        arrayDirection[2,2] = 1.0
    matrixItk = itk.Matrix[itk.D,3,3](itk.GetVnlMatrixFromArray(arrayDirection))
    img_result.SetDirection(matrixItk)
    if flip:
        flipFilter = itk.FlipImageFilter.New(Input=img_result)
        flipFilter.SetFlipAxes((False, False, True))
        flipFilter.SetFlipAboutOrigin(False)
        flipFilter.Update()
        img_result = flipFilter.GetOutput()
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
import wget
from .logging_conf import LoggedTestCase

def createImage():
    x = np.arange(-10, 10, 1)
    y = np.arange(-12, 15, 1)
    z = np.arange(-13, 10, 1)
    xx, yy, zz = np.meshgrid(x, y, z)
    return xx

class Test_Convert(LoggedTestCase):
    def test_convert_unsigned_char(self):
        image = itk.image_from_array(np.float32(createImage()))
        convertedImage = image_convert(image, "unsigned char")
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("da57bf05ec62b9b5ee2aaa71aacbf7dbca8acbf2278553edc499a3af8007dd44" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_convert_short(self):
        image = itk.image_from_array(np.float32(createImage()))
        convertedImage = image_convert(image, "short")
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("e71240bd149a509a3c28193817c82bb78d4cf5a6c8978b8266f820aa332cda0d" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_convert_unsigned_short(self):
        image = itk.image_from_array(np.float32(createImage()))
        convertedImage = image_convert(image, "unsigned short")
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("55913ce0ca7d1c6f8166f0fdf7499e986d5965249742098cc2aaefe35964a1cb" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_convert_float(self):
        image = itk.image_from_array(np.int16(createImage()))
        convertedImage = image_convert(image, "float")
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("c78c8b7450119dd554c338d6fd9f25648c5ee2863d8267cdd72dd20952673865" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_convert_rtDose(self):
        tmpdirpath = tempfile.mkdtemp()
        filenameRTDose = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtdose.dcm?inline=false", out=tmpdirpath, bar=None)
        convertedImage = read_3d_dicom([os.path.join(tmpdirpath, filenameRTDose)])
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("9c18c0344e309d096122c4b771fe3f1e66ddb778d818f98d18f29442fd287d47" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_convert_dicom(self):
        tmpdirpath = tempfile.mkdtemp()
        filename = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/tomoSPECT.dcm?inline=false", out=tmpdirpath, bar=None)
        convertedImage = read_3d_dicom([os.path.join(tmpdirpath, filename)])
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("3a64eee5f6439388fdbe6a5b7a682aca200fbc6826dcfffccc6f5fbae82b9600" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_convert_dicom_flip(self):
        tmpdirpath = tempfile.mkdtemp()
        filename = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/tomoSPECT.dcm?inline=false", out=tmpdirpath, bar=None)
        convertedImage = read_3d_dicom([os.path.join(tmpdirpath, filename)], flip=True)
        itk.imwrite(convertedImage, os.path.join(tmpdirpath, "testConvert.mha"))
        with open(os.path.join(tmpdirpath, "testConvert.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("87c7eee6e29172289407e2739c2618418a38718c09e94ebee9a390a73433d236" == new_hash)
        shutil.rmtree(tmpdirpath)

