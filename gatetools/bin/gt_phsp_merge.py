#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import numpy as np
import gatetools.phsp as phsp
import gatetools as gt
import click
import logging

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('input_filenames', nargs=-1)
@click.option('--output', '-o', required=True)
@gt.add_options(gt.common_options)
def gt_phsp_merge(input_filenames, output, **kwargs):
    """
    \b
    Merge several npy PHSP files

    \b
    <INPUT_FILENAMES> : input PHSP npy files
    """

    # logger
    gt.logging_conf(**kwargs)

    if len(input_filenames) == 0:
        exit(0)

    # read initial keys
    d, keys, n = phsp.load(input_filenames[0], 1)

    def read(f, keys):
        # load data and keys
        d, read_keys, n = phsp.load(f)
        # check keys
        if keys != read_keys:
            logger.error('Keys are not identical. Abort.')
            logger.error('Previous keys : ', keys)
            logger.error('Current keys : ', read_keys, f)
            exit(0)
        return d

    data = np.concatenate([read(x, keys) for x in input_filenames])

    # write 
    phsp.save_npy(output, data, keys)


# --------------------------------------------------------------------------
if __name__ == '__main__':
    gt_phsp_merge()
