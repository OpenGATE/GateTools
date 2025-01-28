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
        parameterFloat = parameterFloat.astype(np.float)
        if len(parameterFloat) == 1:
            parameterFloat = [parameterFloat[0].astype(np.float)]*size
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
@click.option('--newsize', help='Set the output size in pixel', type=str)
@click.option('--newsize_mm', help='Set the output size in mm', type=str)
@click.option('--pad', '-p', help='Set the padding pixel value', default=0.0)

@gt.add_options(gt.common_options)
def gt_image_resize_main(input, output, newsize, newsize_mm, pad, **kwargs):
    '''
    Convenient method to resize an image (pad or crop) around the center.
    If the new size is larger than before, the image is padded at the borders.
    if not, the borders of the image are cropped.
    The padding and the cropping are done to ensure the image is still centered dispatching the same number of voxels for the low border than the higher border. If there is an odd number of voxels to dispatch, the low border is pad/crop with one more voxel than the higer border.

    eg:
    gt_image_resize -i input.mhd -o output.mhd --newsize "2.0"
    gt_image_resize -i input.mhd -o output.mhd --newsize "2.0,3.0,4.0"

    For more complex tool, use gt_affine_transform or gt_image_crop

    '''

    # logger
    gt.logging_conf(**kwargs)

    inputImage = itk.imread(input)
    imageDimension = inputImage.GetImageDimension()

    size = convertNewParameterToFloat(newsize, imageDimension)
    itkSize = None
    if size is not None:
        itkSize = itk.Size[imageDimension]()
        for i in range(imageDimension):
            itkSize[i] = int(size[i])
    size_mm = convertNewParameterToFloat(newsize_mm, imageDimension)
    itkSize_mm = None
    if size_mm is not None:
        itkSize_mm = itk.Point[itk.F, imageDimension]()
        for i in range(imageDimension):
            itkSize_mm[i] = size_mm[i]

    outputImage = gt.imageResize(inputImage, newsize = itkSize, newsize_mm = itkSize_mm, pad = pad)

    itk.imwrite(outputImage, output)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_resize_main()
