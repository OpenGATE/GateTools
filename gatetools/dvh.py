# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides a tool to have dvh values
"""

import os
import itk
import numpy as np
import math
import logging
logger=logging.getLogger(__name__)

def createDVH(dose=None, roi=None, binning=1, label=1):

    if dose is None:
        logger.error("Set the dose image")
        sys.exit(1)
    if roi is  None:
        logger.error("Set the ROI image")
        sys.exit(1)

    if not np.allclose(dose.GetLargestPossibleRegion().GetSize(), roi.GetLargestPossibleRegion().GetSize()):
        logger.error("images have incompatible size")
        sys.exit(1)
    elif not np.allclose(dose.GetOrigin(), roi.GetOrigin()):
        logger.error("images have incompatible origins")
        sys.exit(1)
    elif not np.allclose(dose.GetSpacing(), roi.GetSpacing()):
        logger.error("images have incompatible spacing")
        sys.exit(1)

    if binning > 100 or binning < 0:
        logger.error("binning have to be between 0 and 1")
        sys.exit(1)

    statsRoiFilter = itk.LabelStatisticsImageFilter.New(dose)
    statsRoiFilter.SetLabelInput(roi)
    statsRoiFilter.UseHistogramsOn()
    statsRoiFilter.Update()
    statsRoiFilter.SetHistogramParameters(100, statsRoiFilter.GetMinimum(label), statsRoiFilter.GetMaximum(label))
    statsRoiFilter.Update()
    histogramRoi = statsRoiFilter.GetHistogram(label)

    doseValues = []
    volumePercentage = np.linspace(0,100, int(101/binning))
    for vol in volumePercentage:
        doseValues.append(histogramRoi.Quantile(0, vol/100))

    return (doseValues[::-1], volumePercentage)


#####################################################################################
import unittest
import sys
from datetime import datetime
import tempfile
import hashlib
import shutil
import wget
import pydicom
import gatetools as gt
from matplotlib import pyplot as plt
from .logging_conf import LoggedTestCase

class Test_DVH(LoggedTestCase):
    def test_dvh(self):
        logger.info('Test_DVH test_dvh')
        tmpdirpath = tempfile.mkdtemp()
        filenameStruct = wget.download("https://github.com/OpenGATE/GateTools/raw/master/dataTest/rtstruct.dcm", out=tmpdirpath, bar=None)
        structset = pydicom.read_file(os.path.join(tmpdirpath, filenameStruct))
        filenameDose = wget.download("https://github.com/OpenGATE/GateTools/raw/master/dataTest/rtdose.dcm", out=tmpdirpath, bar=None)
        doseImage = gt.read_3d_dicom([os.path.join(tmpdirpath, filenameDose)])
        transformImage = gt.applyTransformation(input=doseImage, neworigin=[-176, -320, -235])

        aroi = gt.region_of_interest(structset, "PTV")
        mask = aroi.get_mask(transformImage, corrected=False)
        doseValues, volumePercentage = createDVH(transformImage, mask)
        self.assertTrue(np.allclose(doseValues, np.array([20.190093994140625, 18.959465690369303, 18.804925906404534, 18.722033155678602, 18.65508902237712, 18.588144889075636, 18.54843987974758, 18.515462037085403, 18.48248419442323, 18.449506351761055, 18.416528509098878, 18.383550666436705, 18.36128805124364, 18.34407627435657, 18.3268644974695, 18.309652720582427, 18.292440943695357, 18.275229166808288, 18.258017389921214, 18.240805613034144, 18.223593836147074, 18.20638205926, 18.18917028237293, 18.17195850548586, 18.15832293014844, 18.144878469535126, 18.131434008921808, 18.117989548308493, 18.104545087695175, 18.09110062708186, 18.077656166468543, 18.06421170585523, 18.05076724524191, 18.037322784628596, 18.023878324015282, 18.010433863401964, 17.99698940278865, 17.98354494217533, 17.970100481562017, 17.952081204966813, 17.93372760177487, 17.91537399858293, 17.897020395390985, 17.87866679219904, 17.8603131890071, 17.841959585815157, 17.823605982623217, 17.805252379431273, 17.786898776239333, 17.76854517304739, 17.73303607506088, 17.696259518876857, 17.659482962692838, 17.62270640650882, 17.5859298503248, 17.529769002066715, 17.449064892662893, 17.36836078325907, 17.256013233455143, 17.13010433149633, 16.947348849463996, 16.722613833745307, 16.46719982670801, 16.19484141089698, 15.867015321183896, 15.552174179033281, 15.12138749419663, 14.70582691995718, 14.233208816528286, 13.741762860616019, 13.165333616322455, 12.66873394185843, 12.147829191034457, 11.52253017831352, 10.796975261607027, 10.168621249118061, 9.575371758834134, 8.933918659359762, 8.28197685241694, 7.411067305841686, 6.718576116764754, 6.187590913772536, 5.460579210519747, 4.726885546956693, 4.155722666801244, 3.636236033439593, 3.095574108191859, 2.5588087081908752, 2.103911293469914, 1.6858728885650334, 1.2582232485646465, 0.911330363526913, 0.6222875390733799, 0.3946928688883681, 0.2595600974559683, 0.18113183203220395, 0.1449054656257626, 0.10867909921932127, 0.07245273281287994, 0.0362263664064386, -2.727374406249264e-15])))
        self.assertTrue(np.allclose(volumePercentage, np.array(list(range(0, 101)))))
        shutil.rmtree(tmpdirpath)

