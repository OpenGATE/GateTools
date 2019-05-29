#!/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import sys
import os
import uproot
import time
import tokenize
from io import BytesIO

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

''' ---------------------------------------------------------------------------
Load a PHSP (Phase-Space) file
Output is numpy structured array
'''
def load(filename, nmax=-1, random=False):
    b, extension = os.path.splitext(filename)
    nmax = int(nmax)

    if extension == '.root':
        if random:
            print('Error, cannot random on root file for the moment')
            exit(0)
        return load_root(filename, nmax)

    # if extension == '.raw':
    #     return load_raw(filename)

    if extension == '.npy':
        return load_npy(filename, nmax, random)

    print('Error, dont know how to open phsp with extension ',
          extension,
          ' (known extensions: .root .npy)')
    exit(0)


''' ---------------------------------------------------------------------------
Load a PHSP (Phase-Space) file in root format
Output is numpy structured array
'''
def load_root(filename, nmax=-1):
    nmax = int(nmax)
    # Check if file exist
    if (not os.path.isfile(filename)):
        print("File '"+filename+"' does not exist.")
        exit()

    # Check if this is a root file
    try:
        f = uproot.open(filename)
    except Exception:
        print("File '"+filename+"' cannot be opened, not root file ?")
        exit()

    # Look for a single key named "PhaseSpace"
    k = f.keys()
    try:
        psf = f['PhaseSpace']
    except Exception:
        print("This root file does not look like a PhaseSpace, keys are: ",
              f.keys(), ' while expecting "PhaseSpace"')
        exit()
        
    # Get keys
    names = [k.decode('UTF-8') for k in psf.keys()]
    n = psf.numentries

    # Convert to arrays (this take times)
    if (nmax != -1):
        a = psf.arrays(entrystop=nmax)
    else:
        a = psf.arrays()

    # Concat arrays
    d = np.column_stack( a[k] for k in psf.keys())
    #d = np.float64(d) # long
    
    return d, names, n


''' ---------------------------------------------------------------------------
Load a PHSP (Phase-Space) file in npy
Output is numpy structured array
'''
def load_npy(filename, nmax=-1, random=False):
    # Check if file exist
    if (not os.path.isfile(filename)):
        print("File '"+filename+"' does not exist.")
        exit()

    x = np.load(filename, mmap_mode='r')
    n = len(x)
    if nmax > 0:
        if random:
            x = np.random.choice(x, nmax, replace=False)
        else:
            x = x[:nmax]

    data = x.view(np.float32).reshape(x.shape + (-1,))
    #data = np.float64(data) # long
    return data, list(x.dtype.names), n



''' ---------------------------------------------------------------------------
 https://stackoverflow.com/questions/14996453/python-libraries-to-calculate-human-readable-filesize-from-bytes
'''
def humansize(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


''' ---------------------------------------------------------------------------
Write a PHSP (Phase-Space) file in npy
'''
def save_npy(filename, data, keys):

    dtype = []
    for k in keys:
        dtype.append((k, 'f4'))
    
    r = np.zeros(len(data), dtype=dtype)
    i = 0
    for k in keys:
        r[k] = data[:,i]
        i = i+1

    np.save(filename, r)


''' ---------------------------------------------------------------------------
Remove som keys
'''
def remove_keys(data, keys, rm_keys):

    cols = np.arange(len(keys))
    index = []
    if len(rm_keys) == 0:
        return data, keys
    
    for k in rm_keys:
        print(k)
        if k not in keys:
            print('Error the key', k, 'does not exist in', keys)
            exit(0)
        i = keys.index(k)
        cols = np.delete(cols, i)
        index.append(i)
        for c in index:
            keys.pop(c)
    data = data[:, cols]
    print(keys)
    return data, keys


''' ---------------------------------------------------------------------------
Convert string of keys to arrays of key
'''
def str_keys_to_array_keys(keys):
    if keys == None:
        return []
    dd = tokenize.tokenize(BytesIO(keys.encode('utf-8')).readline)
    keys = []
    for toknum, tokval, _, _, _ in dd:
        if tokval != 'utf-8' and tokval != '' and tokval != None:
            keys.append(tokval)
    return keys


''' ----------------------------------------------------------------------------
Retrive the E from a dataset
---------------------------------------------------------------------------- '''
def get_E(data, keys):
    try:
        Ei = keys.index('Ekine')
    except:
        try:
            Ei = keys.index('E')
        except:
            raise RuntimeError("Error, cannot find key 'Ekine' nor 'E'. Keys are: ", keys)
    E = data[:,Ei]
    return E, Ei


''' ----------------------------------------------------------------------------
Retrive a fig nb 
---------------------------------------------------------------------------- '''
def fig_get_sub_fig(ax, i):
    # check if single fig
    if not type(ax) is np.ndarray:
        return ax

    # check if single row/line
    if ax.ndim == 1:
        return ax[i]

    # other cases
    index = np.unravel_index(i, ax.shape)
    return ax[index[0]][index[1]]


''' ----------------------------------------------------------------------------
Compute a fig with adapted row/col for n fig
---------------------------------------------------------------------------- '''
def fig_get_nb_row_col(nfig):
    nrow = int(np.sqrt(nfig))
    ncol = int(nfig/nrow)
    if ncol*nrow<nfig:
        nrow += 1
    return nrow, ncol


''' ----------------------------------------------------------------------------
Remove empty plot
---------------------------------------------------------------------------- '''
def fig_rm_empty_plot(nfig, ax):
    nrow, ncol = fig_get_nb_row_col(nfig)
    r = nrow-1
    i = nfig
    while i<ncol*nrow:
        c = i-int(i/ncol)*ncol
        ax[r,c].set_axis_off()
        i = i+1  



''' ---------------------------------------------------------------------------
In the list of keys, toggle angleXY to XY or XY to angleXY
'''
def keys_toggle_angle(keys):

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

        
'''  ---------------------------------------------------------------------------
Keep only the given keys
'''
def select_keys(data, input_keys, output_keys):

    cols = np.arange(len(input_keys))
    index = []
    if len(output_keys) == 0:
        print('Error, select_keys is void')
        exit(0)

    cols = []
    for k in output_keys:
        try:
            i = input_keys.index(k)
            cols.append(i)
        except:
            print('Error, cannot find',k,'in keys:',input_keys)
            exit(0)

    data = data[:, cols]
    return data


'''  ---------------------------------------------------------------------------
Add and compute angleXY in the list of keys
 angle = atan2(k2,k1)
'''
def add_angle(data, keys, k1='X', k2='Y'):

    if 'angleXY' in keys:
        return data, keys
    
    i1 = keys.index(k1)
    i2 = keys.index(k2)
    angle = np.arctan2(data[:,i2], data[:,i1])
    data = np.column_stack((data, angle))
    k = keys.copy()
    k.append('angleXY')    
    return data, k
 


''' ----------------------------------------------------------------------------
Add X and Y from angleXY
---------------------------------------------------------------------------- '''
def add_vector_angle(data, keys, radius, k='angleXY', k1='X', k2='Y'):

    # nothing to do if already exist
    if k1 in keys and k2 in keys:
        return data, keys

    if k not in keys:
        print('Cannot convert angle, the key angleXY does not exist in ', keys)

    i = keys.index(k)
    angle = data[:,i]
    dx = radius * np.cos(angle)
    dy = radius * np.sin(angle)
    data = np.column_stack((data, dx))
    data = np.column_stack((data, dy))

    kk = keys.copy()
    kk.append(k1)
    kk.append(k2)
    return data, kk

''' ----------------------------------------------------------------------------
Add missing keys (angleXY or X+Y)
---------------------------------------------------------------------------- '''
def add_missing_angle(data, input_keys, output_keys, radius):
    
    if 'angleXY' in output_keys:
        data, input_keys = add_angle(data, input_keys)

    if 'X' in output_keys and 'Y' in output_keys:
        data, input_keys = add_vector_angle(data, input_keys, radius)

    return data, input_keys
