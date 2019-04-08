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
import gatetools as gt

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
    #If None it could be a type convervion without pixel conversion
    if pixeltype is not None:
        InputType = type(inputImage)
        OutputType = itk.Image[itk.ctype(pixeltype), inputImage.GetImageDimension()]
        castFilter = itk.CastImageFilter[InputType, OutputType].New()
        castFilter.SetInput(inputImage)
        return castFilter

    return inputImage