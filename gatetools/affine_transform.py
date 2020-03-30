# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides basic affine transformation and resampling of an image for ITK images.
"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import os
import itk
import numpy as np
from numpy import linalg as LA
import math
import logging
logger=logging.getLogger(__name__)

def applyTransformation(input, like, spacinglike, matrix, newsize=[], neworigin=[], newspacing=[], newdirection=[], force_resample=False, keep_original_canvas=False, rotation=[], rotation_center=[], translation=[], pad=0.0, interpolation_mode='linear'):
    
    if like is not None and spacinglike is not None:
        logger.error("Choose between like and spacinglike options")
        sys.exit(1)
    if force_resample and keep_original_canvas:
        logger.error("Choose between force_resample and keep_original_canvas options")
        sys.exit(1)
    imageDimension = input.GetImageDimension()
    if newsize == []:
        newsize = input.GetLargestPossibleRegion().GetSize()
    if len(newsize) != imageDimension:
        logger.error("Size of newsize is not correct (" + str(imageDimension) + "): " + str(newsize))
        sys.exit(1)
    if neworigin == []:
        neworigin = input.GetOrigin()
    if len(neworigin) != imageDimension:
        logger.error("Size of neworigin is not correct (" + str(imageDimension) + "): " + str(neworigin))
        sys.exit(1)
    if newspacing == []:
        newspacing = input.GetSpacing()
    if len(newspacing) != imageDimension:
        logger.error("Size of newspacing is not correct (" + str(imageDimension) + "): " + str(newspacing))
        sys.exit(1)
    if newdirection == []:
        newdirection = input.GetDirection()
    if newdirection.GetVnlMatrix().columns() != imageDimension or newdirection.GetVnlMatrix().rows() != imageDimension:
        logger.error("Size of newdirection is not correct (" + str(imageDimension) + "): " + str(newdirection))
        sys.exit(1)

    if like is not None:
        if like.GetImageDimension() != imageDimension:
            logger.error("Like image do not have the same dimension than input")
            sys.exit(1)
        newsize = like.GetLargestPossibleRegion().GetSize()
        neworigin = like.GetOrigin()
        newspacing = like.GetSpacing()
        newdirection = like.GetDirection()
    if spacinglike is not None:
        if spacinglike.GetImageDimension() != imageDimension:
            logger.error("Spacinglike image do not have the same dimension than input")
            sys.exit(1)
        newspacing = spacinglike.GetSpacing()
    
    if not force_resample and not keep_original_canvas:
        changeInfoFilter = itk.ChangeInformationImageFilter.New(Input=input)
        changeInfoFilter.SetOutputSpacing(newspacing)
        changeInfoFilter.SetOutputOrigin(neworigin)
        changeInfoFilter.SetOutputDirection(newdirection)
        changeInfoFilter.ChangeSpacingOn()
        changeInfoFilter.ChangeOriginOn()
        changeInfoFilter.ChangeDirectionOn()
        changeInfoFilter.Update()
        return changeInfoFilter.GetOutput()

    centerImageIndex = itk.ContinuousIndex[itk.D, imageDimension]()
    for i in range(imageDimension):
        centerImageIndex[i] = (input.GetLargestPossibleRegion().GetSize()[i]-1)/2.0
    centerImagePoint = input.TransformContinuousIndexToPhysicalPoint(centerImageIndex)
    centerImageArray = [0]*imageDimension
    for i in range(imageDimension):
        centerImageArray[i] = centerImagePoint[i]
    if rotation_center == []:
        rotation_center = np.zeros(imageDimension)
        for i in range(imageDimension):
            rotation_center[i] = centerImagePoint[i]
    if len(rotation_center) != imageDimension:
        logger.error("Size of rotation_center is not correct (" + str(imageDimension) + "): " + str(rotation_center))
        sys.exit(1)

    rotationMatrix = []
    translationMatrix = []
    if not matrix is None:
        if rotation != [] or translation != []:
            logger.error("Choose between matrix or rotation/translation, not both")
            sys.exit(1)
        if matrix.GetVnlMatrix().columns() != imageDimension+1 or matrix.GetVnlMatrix().rows() != imageDimension+1:
            logger.error("Size of matrix transformation is not correct (" + str(imageDimension+1) + "): " + str(matrix))
            sys.exit(1)
        if matrix.GetVnlMatrix().columns() == 3 or matrix.GetVnlMatrix().columns() == 4:
            rotationMatrix = itk.matrix_from_array(itk.array_from_matrix(matrix)[:imageDimension, :imageDimension])
        else:
            logger.error("We can transform only 2D and 3D images")
            sys.exit(1)
    else:
        if rotation == []:
            rotation = [0]*imageDimension
        if len(rotation) != imageDimension:
            logger.error("Size of rotation is not correct (" + str(imageDimension) + "): " + str(rotation))
            sys.exit(1)
        if translation == []:
            translation = [0]*imageDimension
        if len(translation) != imageDimension:
            logger.error("Size of translation is not correct (" + str(imageDimension) + "): " + str(translation))
            sys.exit(1)
        if len(rotation) == 2:
            euler = itk.Euler2DTransform[itk.D].New()
            euler.SetRotation(rotation[0]*math.pi/180.0, rotation[1]*math.pi/180.0)
            rotationMatrix = euler.GetMatrix()
        elif len(rotation) == 3:
            euler = itk.Euler3DTransform[itk.D].New()
            euler.SetRotation(rotation[0]*math.pi/180.0, rotation[1]*math.pi/180.0, rotation[2]*math.pi/180.0)
            rotationMatrix = euler.GetMatrix()
        else:
            logger.error("We can transform only 2D and 3D images")
            sys.exit(1)

    transform = itk.AffineTransform[itk.D, imageDimension].New()
    transform.SetCenter([0]*imageDimension)
    transform.SetTranslation([0]*imageDimension)
    transform.SetMatrix(rotationMatrix)
    inverseTransform = itk.AffineTransform[itk.D, imageDimension].New()
    transform.GetInverse(inverseTransform)
    if not matrix is None:
        translation = itk.array_from_matrix(matrix)[:imageDimension, imageDimension] - rotation_center + rotationMatrix*rotation_center
    translationMatrix = inverseTransform.GetMatrix()*(centerImageArray - rotation_center) - (centerImageArray - rotation_center) - inverseTransform.GetMatrix()*translation

    inputOrigin = itk.Point[itk.D, imageDimension]()
    for i in range(imageDimension):
        inputOrigin[i] = input.GetOrigin()[i]
    preTranslateFilter = itk.ChangeInformationImageFilter.New(Input=input)
    preTranslateFilter.CenterImageOn()
    preTranslateFilter.Update()

    cornersIndex = [itk.ContinuousIndex[itk.D, imageDimension]() for i in range(imageDimension**2-1)]
    if imageDimension == 2 or imageDimension == 3:
        cornersIndex[0][0] = -0.5
        cornersIndex[0][1] = -0.5
        if imageDimension == 3:
           cornersIndex[0][2] = -0.5
        cornersIndex[1][0] = input.GetLargestPossibleRegion().GetSize()[0]-0.5
        cornersIndex[1][1] = cornersIndex[0][1]
        if imageDimension == 3:
            cornersIndex[1][2] = cornersIndex[0][2]
        cornersIndex[2][0] = cornersIndex[0][0]
        cornersIndex[2][1] = input.GetLargestPossibleRegion().GetSize()[1]-0.5
        if imageDimension == 3:
            cornersIndex[2][2] = cornersIndex[0][2]
        cornersIndex[3][0] = cornersIndex[1][0]
        cornersIndex[3][1] = cornersIndex[2][1]
        if imageDimension == 3:
            cornersIndex[3][2] = cornersIndex[0][2]
        if imageDimension == 3:
            cornersIndex[4][0] = cornersIndex[0][0]
            cornersIndex[4][1] = cornersIndex[0][1]
            cornersIndex[4][2] = input.GetLargestPossibleRegion().GetSize()[2]-0.5
            cornersIndex[5][0] = cornersIndex[1][0]
            cornersIndex[5][1] = cornersIndex[0][1]
            cornersIndex[5][2] = cornersIndex[4][2]
            cornersIndex[6][0] = cornersIndex[0][0]
            cornersIndex[6][1] = cornersIndex[2][1]
            cornersIndex[6][2] = cornersIndex[4][2]
            cornersIndex[7][0] = cornersIndex[1][0]
            cornersIndex[7][1] = cornersIndex[2][1]
            cornersIndex[7][2] = cornersIndex[4][2]
        outputCorners = np.zeros((2**imageDimension, imageDimension))
        for i in range(2**imageDimension):
            outputCorners[i, :] = inverseTransform.GetMatrix()*preTranslateFilter.GetOutput().TransformContinuousIndexToPhysicalPoint(cornersIndex[i])
        minOutputCorner = np.zeros(imageDimension)
        maxOutputCorner = np.zeros(imageDimension)

        for i in range(imageDimension):
            minOutputCorner[i] = min(outputCorners[:, i])
            maxOutputCorner[i] = max(outputCorners[:, i])
        temp = minOutputCorner + 0.5*itk.array_from_vnl_vector(newspacing.GetVnlVector())
        originAfterRotation = itk.Point[itk.D, imageDimension]()
        for i in range(imageDimension):
            originAfterRotation[i] = temp[i]
        temp = (maxOutputCorner - minOutputCorner)/itk.array_from_vnl_vector(newspacing.GetVnlVector())
        sizeAfterRotation = itk.Size[imageDimension]()
        for i in range(imageDimension):
            sizeAfterRotation[i] = int(math.ceil(temp[i]))
    else:
        logger.error("We can transform only 2D and 3D images")
        sys.exit(1)

    tempImageType = itk.Image[itk.F, imageDimension]
    castImageFilter = itk.CastImageFilter[type(input), tempImageType].New()
    castImageFilter.SetInput(preTranslateFilter.GetOutput())
    castImageFilter.Update()
    
    resampleFilter = itk.ResampleImageFilter.New(Input=castImageFilter.GetOutput())
    resampleFilter.SetOutputSpacing(newspacing)
    resampleFilter.SetOutputOrigin(originAfterRotation)
    resampleFilter.SetOutputDirection(newdirection)
    resampleFilter.SetSize(sizeAfterRotation)
    resampleFilter.SetTransform(transform)
    if interpolation_mode == "NN":
        interpolator = itk.NearestNeighborInterpolateImageFunction[tempImageType, itk.D].New()
    else:
        interpolator = itk.LinearInterpolateImageFunction[tempImageType, itk.D].New()
    resampleFilter.SetInterpolator(interpolator)
    resampleFilter.SetDefaultPixelValue(pad)
    resampleFilter.Update()

    postTranslateFilter = itk.ChangeInformationImageFilter.New(Input=resampleFilter.GetOutput())
    postTranslateFilter.SetOutputOrigin(originAfterRotation + centerImagePoint + translationMatrix)
    postTranslateFilter.ChangeOriginOn()
    postTranslateFilter.Update()

    if keep_original_canvas:
        identityTransform = itk.AffineTransform[itk.D, imageDimension].New()
        resampleFilterOriginalCanvas = itk.ResampleImageFilter.New(Input=postTranslateFilter.GetOutput())
        resampleFilterOriginalCanvas.SetOutputSpacing(newspacing)
        resampleFilterOriginalCanvas.SetOutputOrigin(neworigin)
        resampleFilterOriginalCanvas.SetOutputDirection(newdirection)
        resampleFilterOriginalCanvas.SetSize(newsize)
        resampleFilterOriginalCanvas.SetTransform(identityTransform)
        if interpolation_mode == "NN":
            interpolator = itk.NearestNeighborInterpolateImageFunction[tempImageType, itk.D].New()
        else:
            interpolator = itk.LinearInterpolateImageFunction[tempImageType, itk.D].New()
        resampleFilterOriginalCanvas.SetInterpolator(interpolator)
        resampleFilterOriginalCanvas.SetDefaultPixelValue(pad)
        resampleFilterOriginalCanvas.Update()
        
    castImageFilter2 = itk.CastImageFilter[tempImageType, type(input)].New()
    if keep_original_canvas:
        castImageFilter2.SetInput(resampleFilterOriginalCanvas.GetOutput())
    else:
        castImageFilter2.SetInput(postTranslateFilter.GetOutput())
    castImageFilter2.Update()
    
    return castImageFilter2.GetOutput()


    
    

#####################################################################################
import unittest
import sys
from datetime import datetime
from .logging_conf import LoggedTestCase

class Test_Apply_Transform(LoggedTestCase):
    def test_apply_transform(self):
        logger.info('Test_Apply_Transform test_apply_transform')