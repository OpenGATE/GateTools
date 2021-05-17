#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import click
import itk
import numpy as np
import os
import logging
logger=logging.getLogger(__name__)

def convertNewParameterToInt(newParameterString, size):
    if newParameterString is not None:
        parameterInt = np.array(newParameterString.split(','))
        parameterInt = [int(e) for e in parameterInt]
        if len(parameterInt) == 1:
            parameterInt = [parameterInt[0]]*size
        return parameterInt
    else:
        return [1]*size

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--input', type=str, required=True, help='Input filename')
@click.option('-o', '--output', type=str, required=True, help='Output image name')
@click.option('-m', '--morphotype', type=click.Choice(["0", "1", "2", "3"], case_sensitive=False), default="0", help='Morpholigical operation choice')
@click.option('-r', '--radius', type=str, help='Radius (default in pixel)')
@click.option('-mm', '--mm', is_flag=True, help='If set, Radius is set in mm')
@gt.add_options(gt.common_options)
def gt_morpho_math(input, output, morphotype, radius, mm, **kwargs):
    '''
    Compute morphological operation on binary image
    
    Radius is in pixel. If you set -r "2,3,4", the kernel will be 5,7,9 pixels along x,y and z axis.
    If the flag -mm is set, the radius is converted from mm to pixel according the input spacing.
    
    morphotype is the type of the morpholigical operation:\n
     - 0 (default): dilatation \n
     - 1: erosion \n
     - 2: closing \n
     - 3: opening
    '''

    # logger
    gt.logging_conf(**kwargs)

    #Check if input is available
    if not os.path.isfile(input):
        logger.error('no existing input: ' + input)
        return

    #Read input
    inputImage = itk.imread(input)

    #Convert Radius
    newRadius = convertNewParameterToInt(radius, inputImage.GetImageDimension())
    if mm:
        newRadius = gt.convertRadiusToPx(newRadius, inputImage.GetSpacing())

    #Morpho operation
    outputImage = gt.morpho_math(inputImage, int(morphotype), newRadius)
    if outputImage is not None:
      itk.imwrite(outputImage, output)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_morpho_math()
