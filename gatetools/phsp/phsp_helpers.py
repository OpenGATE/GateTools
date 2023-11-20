# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import numpy as np
import os
import tokenize
from io import BytesIO
from matplotlib import pyplot as plt
import uproot
import logging

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
def load(filename, treename='PhaseSpace', nmax=-1, nstart=0, shuffle=False):
    """ 
    Load a PHSP (Phase-Space) file
    Output is numpy structured array

    """

    b, extension = os.path.splitext(filename)
    nmax = int(nmax)

    if extension == '.root':
        if shuffle:
            logger.error('cannot shuffle on root file for the moment')
            exit(0)
        return load_root(filename, treename, nmax=nmax, nstart=nstart)

    if extension == '.npy' or extension == '.npz':
        return load_npy(filename, nmax=nmax, nstart=nstart, shuffle=shuffle)

    logger.error('dont know how to open phsp with extension ',
                 extension,
                 ' (known extensions: .root .npy)')
    exit(0)


# -----------------------------------------------------------------------------
def load_root(filename, treename, nmax=-1, nstart=0):
    """
    Load a PHSP (Phase-Space) file in root format
    Output is numpy structured array
    """

    nmax = int(nmax)
    # Check if file exist
    if not os.path.isfile(filename):
        logger.error(f"File '{filename}' does not exist.")
        exit()

    # Check if this is a root file
    try:
        with uproot.open(filename) as f:
            k = f.keys()
            if len(k) == 1:
                treename = k[0]
            try:
                psf = f[treename]
            except Exception:
                logger.error("This root file does not look like a PhaseSpace, branches are: ",
                             f.keys(), f' while expecting {treename}')
                exit()

            # Get keys
            names = [k for k in psf.keys()]
            n = psf.num_entries

            # Convert to arrays (this take times)
            if nmax != -1:
                a = psf.arrays(entry_start=nstart, entry_stop=nmax, library="numpy")
            else:
                a = psf.arrays(library="numpy")

            # Concat arrays
            d = np.column_stack([a[k] for k in psf.keys()])
            # d = np.float64(d) # slow
    except Exception:
        logger.error(f"File '{filename}' cannot be opened, not root file ?")
        exit()

    return d, names, int(n)


# -----------------------------------------------------------------------------
def load_npy(filename, nmax=-1, nstart=0, shuffle=False):
    """
    Load a PHSP (Phase-Space) file in npy
    Output is numpy structured array
    """

    # Check if file exist
    if not os.path.isfile(filename):
        logger.error(f"File '{filename}' does not exist.")
        exit()

    x = np.load(filename, mmap_mode='r')
    n = len(x)
    if nmax > 0:
        if shuffle:
            x = np.random.choice(x, nmax, replace=False)
        else:
            x = x[nstart:nmax]

    data = x.view(np.float32).reshape(x.shape + (-1,))
    # data = np.float64(data) # slow
    return data, list(x.dtype.names), n


# -----------------------------------------------------------------------------
def humansize(nbytes):
    """
    https://stackoverflow.com/questions/14996453/python-libraries-to-calculate-human-readable-filesize-from-bytes
    """

    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


# -----------------------------------------------------------------------------
def save_npy(filename, data, keys):
    """
    Write a PHSP (Phase-Space) file in npy
    """

    dtype = []
    for k in keys:
        dtype.append((k, 'f4'))

    r = np.zeros(len(data), dtype=dtype)
    i = 0
    for k in keys:
        r[k] = data[:, i]
        i = i + 1

    np.save(filename, r)


# -----------------------------------------------------------------------------
def remove_keys(data, keys, rm_keys):
    """
    Remove som keys
    """

    cols = np.arange(len(keys))
    index = []
    if len(rm_keys) == 0:
        return data, keys

    for k in rm_keys:
        if k not in keys:
            logger.error('Error the key', k, 'does not exist in', keys)
            exit(0)
        i = keys.index(k)
        cols = np.delete(cols, i)
        index.append(i)
        for c in index:
            keys.pop(c)
    data = data[:, cols]
    return data, keys


# -----------------------------------------------------------------------------
def str_keys_to_array_keys(keys):
    """
    Convert string of keys to arrays of key
    """
    if not isinstance(keys, str):
        return keys

    if keys is None:
        return []
    dd = tokenize.tokenize(BytesIO(keys.encode('utf-8')).readline)
    keys = []
    for toknum, tokval, _, _, _ in dd:
        if tokval != 'utf-8' and tokval != '' and tokval != None:
            keys.append(tokval)
    return keys


# -----------------------------------------------------------------------------
def get_E(data, keys):
    """
    Retrieve the E from a dataset
    """

    try:
        Ei = keys.index('Ekine')
    except:
        try:
            Ei = keys.index('E')
        except:
            raise RuntimeError("Error, cannot find key 'Ekine' nor 'E'. Keys are: ", keys)
    E = data[:, Ei]
    return E, Ei


# -----------------------------------------------------------------------------
def fig_get_sub_fig(ax, i):
    """
    Retrieve a fig nb
    """

    # check if single fig
    if not type(ax) is np.ndarray:
        return ax

    # check if single row/line
    if ax.ndim == 1:
        return ax[i]

    # other cases
    index = np.unravel_index(i, ax.shape)
    return ax[index[0]][index[1]]


# -----------------------------------------------------------------------------
def fig_get_nb_row_col(nfig):
    """
    Compute a fig with adapted row/col for n fig
    """

    nrow = int(np.sqrt(nfig))
    ncol = int(nfig / nrow)
    if ncol * nrow < nfig:
        nrow += 1
    return nrow, ncol


# -----------------------------------------------------------------------------
def fig_rm_empty_plot(total, nfig, ax):
    """
    Remove empty plot
    """

    nrow, ncol = fig_get_nb_row_col(total)
    i = 0
    r = 0
    while r < nrow:
        c = 0
        while c < ncol:
            if i >= nfig:
                ax[r, c].set_axis_off()
            i += 1
            c += 1
        r += 1


# -----------------------------------------------------------------------------
def keys_toggle_angle(keys):
    """
    In the list of keys, toggle angleXY to XY or XY to angleXY
    """

    k = keys.copy()
    if 'X' in keys and 'Y' in keys:
        k.remove('X')
        k.remove('Y')
        k.append('angleXY')
    else:
        if 'angleXY' in keys:
            k.append('X')
            k.append('Y')
            k.remove('angleXY')
    return k


# -----------------------------------------------------------------------------
def select_keys(data, input_keys, output_keys):
    """
    Keep only the given keys
    """

    if len(output_keys) == 0:
        logger.error('Error, select_keys is void')
        exit(0)

    cols = []
    for k in output_keys:
        try:
            i = input_keys.index(k)
            cols.append(i)
        except:
            logger.error('Error, cannot find', k, 'in keys:', input_keys)
            exit(0)

    data = data[:, cols]
    return data


# -----------------------------------------------------------------------------
def add_angle(data, keys, k1='X', k2='Y'):
    """
    Add and compute angleXY in the list of keys
    angle = atan2(k2,k1)
    """

    if 'angleXY' in keys:
        return data, keys

    i1 = keys.index(k1)
    i2 = keys.index(k2)
    angle = np.arctan2(data[:, i2], data[:, i1])
    data = np.column_stack((data, angle))
    k = keys.copy()
    k.append('angleXY')
    return data, k


# -----------------------------------------------------------------------------
def add_vector_angle(data, keys, radius, k='angleXY', k1='X', k2='Y'):
    """
    Add X and Y from angleXY
    """

    # nothing to do if already exist
    if k1 in keys and k2 in keys:
        return data, keys

    if k not in keys:
        logger.warning('Cannot convert angle, the key angleXY does not exist in ', keys)

    i = keys.index(k)
    angle = data[:, i]
    dx = radius * np.cos(angle)
    dy = radius * np.sin(angle)
    data = np.column_stack((data, dx))
    data = np.column_stack((data, dy))

    kk = keys.copy()
    kk.append(k1)
    kk.append(k2)
    return data, kk


# -----------------------------------------------------------------------------
def add_missing_angle(data, input_keys, output_keys, radius):
    """
    Add missing keys (angleXY or X+Y)
    """

    if 'angleXY' in output_keys:
        data, input_keys = add_angle(data, input_keys)

    if 'X' in output_keys and 'Y' in output_keys:
        data, input_keys = add_vector_angle(data, input_keys, radius)

    return data, input_keys


# -----------------------------------------------------------------------------
def fig_histo2D(ax, data, keys, k, nbins, color='g'):
    """
    Fig 2D histo
    """

    i1 = keys.index(k[0])
    x = data[:, i1]
    i2 = keys.index(k[1])
    y = data[:, i2]
    if color == 'g':
        cmap = plt.cm.Greens
    if color == 'r':
        cmap = plt.cm.Reds
    if color == 'b':
        cmap = plt.cm.Blues

    counts, xedges, yedges, im = ax.hist2d(x, y, bins=(nbins, nbins), alpha=1, cmap=cmap)
    # , norm=LogNorm())
    plt.colorbar(im, ax=ax)
    ax.set_xlabel(k[0])
    ax.set_ylabel(k[1])


#####################################################################################
import unittest
import hashlib
import wget
import tempfile
import shutil
from gatetools.logging_conf import LoggedTestCase


class Test_Phsp(LoggedTestCase):
    def test_phsp_convert(self):
        logger.info('Test_Phsp test_phsp_convert')
        tmpdirpath = tempfile.mkdtemp()
        filenameRoot = wget.download(
            "https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/phsp.root?inline=false", out=tmpdirpath,
            bar=None)
        data, read_keys, m = load(os.path.join(tmpdirpath, filenameRoot), -1)
        save_npy(os.path.join(tmpdirpath, "testphsp.npy"), data, read_keys)
        with open(os.path.join(tmpdirpath, "testphsp.npy"), "rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("cec796ec5764d039b02e15d504e80ccf2b2c35e0e5380985245262faf0ff0892" == new_hash)
        dataNPY, read_keysNPY, mNPY = load(os.path.join(tmpdirpath, "testphsp.npy"), -1)
        self.assertTrue(np.allclose(131.69868, np.amax(dataNPY[:, 2])))
        shutil.rmtree(tmpdirpath)

    def test_phsp_info(self):
        logger.info('Test_Phsp test_phsp_info')
        tmpdirpath = tempfile.mkdtemp()
        filenameRoot = wget.download(
            "https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/phsp.root?inline=false", out=tmpdirpath,
            bar=None)
        data, read_keys, m = load(os.path.join(tmpdirpath, filenameRoot), -1)
        self.assertTrue("17.27 MB" == humansize(os.stat(os.path.join(tmpdirpath, filenameRoot)).st_size))
        self.assertTrue(np.float32 == data.dtype)
        self.assertTrue(782127 == m)
        self.assertTrue(7 == len(read_keys))
        self.assertTrue(np.allclose(131.69868, np.amax(data[:, 2])))
        shutil.rmtree(tmpdirpath)
