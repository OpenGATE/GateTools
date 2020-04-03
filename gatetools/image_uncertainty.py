# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""

This module provides a function to compute relative statistical
uncertainty (typically for Edep or Dose), with the history by history
method as explained for example in [Chetty2006]

"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import itk
import gatetools as gt
from functools import reduce
import operator
import numpy as np
import numpy.testing as npt
import logging
logger=logging.getLogger(__name__)

def relative_uncertainty_Poisson(x, sigma_flag, threshold=0):
    u = np.sqrt(x)
    if not sigma_flag:
        u = np.divide(u, x, out=np.ones_like(x), where=x > threshold)
    return u


def relative_uncertainty(x, sq_x, N, sigma_flag, threshold=0):
    # sometimes strange warning : 'invalid value encountered in sqrt'
    # --> seems when values too close to zero
    # sv = np.seterr(all='raise')
    # If the warning is changed to an error, it becomes
    # FloatingPointError: underflow encountered in sqrt:
    # https://github.com/numpy/numpy/issues/11448
    #
    # corrected sample standard deviation
    # https://en.wikipedia.org/wiki/Standard_deviation#Corrected_sample_standard_deviation
    # See also Chetty2006 (IJROBP)

    u = (sq_x/N - (x/N)**2) / (N-1)
    # idem ->    u = np.sqrt( (N*sq_x - x*x) / (N-1) )
    u[u<1e-40] = 0.0
    u = np.sqrt(u)
    if not sigma_flag:
        u = np.divide(u, x/N, out=np.ones_like(x), where=x > threshold)
    return u


def relative_uncertainty_by_slice(x, sigma_flag, threshold=0, sq_x=[], N=0):
    i=0
    means = []
    nb = []
    uncertainty = np.copy(x)
    uncertainty.fill(0.0)
    use_square = False
    if len(sq_x)>0:
        use_square = True
    else:
        sq_x = x

    for s, sq in zip(x, sq_x):
        t = np.max(s)*threshold
        if use_square:
            u = relative_uncertainty(s, sq, N, sigma_flag, t)
        else:
            u = relative_uncertainty_Poisson(s, sigma_flag, t)
        n = len(np.where(s > t)[0])
        if n==0:
            mean = 1.0
        else:
            mean = u[np.where(s > t)].sum()
            mean = mean/n
        means.append(mean)
        nb.append(n)
        uncertainty[i] = u
        i = i + 1

    return uncertainty, means, nb


def check_N(N):
    N = float(N)
    if N<0:
        raise RuntimeError('ERROR: N  must be positive')


def image_uncertainty(img_list=[], img_squared_list=[], N=0, sigma_flag=False, threshold=0):
    check_N(N)

    # Get the sums
    img_sum = gt.image_sum(img_list)
    img_sq_sum = gt.image_sum(img_squared_list)

    # View as np
    np_sum = itk.array_view_from_image(img_sum)
    np_sq_sum = itk.array_view_from_image(img_sq_sum)

    # Compute relative uncertainty [Chetty 2006]
    t = np.max(np_sum)*threshold
    uncertainty = relative_uncertainty(np_sum, np_sq_sum, N, t)

    # create and return itk image
    img_uncertainty = itk.image_from_array(uncertainty)
    img_uncertainty.CopyInformation(img_sum)
    return img_uncertainty


def image_uncertainty_by_slice(img_list=[], img_squared_list=[], N=0, sigma_flag=False, threshold=0):
    check_N(N)

    # Get the sums
    img_sum = gt.image_sum(img_list)
    img_sq_sum = gt.image_sum(img_squared_list)

    # View as np
    np_sum = itk.array_view_from_image(img_sum)
    np_sq_sum = itk.array_view_from_image(img_sq_sum)

    # compute uncertainty
    uncertainty, means, nb = relative_uncertainty_by_slice(np_sum, sigma_flag, threshold, np_sq_sum, N)

    # create and return itk image
    img_uncertainty = itk.image_from_array(uncertainty)
    img_uncertainty.CopyInformation(img_sum)
    return img_uncertainty, means, nb


def image_uncertainty_Poisson(img_list=[], sigma_flag=False, threshold=0):
    # Get the sums
    img_sum = gt.image_sum(img_list)

    # View as np
    np_sum = itk.array_view_from_image(img_sum)

    # Convert to float
    np_sum = np_sum.astype(np.float64)

    # Get stddev (variance is the mean)
    sigma_flag = np.sqrt(np_sum)

    # compute uncertainty
    t = np.max(np_sum)*threshold
    uncertainty = relative_uncertainty_Poisson(np_sum, t)

    # np is double, convert to float32
    uncertainty = uncertainty.astype(np.float32)

    # create and return itk image
    img_uncertainty = itk.image_from_array(uncertainty)
    img_uncertainty.CopyInformation(img_sum)
    return img_uncertainty


def image_uncertainty_Poisson_by_slice(img_list=[], sigma_flag=False, threshold=0):
    # Get the sums
    img_sum = gt.image_sum(img_list)

    # View as np
    np_sum = itk.array_view_from_image(img_sum)

    # Convert to float
    np_sum = np_sum.astype(np.float64)

    # compute uncertainty
    uncertainty, means, nb = relative_uncertainty_by_slice(np_sum, sigma_flag, threshold)

    # np is double, convert to float32
    uncertainty = uncertainty.astype(np.float32)

    # create and return itk image
    img_uncertainty = itk.image_from_array(uncertainty)
    img_uncertainty.CopyInformation(img_sum)
    return img_uncertainty, means, nb

#####################################################################################
import unittest
import hashlib
import os
import hashlib
import numpy as np
import shutil
import tempfile
from .logging_conf import LoggedTestCase

class Test_Uncertainty(LoggedTestCase):
    def test_image_uncertainty(self):
        x = np.arange(0, 1, 0.01)
        y = np.arange(0, 1, 0.01)
        z = np.arange(0, 1, 0.01)
        xx, yy, zz = np.meshgrid(x, y, z)
        npImage = 10*xx+4.5
        npsImage = 10*xx**2+9*xx+2.85
        image = itk.image_from_array(np.float32(npImage))
        images = [image]
        simage = itk.image_from_array(np.float32(npsImage))
        simages = [simage]
        uncertainty = image_uncertainty(images, simages, N=1000000000000)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(uncertainty, os.path.join(tmpdirpath, "uncertainty.mha"))
        with open(os.path.join(tmpdirpath, "uncertainty.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("0a2dc7a0e28509c569cecde6b6252507936b29365cb4db0c75ab3c0fab3b2bc4" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_image_uncertainty_by_slice(self):
        x = np.arange(0, 1, 0.01)
        y = np.arange(0, 1, 0.01)
        z = np.arange(0, 1, 0.01)
        xx, yy, zz = np.meshgrid(x, y, z)
        npImage = 10*xx+4.5
        npsImage = 10*xx**2+9*xx+2.85
        image = itk.image_from_array(np.float32(npImage))
        images = [image]
        simage = itk.image_from_array(np.float32(npsImage))
        simages = [simage]
        uncertainty, mean, nb = image_uncertainty_by_slice(images, simages, N=1000000000000)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(uncertainty, os.path.join(tmpdirpath, "uncertainty.mha"))
        #self.assertTrue(mean[0] == 0.3356322509765625)
        npt.assert_almost_equal(mean[0], 0.3356322509765625)
        self.assertTrue(nb[0] == 10000)
        with open(os.path.join(tmpdirpath, "uncertainty.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("0a2dc7a0e28509c569cecde6b6252507936b29365cb4db0c75ab3c0fab3b2bc4" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_image_uncertainty_Poisson(self):
        x = np.arange(0, 1, 0.01)
        y = np.arange(0, 1, 0.01)
        z = np.arange(0, 1, 0.01)
        xx, yy, zz = np.meshgrid(x, y, z)
        npImage = 10*xx+4.5
        image = itk.image_from_array(np.float32(npImage))
        images = [image]
        uncertainty = image_uncertainty_Poisson(images)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(uncertainty, os.path.join(tmpdirpath, "uncertainty.mha"))
        with open(os.path.join(tmpdirpath, "uncertainty.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("cb58fb2f5490546bb83b9e0e51ce1d87b13eab2f0f4ebddc4e9c767c8b98e57b" == new_hash)
        shutil.rmtree(tmpdirpath)
    def test_image_uncertainty_Poisson_by_slice(self):
        x = np.arange(0, 1, 0.01)
        y = np.arange(0, 1, 0.01)
        z = np.arange(0, 1, 0.01)
        xx, yy, zz = np.meshgrid(x, y, z)
        npImage = 10*xx+4.5
        image = itk.image_from_array(np.float32(npImage))
        images = [image]
        uncertainty, mean, nb = image_uncertainty_Poisson_by_slice(images)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(uncertainty, os.path.join(tmpdirpath, "uncertainty.mha"))
        npt.assert_almost_equal(mean[0], 0.33836081024332604)
        self.assertTrue(nb[0] == 10000)
        with open(os.path.join(tmpdirpath, "uncertainty.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("cb58fb2f5490546bb83b9e0e51ce1d87b13eab2f0f4ebddc4e9c767c8b98e57b" == new_hash)
        shutil.rmtree(tmpdirpath)
