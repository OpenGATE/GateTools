#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import sys
import gatetools as gt
import click
import itk
import numpy as np
import logging
logger=logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('input_filename')
@click.option('--output', '-o', help='Output filename', required=True)
@click.option('--bg', help='Value of the backgroup to autocrop', default=None)
@click.option('--bb', default=None,
              help="Bounding Box with 6 ints (voxel), separated with comma 'x1,x2,y1,y2,z1,z2'")
@gt.add_options(gt.common_options)
def gt_image_crop(input_filename, output, bg, bb, **kwargs):
    '''
    \b
    Crop an image.

    If --bg : auto crop according to the given background value
    If --bb : manual crop in voxel.

    \b
    <INPUT_FILENAME> : input image
    '''

    # logger
    gt.logging_conf(**kwargs)

    # check exclusive options
    if bg == None and bb == None:
        bg = 0
    if bg != None and bb != None:
        logger.error('Use --bg or --bb not both')
        exit(0)

    # read img
    try:
        img = itk.imread(input_filename)
    except:
        logger.error(f'cannot read {input_filename}')
        exit(0)
    dims = np.array(img.GetLargestPossibleRegion().GetSize())
    
    logger.info(f'Input image: {input_filename} {dims}')

    # autocrop
    if bg != None:
        logger.info(f'Auto crop with background {bg}')
        o = gt.image_auto_crop(img, bg)

    # manual crop
    if bb != None:
        bb = [float(x) for x in bb.split(',')]
        bb = gt.bounding_box(xyz=bb)
        logger.info(f'Crop with bounding box {bb}')
        o = gt.image_crop_with_bb(img, bb)

    # final write
    dims = np.array(o.GetLargestPossibleRegion().GetSize())
    
    logger.info(f'Output image: {output} {dims}')
    itk.imwrite(o, output)

# --------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_crop()
