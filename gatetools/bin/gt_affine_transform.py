#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import itk
import click
import sys
import numpy as np
import os
import logging
logger=logging.getLogger(__name__)

def convertNewParameterToFloat(newParameterString, size):
    if newParameterString is not None:
        parameterFloat = np.array(newParameterString.split(','))
        parameterFloat = parameterFloat.astype(float)
        if len(parameterFloat) == 1:
            parameterFloat = [parameterFloat[0].astype(float)]*size
        return parameterFloat
    else:
        return None
    

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)




@click.option('--input','-i', help='Input filename', required=True,
              type=click.Path(dir_okay=False))
@click.option('--output','-o', help='Output filename', required=True,
              type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))
@click.option('--newsize', help='Set the output size', type=str)
@click.option('--neworigin', help='Set the output origin', type=str)
@click.option('--newspacing', help='Set the output spacing', type=str)
@click.option('--newdirection', help='Set the output direction', type=str)


@click.option('--like', '-l', help='Output will have the same size, origin, spacing and direction than this like image', type=click.Path(dir_okay=False))
@click.option('--spacinglike', '-sl', help='Output will have the same spacing than this spacinglike image', type=click.Path(dir_okay=False))


@click.option('--force_resample', '-fr', help='Force the output to be resampled instead of only changing the metadata', is_flag=True)
@click.option('--keep_original_canvas', '-koc', help='Perform the transformation on the image but the output will keep the same physical region than the input', is_flag=True)
@click.option('--adaptive', '-a', help='If newspacing is set, compute the corresponding new size and vice versa', is_flag=True)


@click.option('--matrix', '-m', help='Matrix for affine transformation', type=click.Path(dir_okay=False))
@click.option('--rotation', '-r', help='Rotation for affine transformation', type=str)
@click.option('--center', '-c', help='Rotation center or affine transformation', type=str)
@click.option('--translation', '-t', help='Translation for affine transformation', type=str)

@click.option('--pad', '-p', help='Set the padding pixel value', default=0.0)

@click.option('--interpolation_mode', '-im', help='Interpolation mode: NN for nearest neighbor, linear for linear interpolation and BSpline for BSpline interpolation', default='linear', type=click.Choice(['NN', 'linear', 'BSpline']))
@click.option('--bspline_order', '-bo', help='For BSpline interpolator, set the interpolation bspline order', default='2', type=click.Choice(['0', '1', '2', '3', '4', '5']))

@gt.add_options(gt.common_options)
def gt_affine_transform_main(input, output, newsize, neworigin, newspacing, newdirection, like, spacinglike, force_resample, keep_original_canvas, adaptive, matrix, rotation, center, translation, pad, interpolation_mode, bspline_order, **kwargs):
    '''
    Basic affine transfomation and resampling of images
    
    eg:
    gt_affine_transform -i input.mhd -o output.mhd --newsize "2.0"
    gt_affine_transform -i input.mhd -o output.mhd --newsize "2.0,3.0,4.0"
    
    There are 3 modes to apply the transform:
      - by default, the transformation is applied to the mhd metadata. In such a case, no resampling is performed. The raw file contains the same data, only the mhd file is modified.
      - with force_resample flag, the output image will be resampled like the input image.
      - with keep_original_canvas, the transformation will be applied to the input image but output will keep the same support (physical size) than the input. Warning, some pixels may fall outside the image support after the transformation and will be ignored.
    
    --matrix is a file that contains the transformation matrix (rotation + translation). Example for a 3D image:
    1 0 0 0
    0 1 0 0
    0 0 1 0
    0 0 0 1

    --rotation is in degree. By default, the rotation is around the center of the image

    It could be more convenient to use images with an identity matrix as image direction and keep the image with the correct space coordinate. In such a case you can do:
        gt_affine_transform -i input.mhd -o output.mhd -fr

    --adaptive flag (in combination with force_resample flag) allows the users to set the newspacing (or spacinglike) and the newsize is automatically computed and vice versa.

    '''

    # logger
    gt.logging_conf(**kwargs)
    
    inputImage = itk.imread(input)
    imageDimension = inputImage.GetImageDimension()
    likeImage = None
    spacingLikeImage = None
    if like is not None:
        likeImage = itk.imread(like)
    if spacinglike is not None:
        spacingLikeImage = itk.imread(spacinglike)

    size = convertNewParameterToFloat(newsize, imageDimension)
    itkSize = None
    if size is not None:
        itkSize = itk.Size[imageDimension]()
        for i in range(imageDimension):
            itkSize[i] = int(size[i])
    origin = convertNewParameterToFloat(neworigin, imageDimension)
    itkOrigin = None
    if origin is not None:
        itkOrigin = itk.Vector[itk.D, imageDimension]()
        for i in range(imageDimension):
            itkOrigin[i] = origin[i]
    spacing = convertNewParameterToFloat(newspacing, imageDimension)
    itkSpacing = None
    if spacing is not None:
        itkSpacing = itk.Vector[itk.D, imageDimension]()
        for i in range(imageDimension):
            itkSpacing[i] = spacing[i]
    direction = convertNewParameterToFloat(newdirection, imageDimension**2)
    itkDirection = None
    if direction is not None:
        itkDirection = itk.matrix_from_array(np.array(direction).newshape((imageDimension, imageDimension)))
    rotationParameter = convertNewParameterToFloat(rotation, imageDimension)
    rotationCenterParameter = convertNewParameterToFloat(center, imageDimension)
    translationParameter = convertNewParameterToFloat(translation, imageDimension)
    matrixParameter = None
    if not matrix is None:
        if not os.path.isfile(matrix):
            logger.error("Cannot read the matrix file: " + matrix)
            sys.exit(1)
        try:
            with open(matrix, 'r') as f:
                readMatrix = [[float(num) for num in line.split(' ')] for line in f if line.strip() != "" ]
        except Exception as e:
            logger.error("Cannot read the matrix file: ")
            logger.error(e)
            sys.exit(1)
        matrixParameter = itk.matrix_from_array(np.array(readMatrix))

    outputImage = gt.applyTransformation(inputImage, likeImage, spacingLikeImage, matrixParameter, newsize = itkSize, neworigin = itkOrigin, newspacing = itkSpacing, newdirection = itkDirection, force_resample = force_resample, keep_original_canvas = keep_original_canvas, adaptive = adaptive, rotation = rotationParameter, rotation_center = rotationCenterParameter, translation = translationParameter, pad = pad, interpolation_mode = interpolation_mode, bspline_order=int(bspline_order))
    
    itk.imwrite(outputImage, output)
    

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_affine_transform_main()
