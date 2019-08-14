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
import gatetools as gt
import numpy as np

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
    for f in files:
        if hasattr(f, 'SliceLocation'):
            slices.append(f)
        else:
            skipcount = skipcount + 1

    if skipcount >0:
        print("skipped, no SliceLocation: {}".format(skipcount))

    # ensure they are in the correct order
    slices = sorted(slices, key=lambda s: s.SliceLocation)

    # pixel aspects, assuming all slices are the same
    ps = slices[0].PixelSpacing
    ss = slices[0].SliceThickness
    spacing = [ps[0], ps[1], ss]
    ip = slices[0][0x20, 0x32].value #Image Position
    origin = [ip[0], ip[1], ip[2]]
    io = slices[0][0x20, 0x37].value #Image Orientation
    #orientation = [io[0], io[1], io[2], io[3], io[4], io[5]]
    ri = slices[0][0x28, 0x1052].value #Rescale Intercept
    rs = slices[0][0x28, 0x1053].value #Rescale Slope

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

    img_result = itk.GetImageFromArray(np.float32(img3d))
    img_result.SetSpacing(spacing)
    img_result.SetOrigin(origin)
    #img_result.SetDirection(orientation) ##TODO
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
