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
@click.option('-s', '--sigma', help='Set the sigma of the filter in pixel', type=str)
@click.option('-m', '--sigma_mm', help='Set the sigma of the filter in mm', type=str)
@click.option('-f', '--float', help='Keep the output to float pixel type', is_flag=True)

@gt.add_options(gt.common_options)
def gt_image_gauss_main(input, output, sigma, sigma_mm, float, **kwargs):
    """
    Apply gaussian filter to the image

    eg:

    gt_image_gauss -i input.mhd -o output.mhd --sigma "2.0"

    gt_image_gauss -i input.mhd -o output.mhd --sigma "2.0,3.0,4.0"

    The script uses RecursiveGaussianImageFilter from R. Deriche, "Recursively Implementing The Gaussian and Its Derivatives", INRIA, 1993
    The output is automatically converted to input type. So if the input is int pixel type, the gaussian filtered output image is rounded. Use float flag to avoid this rounding.

    """

    # logger
    gt.logging_conf(**kwargs)
    
    inputImage = itk.imread(input)
    imageDimension = inputImage.GetImageDimension()

    if sigma is not None:
        sigma = convertNewParameterToFloat(sigma, imageDimension)
    if sigma_mm is not None:
        sigma_mm = convertNewParameterToFloat(sigma_mm, imageDimension)

    outputImage = gt.gaussFilter(inputImage, sigma, sigma_mm, float)

    itk.imwrite(outputImage, output)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_gauss_main()
