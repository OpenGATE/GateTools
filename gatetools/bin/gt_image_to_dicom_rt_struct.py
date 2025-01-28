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
import os
import rt_utils
import logging
logger=logging.getLogger(__name__)


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--mask','-m', help='Input mask filename', required=True,
              type=click.Path(dir_okay=False))
@click.option('--rtstruct','-r', help='Input RTstruct to have a model', required=True,
              type=click.Path(dir_okay=False))
@click.option('--output','-o', help='Output dicom RTStruct filename',
              type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))
@click.option('--name','-n', help='Name of the ROI', default='ROI')
@click.argument('dicom', type=str, required=True, nargs=-1)

@gt.add_options(gt.common_options)
def gt_image_to_dicom_rt_struct_main(mask, rtstruct, output, name, dicom, **kwargs):
    '''
    Tool to convert a binary mask image (mhd, ...) to RTStruct. It uses the python tool rt_utils
    The mask and the image from dicom must have the same spacing/size/origin. The resample is done automatically if needed

    eg:

    gt_image_to_dicom_rt_struct -m path/to/binary/mask.mhd -r path/to/model/rtstruct.dcm -o path/to/output path/to/ct/dicom/*.dcm

    '''

    # logger
    gt.logging_conf(**kwargs)

    maskImage = itk.imread(mask)
    rtstruct = gt.image_to_dicom_rt_struct(dicom, maskImage, name, rtstruct)
    rtstruct.save(output)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_to_dicom_rt_struct_main()
