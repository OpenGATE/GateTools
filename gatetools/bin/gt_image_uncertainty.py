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
import os
import re
import numpy as np
import logging
logger=logging.getLogger(__name__)

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('filenames', nargs=-1)

@click.option('--nevents','-n', help='Total numbers of events', default=0.0)

@click.option('--counts/--not-counts', '-c', default=False, help='Compute uncertainty for counts image (Poisson process)')

@click.option('--output','-o', help='Output filename', required=True)

@click.option('--by_slice/--not-by_slice', '-s', default=False, help='Display mean uncertainty by slice (only with --counts)')

@click.option('--threshold', '-t', default=0.0, help='Threshold in %, do not consider pixels with value lower \ than this % of the max value by slice (only with --counts)')

@click.option('--efficiency','-e', help='Compute efficiency (1/t*sigma). The time is read in the given stat file. Only slice by slice for the moment', default=False)

@click.option('--sigma', default=False, is_flag=True, help='By default, uncertainty is normalized, unc = sigma/x. By using this option, the output is *not* normalized, sigma=sqrt(var) is computed.')

@gt.add_options(gt.common_options)
def gt_image_uncertainty(filenames, nevents, output, counts, by_slice, threshold, efficiency, sigma, verbose, **kwargs):
    '''
    Compute relative statistical uncertainty image for a list of
    images. Images are summed before computing the the uncertainty.

    FILENAMES: list of image filenames

    Mode 1: if option '-c' is *not* provided, looks for files
    "XXX-Squared.mhd" (in the same dir than the filenames). Squared
    images will be used to compute the uncertainty with the history by
    history method [Chetty2006, IJROBP]. The number of events (option
    -n) must be provided.

    Mode 2: if option '-c' is provided, image values are considered as
    counts of Poisson distribution. The variance is thus equal to the
    mean. No need to indicate the number of events.

    Option '-s' and '-t': display slice by slice mean relative
    uncertainty. Only consider pixel values greater than threshold %
    of the max value in the image.

    Example1:
    gt_image_uncertainty run.XYZ/output_*/dose-Edep.mhd -o u.mhd -N 100000000

    Example2:
    gt_image_uncertainty output/projection.mhd -c -o u.mhd -s -t 0.1

    Example3:
    gt_image_uncertainty output/projection.mhd -c -o u.mhd -s -t 0.1 -e output/stats.txt

    (Not yet implemented: efficiency image)
    
    '''

    # logger
    gt.logging_conf(**kwargs)

    # do nothing if no filenames
    if len(filenames) == 0:
        logger.error('Please provide at least one filename')
        exit()

    # ensure that nevents is an int (convert sci notation e.g. 1e5)
    nevents = int(float(nevents))

    # verbose
    if verbose:
        logger.info("Found {} file(s)".format(len(filenames)))

    # efficiency ?
    sigma_flag = sigma
    time = 0.0
    if efficiency:
        fp = open(efficiency, 'r')
        line = fp.readline()
        while line:            
            m = re.match(r'.*ElapsedTime = (.*)', line)
            if m:
                time = float(m.group(1))
            line = fp.readline()
        fp.close()
        
    # uncertainty with squared images
    if not counts:
        # find the squared images filenames
        sfilenames = []
        for f in filenames:
            fs = os.path.splitext(f)[0]+'-Squared'+os.path.splitext(f)[1]
            exist = os.path.isfile(fs)
            if not exist:
                logger.error('The file {} does not exist'.format(fs))
                exit()
            if verbose:
                logger.info('Found squared image {}'.format(fs))
            sfilenames.append(fs)
        # compute uncertainty history by hitory
        if by_slice:
            uncertainty, m, nb = gt.image_uncertainty_by_slice(filenames, sfilenames, nevents, sigma_flag, threshold)
        else:
            uncertainty = gt.image_uncertainty(filenames, sfilenames, nevents, sigma_flag, threshold)
    else:
        # compute uncertainty Poisson
        if by_slice:
            uncertainty, m, nb = gt.image_uncertainty_Poisson_by_slice(filenames, sigma_flag, threshold)
        else:
            uncertainty = gt.image_uncertainty_Poisson(filenames, sigma_flag, threshold)


    if by_slice:
        i =0
        for mean,n in zip(m, nb):
            if efficiency:
                eff = 1.0/(time * mean)
                logger.info("Channel {0} uncertainty and nb pixels = {1:6.2f} % {2:10}  efficiency = {3:6.15f}"
                      .format(i, mean*100.0, n, eff))
            else:
                logger.info("Channel {0} uncertainty and nb pixels = {1:6.2f} % {2:10}".format(i, mean*100.0, n))
            i = i+1


    # write file
    if verbose:
        logger.info('Write {}'.format(output))
    itk.imwrite(uncertainty, output)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_uncertainty()
