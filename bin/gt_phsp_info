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
import os
import logging
import uproot

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('filename')
@click.option('--tree', '-t', default='PhaseSpace',
              help='Name of the tree to show in the root file')
@click.option('-n', default=float(1e5), help='Use -1 to read all data')
@gt.add_options(gt.common_options)
def gt_phsp_info(filename, n, tree, **kwargs):
    """
    \b
    Print information about the given PHSP phase-space file

    \b
    <FILENAME> : input PHSP root/npy file
    """

    # logger
    gt.logging_conf(**kwargs)

    data, keys, m = phsp.load(filename, treename=tree, nmax=n)

    # print info
    print(f'File:        {filename}')
    statinfo = os.stat(filename)
    print(f'Size:        {phsp.humansize(statinfo.st_size)}')
    b, extension = os.path.splitext(filename)
    if extension == '.root':
        t = 'root'
        f = uproot.open(filename)
        print(f'Branches:    {f.keys()}')
    if extension == '.npy' or extension == '.npz':
        t = 'npy'
    print(f'Type:        {t} {data.dtype}')
    print(f'Nb values:   {m} ({m:.2e})')
    n = len(data)
    print(f'Read values: {n} ({n:.2e})')
    print(f'Nb of keys:  {len(keys)}')
    print(f'Keys:        ', *keys)

    # stats info per key
    print('{:<10} {:>10} {:>10} {:>10} {:>10}'.format('key', 'min', 'max', 'mean', 'std'))
    i = 0
    for k in keys:
        x = data[:, i]
        try:
            xmin = np.amin(x)
            xmax = np.amax(x)
            xmean = np.mean(x)
            xstd = np.std(x)
            print(f'{k:10} {xmin:10.3f} {xmax:10.3f} {xmean:10.3f} {xstd:10.3f}')
        except:
            # probably string values (ignored for the moment)
            s, cts = np.unique(x, return_counts=True)
            print(f'{k:10} {s} {cts}')
            pass
        i = i + 1


# --------------------------------------------------------------------------
if __name__ == '__main__':
    gt_phsp_info()
