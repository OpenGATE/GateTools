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
import csv
import os
import matplotlib
matplotlib.get_backend()
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import logging
logger=logging.getLogger(__name__)


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--input1','-i', help='Input ROI filename 1', required=True,
              type=click.Path(dir_okay=False))
@click.option('--input2','-j', help='Input ROI filename 2', required=True,
              type=click.Path(dir_okay=False))
@click.option('--percentile','-p', help='Percentile of Hausdorff distance (default = 1.0)', default=1.0)

@gt.add_options(gt.common_options)
def gt_hausdorff_main(input1, input2, percentile, **kwargs):
    '''
    Compute the hausdorff distance between 2 binary images. Percentile is between 0.0 and 1.0

    eg:

    gt_hausdorff -i mask1.mhd -j mask2.mhd -p 0.95

    '''

    # logger
    gt.logging_conf(**kwargs)

    mask1 = itk.imread(input1)
    mask2 = itk.imread(input2)

    hausdorffDistance = gt.computeHausdorff(mask1, mask2, percentile)
    print(hausdorffDistance)




# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_hausdorff_main()
