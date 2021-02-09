#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import sys
import numpy as np
import gatetools.phsp as phsp
import gatetools as gt
import click
import os
import logging

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('input_filename')
@click.option('-n', default=float(-1), help='Use -1 to read all data')
@click.option('--nb_peaks', '-p', default=int(2), help='Number of peaks to find')
@click.option('--output', '-o', default='auto', help="If 'auto', use filename_E.pth")
@click.option('--dry_run/--no-dry_run', default=False)
@gt.add_options(gt.common_options)
def gt_phsp_peaks(input_filename, n, nb_peaks, dry_run, output, **kwargs):
    """
    \b
    Detect and separate the energy peaks. 

    \b
    <INPUT_FILENAME> : input PHSP root file
    """

    # logger
    gt.logging_conf(**kwargs)

    if output == 'auto':
        b, extension = os.path.splitext(input_filename)
        output_filename = b
    else:
        output_filename = output
    logger.info('output', output_filename)

    # load data keys and the total nb of values (m) ; only n values are read
    data, keys, m = phsp.load(input_filename, n)

    # get E 
    E, index = phsp.get_E(data, keys)

    # counts elements and sort
    values, counts = np.unique(E, return_counts=True)
    values = [v for _, v in sorted(zip(counts, values))]
    counts = np.sort(counts)
    values = values[::-1]
    counts = counts[::-1]

    # 
    filename, extension = os.path.splitext(input_filename)
    for i in range(nb_peaks):
        v = values[i]
        condition = data[:, index] == v
        d = data[condition]
        data = data[np.logical_not(condition)]
        e = str(v * 1000)
        er = str(int(round(v * 1000)))
        out = output_filename + '_' + er + '.npy'
        logger.info('Write peak', e, 'keV with', len(d), 'elements in', out)
        if not dry_run:
            phsp.save_npy(out, d, keys)

    # write
    out = output_filename + '_nopeak' + '.npy'
    logger.info('Write remaining data with', len(data), 'elements in', out)
    if not dry_run:
        phsp.save_npy(out, data, keys)


# --------------------------------------------------------------------------
if __name__ == '__main__':
    gt_phsp_peaks()
