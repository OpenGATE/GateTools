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
import csv
import logging
logger=logging.getLogger(__name__)

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)




@click.option('--input','-i', help='Input filename', required=True,
              type=click.Path(dir_okay=False))
@click.option('--mask','-m', help='Mask filename (.mhd/.mha file)',
              type=click.Path(dir_okay=False))
@click.option('--resample', '-r', help='Resample the mask if its size is not the same than the input', is_flag=True)
@click.option('--histogram','-h', help='Histogram output csv file path (the extension is added)',
              type=click.Path(dir_okay=False))
@click.option('--bin', '-b', help='Number of bins for the histogram', default=1000)
@gt.add_options(gt.common_options)
def gt_image_statistics_main(input, mask, resample, histogram, bin, **kwargs):
    '''
    Basic image statistics of the input image
    
    The statistics can be computed in a region of interest using the mask option to load a binary mask representing the ROI.
    
    If the mask do not have the same size, spacing, origin, direction than the input, the algorithm fails. In such a case you can add the resample flag to force a resample of the mask.

    If histogram option is set with a path, compute and save the histogram of the image (or inside the ROI) to a csv file with 2 columns: bin_edges of size bin+1 and values of size bin
    '''

    # logger
    gt.logging_conf(**kwargs)
    
    inputImage = itk.imread(input)
    maskImage = None
    if not mask is None:
        maskImage = itk.imread(mask)

    outputStats = gt.imageStatistics(inputImage, maskImage, resample, bin)
    
    print("Number of voxels: " + str(outputStats["nbPixel"]))
    print("Mean: " + str(outputStats["mean"]))
    print("Median: " + str(outputStats["median"]))
    print("Sum: " + str(outputStats["sum"]))
    print("Minimum: " + str(outputStats["minimum"]))
    print("Maximum: " + str(outputStats["maximum"]))
    print("Variance: " + str(outputStats["variance"]))
    print("Sigma: " + str(outputStats["sigma"]))
    if not histogram is None:
            with open(histogram +'.csv', 'w', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow(['bin edge'] + ['number of pixel'])
                for x, y in zip(outputStats["hist"][1][:-1], outputStats["hist"][0]):
                    spamwriter.writerow([x, y])
                spamwriter.writerow([outputStats["hist"][1][-1]])
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_statistics_main()
