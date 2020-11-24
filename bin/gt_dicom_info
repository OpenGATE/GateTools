#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import pydicom
import click
import logging
logger=logging.getLogger(__name__)

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--input', '-i', help='Input dicom filename', required=True,
                type=click.Path(dir_okay=False))

@gt.add_options(gt.common_options)
def gt_dicom_info_main(input, **kwargs):
    '''
    Print the tag vlaues of the dicom input
    '''

    # logger
    gt.logging_conf(**kwargs)

    print(gt.printTags(input))


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_dicom_info_main()
