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
import logging
logger=logging.getLogger(__name__)

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--input', '-i', help='Input image filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--dicom', '-d', help='Input Dicom file example',
                type=click.Path(dir_okay=False))
@click.option('--output', '-o', default='output.dcm', help='Output dicom filename')
@click.option('--newseriesuid', '-e', is_flag=True, help='New Series UID if set')
@click.option('--newstudyuid', '-u', is_flag=True, help='New Study UID if set')
@click.option('--tag', '-t', type=(str, str), multiple=True, help='Change Tag')

@gt.add_options(gt.common_options)
def gt_write_dicom_main(input, dicom, output, newseriesuid, newstudyuid, tag, **kwargs):
    '''
    Convert the input image (usually mhd, nii, ...) to dicom format.\n
    If dicom is set, take the tags of dicom as model for the output.\n
    Write the dicom volume as output\n
    By default, if dicom is set, the series UID and the study UID are the same than the dicom (and the Reference Frame UID too). If newstudyuid is set, the study UID is generated, the Frame of Reference UID and the series UID are different than the dicom UIDs. If newseriesuid is set, just the series UID is different.\n
    If you want to change or add a tag, use the option tag:\n
    Example for the following tags:\n
      (0008, 0060) Modality      CS: 'CT'\n
      (0018, 9309) Table Speed   FD: 46.0\n
      (0008, 0008) Image Type    CS: ['ORIGINAL', 'PRIMARY', 'AXIAL', 'CT_SOM5 SPI']\n
    You can use the command line:\n
      gt_write_dicom -i input.mhd -d dicom.dcm -o output.dcm --tag 0x00080060 "CT" --tag 0x00189309 46.0 --tag 0x00080008 "NM\\test"
    '''

    # logger
    gt.logging_conf(**kwargs)

    inputImage = itk.imread(input)
    gt.writeDicom(inputImage, dicom, output, newseriesuid, newstudyuid, tag)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_write_dicom_main()
