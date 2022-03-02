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
import logging
#import rt_utils
logger=logging.getLogger(__name__)

def image_to_dicom_rt_struct(dicom, mask, name, rtstruct):

    #Read dicom input
    series = gt.separate_series(dicom)
    if len(series.keys()) != 1:
        logger.error('The number of dicom serie detected is not 1')
        return
    seriesInstanceUID = list(series.keys())[0]
    if len(series[seriesInstanceUID]) > 1:
        dicomImage = gt.read_dicom(series[seriesInstanceUID])
    elif len(series[seriesInstanceUID]) == 1 and series[seriesInstanceUID][0].endswith(".dcm"):
        dicomImage = gt.read_3d_dicom(series[seriesInstanceUID])
    else:
        logger.error('no input available')
        return
    dicomFolder = os.path.dirname(dicom[0])

    #Check if mask and dicomImage have the same spacing, size, offset
    #If not, resample like the dicom
    resize = False
    if not np.array_equal(mask.GetSpacing(), dicomImage.GetSpacing()):
        resize = True
    if not np.array_equal(mask.GetOrigin(), dicomImage.GetOrigin()):
        resize = True
    if not np.array_equal(mask.GetLargestPossibleRegion().GetSize(), dicomImage.GetLargestPossibleRegion().GetSize()):
        resize = True
    if resize:
        mask = gt.applyTransformation(input=mask, like=dicomImage, force_resample=True, pad=0, interpolation_mode="NN")

    rtstruct = rt_utils.RTStructBuilder.create_from(
      dicom_series_path=dicomFolder, 
      rt_struct_path=rtstruct
    )

    print(mask.GetLargestPossibleRegion().GetSize())
    print(dicomImage.GetLargestPossibleRegion().GetSize())
    segArray = itk.array_from_image(mask)
    segArray = segArray.astype(np.bool)
    segArray = np.swapaxes(segArray,0,2)
    segArray = np.swapaxes(segArray,0,1)

    rtstruct.add_roi(
      mask=segArray, 
      color=[255, 0, 255], 
      name=name,
      approximate_contours=False
    )

    print(rtstruct)
    return (rtstruct)

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
from .logging_conf import LoggedTestCase

#class Test_image2DicomRTStruct(LoggedTestCase):
#    def test_image2DicomRTStruct(self):
#        logger.info('Test_image2DicomRTStruct test_image2DicomRTStruct')
#        tmpdirpath = tempfile.mkdtemp()
#        print(tmpdirpath)
#        filenameStruct = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtstruct.dcm?inline=false", out=tmpdirpath, bar=None)
#        filenameDose = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/rtdose.dcm?inline=false", out=tmpdirpath, bar=None)
#        doseImage = gt.read_3d_dicom([os.path.join(tmpdirpath, filenameDose)])
#        
#        #Create mask:
#        array = np.zeros(itk.array_from_image(doseImage).shape)
#        array[20:30, 41:48, 25:51] = 1.0
#        mask = itk.image_from_array(array)
#        mask.SetOrigin(doseImage.GetOrigin())
#        mask.SetSpacing(doseImage.GetSpacing())
#
#        rtstruct = image_to_dicom_rt_struct([os.path.join(tmpdirpath, filenameDose)], mask, os.path.join(tmpdirpath, filenameStruct))
#        rtstruct.save(os.path.join(tmpdirpath, "rtstruct2"))
#        with open(os.path.join(tmpdirpath, "rtstruct.dcm"),"rb") as fnew:
#            bytesNew = fnew.read()
#            new_hash = hashlib.sha256(bytesNew).hexdigest()
#            print(new_hash)
#            self.assertTrue("87c7eee6e29172289407e2739c2618418a38718c09e94ebee9a390a73433d236" == new_hash)
#        shutil.rmtree(tmpdirpath)

