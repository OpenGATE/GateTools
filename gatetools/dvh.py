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
import scipy.interpolate
logger=logging.getLogger(__name__)

def createDVH(dose=None, roi=None, bins=1000, label=1, useCm3=False):

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

    if bins < 1:
        logger.error("bins must be superior or equal to 1")
        sys.exit(1)

    statsRoiFilter = itk.LabelStatisticsImageFilter.New(dose)
    statsRoiFilter.SetLabelInput(roi)
    statsRoiFilter.UseHistogramsOn()
    statsRoiFilter.Update()
    statsRoiFilter.SetHistogramParameters(bins, statsRoiFilter.GetMinimum(label), statsRoiFilter.GetMaximum(label))
    statsRoiFilter.Update()
    histogramRoi = statsRoiFilter.GetHistogram(label)
    volumePercentage = [0]
    doseValues = []
    for i in range(bins):
        volumePercentage.append(volumePercentage[-1] + histogramRoi.GetFrequency(bins-1-i))
        doseValues.append(histogramRoi.GetMeasurement(bins-1-i, 0))
    volumePercentage = np.array(volumePercentage[1:])/histogramRoi.GetTotalFrequency()*100
    volumePercentage = volumePercentage[::-1]
    doseValues = doseValues[::-1]

    if useCm3:
        volumeRoi = statsRoiFilter.GetCount(label)*dose.GetSpacing()[0]*dose.GetSpacing()[1]*dose.GetSpacing()[2]
        volumePercentage = volumePercentage*volumeRoi/100.0

    return (doseValues, volumePercentage)

def computeD(doseValues, volumePercentage, D):
    volumePercentage = np.flip(volumePercentage)
    doseValues = np.flip(doseValues)
    #Remove multiple values:
    indexToRemove = []
    for index in range(1, len(volumePercentage)):
        if volumePercentage[index] == volumePercentage[index-1]:
            indexToRemove += [index-1]
    volumePercentage = np.delete(volumePercentage, indexToRemove)
    doseValues = np.delete(doseValues, indexToRemove)

    doseInterpolated = scipy.interpolate.interp1d(volumePercentage, doseValues, kind='cubic', assume_sorted=False)
    return(doseInterpolated(D))

def computeV(doseValues, volumePercentage, V):
    volumeInterpolated = scipy.interpolate.interp1d(doseValues, volumePercentage, kind='cubic')
    return(volumeInterpolated(V))


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
        filenameStruct = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtstruct.dcm?inline=false", out=tmpdirpath, bar=None)
        structset = pydicom.read_file(os.path.join(tmpdirpath, filenameStruct))
        filenameDose = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtdose.dcm?inline=false", out=tmpdirpath, bar=None)
        doseImage = gt.read_3d_dicom([os.path.join(tmpdirpath, filenameDose)])
        transformImage = gt.applyTransformation(input=doseImage, neworigin=[-176, -320, -235])

        aroi = gt.region_of_interest(structset, "PTV")
        mask = aroi.get_mask(transformImage, corrected=False)
        doseValues, volumePercentage = createDVH(transformImage, mask, bins=100)
        self.assertTrue(np.allclose(doseValues, np.array([0.10095047205686569, 0.3028514161705971, 0.5047523528337479, 0.7066532969474792, 0.9085542261600494, 1.1104551553726196, 1.3123561143875122, 1.5142570734024048, 1.7161580324172974, 1.9180589318275452, 2.119959831237793, 2.3218607902526855, 2.523761749267578, 2.7256627082824707, 2.9275636672973633, 3.129464626312256, 3.3313655853271484, 3.533266544342041, 3.7351675033569336, 3.9370683431625366, 4.13896918296814, 4.340870141983032, 4.542771100997925, 4.744672060012817, 4.94657301902771, 5.1484739780426025, 5.350374937057495, 5.552275896072388, 5.75417685508728, 5.956077814102173, 6.157978773117065, 6.359879732131958, 6.561780691146851, 6.763681650161743, 6.965582609176636, 7.167483568191528, 7.369384527206421, 7.5712854862213135, 7.773186445236206, 7.9750871658325195, 8.176988124847412, 8.378889083862305, 8.580790042877197, 8.78269100189209, 8.984591960906982, 9.186492919921875, 9.388393878936768, 9.59029483795166, 9.792195796966553, 9.994096755981445, 10.195997714996338, 10.39789867401123, 10.599799633026123, 10.801700592041016, 11.003601551055908, 11.2055025100708, 11.407403469085693, 11.609304428100586, 11.811205387115479, 12.013106346130371, 12.215007305145264, 12.416908264160156, 12.618809223175049, 12.820710182189941, 13.022610664367676, 13.224511623382568, 13.426412582397461, 13.628313541412354, 13.830214500427246, 14.032115459442139, 14.234016418457031, 14.435917377471924, 14.637818336486816, 14.839719295501709, 15.041620254516602, 15.243521213531494, 15.445422172546387, 15.64732313156128, 15.849224090576172, 16.051124572753906, 16.253026008605957, 16.454927444458008, 16.656827926635742, 16.858728408813477, 17.060629844665527, 17.262531280517578, 17.464431762695312, 17.666332244873047, 17.868233680725098, 18.07013511657715, 18.272035598754883, 18.473936080932617, 18.675837516784668, 18.87773895263672, 19.079639434814453, 19.281539916992188, 19.483440399169922, 19.685341835021973, 19.887243270874023, 20.089143753051758])))
        self.assertTrue(np.all(volumePercentage >= 0))
        self.assertTrue(np.all(volumePercentage <= 100))
        self.assertTrue(len(doseValues) == 100)
        self.assertTrue(len(volumePercentage) == 100)
        shutil.rmtree(tmpdirpath)

    def test_dvh_volume(self):
        logger.info('Test_DVH test_dvh_volume')
        tmpdirpath = tempfile.mkdtemp()
        filenameStruct = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtstruct.dcm?inline=false", out=tmpdirpath, bar=None)
        structset = pydicom.read_file(os.path.join(tmpdirpath, filenameStruct))
        filenameDose = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtdose.dcm?inline=false", out=tmpdirpath, bar=None)
        doseImage = gt.read_3d_dicom([os.path.join(tmpdirpath, filenameDose)])
        transformImage = gt.applyTransformation(input=doseImage, neworigin=[-176, -320, -235])

        aroi = gt.region_of_interest(structset, "PTV")
        mask = aroi.get_mask(transformImage, corrected=False)
        doseValues, volumePercentage = createDVH(transformImage, mask, bins=100, useCm3=True)
        self.assertTrue(np.all(volumePercentage >= 0))
        self.assertTrue(np.all(volumePercentage <= 115120))
        self.assertTrue(len(doseValues) == 100)
        self.assertTrue(len(volumePercentage) == 100)
        shutil.rmtree(tmpdirpath)

    def test_dvh_compute_v(self):
        logger.info('Test_DVH test_dvh_compute_v')
        tmpdirpath = tempfile.mkdtemp()
        filenameStruct = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtstruct.dcm?inline=false", out=tmpdirpath, bar=None)
        structset = pydicom.read_file(os.path.join(tmpdirpath, filenameStruct))
        filenameDose = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtdose.dcm?inline=false", out=tmpdirpath, bar=None)
        doseImage = gt.read_3d_dicom([os.path.join(tmpdirpath, filenameDose)])
        transformImage = gt.applyTransformation(input=doseImage, neworigin=[-176, -320, -235])

        aroi = gt.region_of_interest(structset, "PTV")
        mask = aroi.get_mask(transformImage, corrected=False)
        doseValues, volumePercentage = createDVH(transformImage, mask)
        self.assertTrue(np.isclose(computeV(doseValues, volumePercentage, 10), 75.33129165068235))
        shutil.rmtree(tmpdirpath)

    def test_dvh_compute_d(self):
        logger.info('Test_DVH test_dvh_compute_d')
        tmpdirpath = tempfile.mkdtemp()
        filenameStruct = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtstruct.dcm?inline=false", out=tmpdirpath, bar=None)
        structset = pydicom.read_file(os.path.join(tmpdirpath, filenameStruct))
        filenameDose = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtdose.dcm?inline=false", out=tmpdirpath, bar=None)
        doseImage = gt.read_3d_dicom([os.path.join(tmpdirpath, filenameDose)])
        transformImage = gt.applyTransformation(input=doseImage, neworigin=[-176, -320, -235])

        aroi = gt.region_of_interest(structset, "PTV")
        mask = aroi.get_mask(transformImage, corrected=False)
        doseValues, volumePercentage = createDVH(transformImage, mask)
        self.assertTrue(np.isclose(computeD(doseValues, volumePercentage, 95), 0.15428162737918327))
        shutil.rmtree(tmpdirpath)

