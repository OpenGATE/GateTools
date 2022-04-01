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
from matplotlib import pyplot as plt
import logging
import math

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('filenames', nargs=2)
@click.option('-n', default=float(-1), help='Use -1 to read all data')
@click.option('--keys', '-k', help='Plot the given keys (as a str list such that "X Y Z")', default='')
@click.option('--tree', '-t', default='PhaseSpace', help='Name of the tree in the root file')
@gt.add_options(gt.common_options)
def gt_phsp_plot(filenames, keys, n, tree, **kwargs):
    """
    \b
    Compare two phsp, sample per sample

    \b
    <INPUT_FILENAME> : input PHSP root/pny files
    """

    # logger
    gt.logging_conf(**kwargs)

    # load data
    data1, read_keys1, m1 = phsp.load(filenames[0], tree, n)
    if n == -1 or n > m1:
        n = m1
    print(f'Reading {n}/{m1}')

    data2, read_keys2, m2 = phsp.load(filenames[1], tree, n)
    print(f'Reading {n}/{m2}')

    # select keys
    if keys:
        keys = phsp.str_keys_to_array_keys(keys)
    else:
        keys = read_keys1

    # loop on keys
    for k in keys:
        if k not in read_keys1:
            print(f'Warning : key {k} not in {filenames[0]}')
            continue
        index1 = read_keys1.index(k)
        if k not in read_keys2:
            print(f'Warning : key {k} not in {filenames[1]}')
            continue
        index2 = read_keys2.index(k)
        x1 = data1[:, index1]
        x2 = data2[:, index2]
        is_close = np.allclose(x1, x2)
        print(f'Compare {k} : {is_close}')
        if not is_close:
            dmin = (np.min(x1) - np.min(x2)) / np.min(x1) * 100
            dmean = (np.mean(x1) - np.mean(x2)) / np.mean(x1) * 100
            dmax = (np.max(x1) - np.max(x2)) / np.max(x1) * 100
            print(f'    min/mean/max: {dmin:.2f} {dmean:.2f} {dmax:.2f} % ')
            for i in range(int(n) - 1):
                close = np.isclose(x1[i], x2[i])
                if not close:
                    d = (x1[i] - x2[i]) / x1[i] * 100
                    print(f'{i} -> {x1[i]:.4f} vs {x2[i]:.4f} -> {d:.2f}% ')


# --------------------------------------------------------------------------
if __name__ == '__main__':
    gt_phsp_plot()
