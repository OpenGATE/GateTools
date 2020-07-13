# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides basic affine transformation and resampling methods for images.
"""

import os
import itk
import numpy as np
import math
import logging
logger=logging.getLogger(__name__)

def applyTransformation(input=None, like=None, spacinglike=None, matrix=None, newsize=None, neworigin=None, newspacing=None, newdirection=None, force_resample=None, keep_original_canvas=None, adaptive=None, rotation=None, rotation_center=None, translation=None, pad=None, interpolation_mode=None, bspline_order=2):
    
    if like is not None and spacinglike is not None:
        logger.error("Choose between like and spacinglike options")
        sys.exit(1)
    if newspacing is not None and spacinglike is not None:
        logger.error("Choose between newspacing and spacinglike options")
        sys.exit(1)

    if force_resample is None:
        force_resample = False
    if keep_original_canvas is None:
        keep_original_canvas = False
    if force_resample and keep_original_canvas:
        logger.error("Choose between force_resample and keep_original_canvas options")
        sys.exit(1)
    if adaptive is None:
        adaptive = False
    if adaptive and not force_resample:
        logger.error("Be sure to activate force_resample flag with adaptive flag")
        sys.exit(1)

    if force_resample and adaptive and (newspacing is not None or spacinglike is not None) and newsize is not None:
        logger.error("With adaptive flag, choose between spacing and size options")
        sys.exit(1)
    imageDimension = input.GetImageDimension()
    if newsize is None:
        newsize = input.GetLargestPossibleRegion().GetSize()
    if len(newsize) != imageDimension:
        logger.error("Size of newsize is not correct (" + str(imageDimension) + "): " + str(newsize))
        sys.exit(1)
    if newspacing is None:
        newspacing = input.GetSpacing()
    if len(newspacing) != imageDimension:
        logger.error("Size of newspacing is not correct (" + str(imageDimension) + "): " + str(newspacing))
        sys.exit(1)
    if newdirection is None:
        newdirection = input.GetDirection()
    if newdirection.GetVnlMatrix().columns() != imageDimension or newdirection.GetVnlMatrix().rows() != imageDimension:
        logger.error("Size of newdirection is not correct (" + str(imageDimension) + "): " + str(newdirection))
        sys.exit(1)

    if like is not None:
        if like.GetImageDimension() != imageDimension:
            logger.error("Like image does not have the same dimension than input")
            sys.exit(1)
        newsize = like.GetLargestPossibleRegion().GetSize()
        neworigin = like.GetOrigin()
        newspacing = like.GetSpacing()
        newdirection = like.GetDirection()
    if spacinglike is not None:
        if spacinglike.GetImageDimension() != imageDimension:
            logger.error("Spacinglike image does not have the same dimension than input")
            sys.exit(1)
        newspacing = spacinglike.GetSpacing()

    if pad is None:
        pad = 0.0
    if interpolation_mode is None:
        interpolation_mode : "linear"

    if not force_resample and not keep_original_canvas:
        if neworigin is None:
            neworigin = input.GetOrigin()
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
    if rotation_center is None:
        rotation_center = np.zeros(imageDimension)
        for i in range(imageDimension):
            rotation_center[i] = centerImagePoint[i]
    if len(rotation_center) != imageDimension:
        logger.error("Size of rotation_center is not correct (" + str(imageDimension) + "): " + str(rotation_center))
        sys.exit(1)

    rotationMatrix = []
    translationMatrix = []
    if not matrix is None:
        if not rotation is None or not translation is None:
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
        if imageDimension == 2:
            if rotation is None:
                rotation = [0]
            if len(rotation) != 1:
                logger.error("Size of rotation is not correct (1): " + str(rotation))
                sys.exit(1)
        elif imageDimension == 3:
            if rotation is None:
                rotation = [0]*imageDimension
            if len(rotation) != imageDimension:
                logger.error("Size of rotation is not correct (3): " + str(rotation))
                sys.exit(1)
        if translation is None:
            translation = [0]*imageDimension
        if len(translation) != imageDimension:
            logger.error("Size of translation is not correct (" + str(imageDimension) + "): " + str(translation))
            sys.exit(1)
        if imageDimension == 2:
            euler = itk.Euler2DTransform[itk.D].New()
            euler.SetRotation(rotation[0]*math.pi/180.0)
            rotationMatrix = euler.GetMatrix()
        elif imageDimension == 3:
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

    cornersIndex = [itk.ContinuousIndex[itk.D, imageDimension]() for i in range(2**imageDimension)]
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
    resampleDirection = itk.matrix_from_array(np.eye(imageDimension))
    resampleFilter.SetOutputDirection(resampleDirection)
    resampleFilter.SetSize(sizeAfterRotation)
    resampleFilter.SetTransform(transform)
    if interpolation_mode == "NN":
        interpolator = itk.NearestNeighborInterpolateImageFunction[tempImageType, itk.D].New()
    elif interpolation_mode == "BSpline":
        interpolator = itk.BSplineInterpolateImageFunction[tempImageType, itk.D, itk.F].New()
        interpolator.SetSplineOrder(bspline_order)
    else:
        interpolator = itk.LinearInterpolateImageFunction[tempImageType, itk.D].New()
    resampleFilter.SetInterpolator(interpolator)
    resampleFilter.SetDefaultPixelValue(pad)
    resampleFilter.Update()

    postTranslateFilter = itk.ChangeInformationImageFilter.New(Input=resampleFilter.GetOutput())
    postTranslateFilter.SetOutputOrigin(originAfterRotation + centerImagePoint + translationMatrix)
    postTranslateFilter.ChangeOriginOn()
    postTranslateFilter.Update()

    if neworigin is None and not (itk.array_from_matrix(input.GetDirection()) == np.eye(imageDimension)).all():
        neworigin = postTranslateFilter.GetOutput().GetOrigin()
    elif neworigin is None:
        neworigin = inputOrigin
    if len(neworigin) != imageDimension:
        logger.error("Size of neworigin is not correct (" + str(imageDimension) + "): " + str(neworigin))
        sys.exit(1)

    if force_resample and adaptive:
        if (np.array(newspacing) == np.array(input.GetSpacing())).all():
            temp = np.array(sizeAfterRotation)*itk.array_from_vnl_vector(newspacing.GetVnlVector())/np.array(newsize)
            newspacing = itk.Vector[itk.D, imageDimension]()
            for i in range(imageDimension):
                newspacing[i] = temp[i]
        else:
            newsize = itk.Size[imageDimension]()
            for i in range(imageDimension):
                newsize[i] = sizeAfterRotation[i]

    identityTransform = itk.AffineTransform[itk.D, imageDimension].New()
    resampleFilterCanvas = itk.ResampleImageFilter.New(Input=postTranslateFilter.GetOutput())
    resampleFilterCanvas.SetOutputSpacing(newspacing)
    resampleFilterCanvas.SetOutputOrigin(neworigin)
    resampleFilterCanvas.SetOutputDirection(resampleDirection)
    resampleFilterCanvas.SetSize(newsize)
    resampleFilterCanvas.SetTransform(identityTransform)
    if interpolation_mode == "NN":
        interpolator = itk.NearestNeighborInterpolateImageFunction[tempImageType, itk.D].New()
    else:
        interpolator = itk.LinearInterpolateImageFunction[tempImageType, itk.D].New()
    resampleFilterCanvas.SetInterpolator(interpolator)
    resampleFilterCanvas.SetDefaultPixelValue(pad)
    resampleFilterCanvas.Update()
        
    castImageFilter2 = itk.CastImageFilter[tempImageType, type(input)].New()
    castImageFilter2.SetInput(resampleFilterCanvas.GetOutput())
    castImageFilter2.Update()
    
    return castImageFilter2.GetOutput()


    
    

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

class Test_Affine_Transform(LoggedTestCase):
    def test_change_info(self):
        logger.info('Test_Affine_Transform test_change_info')
        image = createImageExample()
        transformImage = applyTransformation(input=image, neworigin=[-3, 4, -4.6], newspacing=[3, 3, 3])
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testAffineTransform.mha"))
        with open(os.path.join(tmpdirpath, "testAffineTransform.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("43cfa7c5c4dadf403fd3555663bf4b2341b69b6797bbae65824abd160a5ef36b" == new_hash)
        shutil.rmtree(tmpdirpath)

    def test_force_resample(self):
        logger.info('Test_Affine_Transform test_force_resample')
        image = createImageExample()
        transformImage = applyTransformation(input=image, force_resample=True, rotation=[43, 12, 278], rotation_center=np.array([12, 56, 23]), translation=[100, -5, 12], pad=-15, interpolation_mode='linear')
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testAffineTransform.mha"))
        with open(os.path.join(tmpdirpath, "testAffineTransform.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("98165d7ed3167b393fb65301bfa5a71670142be0421bd609454186c8c4b07333" == new_hash)
        shutil.rmtree(tmpdirpath)

    def test_keep_original_canvas(self):
        logger.info('Test_Affine_Transform test_keep_original_canvas')
        image = createImageExample()
        transformImage = applyTransformation(input=image, keep_original_canvas=True, rotation=[43, 12, 278], rotation_center=np.array([12, 56, 23]), translation=[100, -5, 12], pad=-15, interpolation_mode='NN')
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testAffineTransform.mha"))
        with open(os.path.join(tmpdirpath, "testAffineTransform.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("2ee82f72b33f618b23b2dff553385180565318a85b5819bdc48256a3656e64fb" == new_hash)
        shutil.rmtree(tmpdirpath)

    def test_adaptive(self):
        logger.info('Test_Affine_Transform test_adaptive')
        image = createImageExample()
        newspacing = itk.Vector[itk.D, 3]()
        newspacing.Fill(3)
        transformImage = applyTransformation(input=image, force_resample=True, adaptive=True, newspacing=newspacing, pad=-15, interpolation_mode='linear')
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(transformImage, os.path.join(tmpdirpath, "testAffineTransform.mha"))
        with open(os.path.join(tmpdirpath, "testAffineTransform.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("1f3446724ce83d9dd5b150e506181e3c92f9b5892b0781383207b1a616da9a17" == new_hash)
        shutil.rmtree(tmpdirpath)
