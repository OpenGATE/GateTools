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
@click.argument('filenames', nargs=-1)
@click.option('-n', default=float(1e5), help='Use -1 to read all data')
@click.option('--keys', '-k', help='Plot the given keys (as a str list such that "X Y Z")', default='')
@click.option('--skip', multiple=True, help='(string) Dont plot if this str is contained in a branch name')
@click.option('--quantile', '-q', default=float(0), help='Restrict histogram to quantile')
@click.option('--nb_bins', '-b', default=int(100), help='Number of bins')
@click.option('--tree', '-t', default='PhaseSpace', help='Name of the tree in the root file')
@click.option('--shuffle', '-s', default=False, is_flag=True, help='shuffle samples when loading')
@click.option('--output', '-o', type=str, help='Do not plot, only output a pdf with the given name')
@click.option('--plot2d',
              type=(str, str),
              help='Add 2D plots (key1,key2), such as --plot2d X Ekine --plot2d X Y ', multiple=True)
@gt.add_options(gt.common_options)
def gt_phsp_plot(filenames, keys, n, quantile, tree, nb_bins, plot2d, shuffle, skip, output, **kwargs):
    """
    \b
    Plot histograms

    \b
    <INPUT_FILENAME> : input PHSP root/pny files

    WARNING: if several filenames, they must have the same keys
    """

    # logger
    gt.logging_conf(**kwargs)

    f = None
    nb_fig = 0
    q = {}

    first_keys = None

    skip_branches = skip

    for filename in filenames:
        logger.info(filename)

        # load data
        data, read_keys, m = phsp.load(filename, tree, n, shuffle)
        if n == -1:
            n = m
        print(f'Reading {n}/{m}')

        # get keys
        ckeys = phsp.str_keys_to_array_keys(keys)
        if len(ckeys) == 0:
            ckeys = read_keys

        # store order for the other filename
        if not first_keys:
            first_keys = ckeys
            fk = []
            # remove skip keys
            for k in first_keys:
                add = True
                for sk in skip_branches:
                    if sk in k:
                        print('Skip branch ', k)
                        add = False
                if add:
                    fk.append(k)
            first_keys = fk

        # 2D figs
        keys_2D = plot2d
        if keys_2D == None:
            keys_2D = []

        # compute fig row/col
        nb_fig = len(first_keys) + len(keys_2D)
        nrow, ncol = phsp.fig_get_nb_row_col(nb_fig)

        # create fig
        if not f:
            f, ax = plt.subplots(nrow, ncol, figsize=(25, 10))

        # loop
        i = 0
        nfig = 0
        for k in first_keys:
            if k not in read_keys:
                print(f'Skip key {k}: not in the first list of keys')
                continue

            # get data
            index = read_keys.index(k)
            x = data[:, index]

            if len(x) < 1:
                print(f'Skip key {k}: empty')
                continue

            # check validity
            if type(x[0]) == str:
                print(f'Skip key {k} : str')
                continue
            try:
                a = int(x[0])
            except:
                print(f'Skip key {k}: not numeric? x[0] = {x[0]}')
                continue
            # sometimes, if x is a str (from a root file), x[0] will be 'NULL'
            # (probably not the best method ; to be changed)
            if x[0] == 'NULL':
                print(f'Skip key {k} : not numeric? x[0] = NUL')
                continue

            # get mean to check if nan
            xmean = np.mean(x)
            xmax = np.max(x)
            xmin = np.min(x)
            print(f'Key {k} min/mean/max: {xmin} {xmean} {xmax}')
            if np.isnan(xmean):
                print(f'Skip key {k} : nan ?')
                continue

            a = phsp.fig_get_sub_fig(ax, i)
            q1 = quantile
            q2 = 1.0 - quantile
            if filename == filenames[0]:
                q[k] = (np.quantile(x, q1), np.quantile(x, q2))
            if k not in q:
                q[k] = (np.quantile(x, q1), np.quantile(x, q2))

            label = ' {} $\mu$={:.2f} $\sigma$={:.2f}'.format(k, np.mean(x), np.std(x))
            a.hist(x, nb_bins,
                   # density=True,
                   histtype='stepfilled',
                   range=q[k],
                   # facecolor='g',
                   alpha=0.5,
                   label=label)
            # a.set_ylabel('Probability')
            a.set_ylabel('Counts')
            a.legend()
            i = i + 1
            nfig += 1

        # 2D
        for k in keys_2D:
            a = phsp.fig_get_sub_fig(ax, i)
            phsp.fig_histo2D(a, data, read_keys, k, nb_bins, 'g')
            i = i + 1

    if nb_fig == 0:
        return

    # remove empty plot
    phsp.fig_rm_empty_plot(nb_fig, nfig, ax)
    f.set_size_inches(18.5, 10.5, forward=True)

    if n == -1:
        n = m
    if n > m:
        n = m
    n = int(n)
    m = int(m)
    # plt.subplots_adjust(top=0.7)
    plt.suptitle(f'Values: {n}/{m}')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if output:
        plt.savefig(output)
    else:
        plt.show()
    plt.close()


# --------------------------------------------------------------------------
if __name__ == '__main__':
    gt_phsp_plot()
