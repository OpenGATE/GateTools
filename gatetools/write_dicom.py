# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides a tool to convert image to dicom
"""

import os
import itk
import numpy as np
import pydicom
from datetime import datetime
import copy
import logging
logger=logging.getLogger(__name__)

def insertTag(dataset, tag, value, type):
    if tag in dataset:
        dataset[tag].value = value
    else:
        dataset[tag] = pydicom.DataElement(tag, type, value)


def convertTagValue(value, VRtype):
    if VRtype in ["AE", "AS" , "AT", "CS", "DA", "DS", "DT", "IS", "LO", "LT", "OB", "OD", "OF", "OW", "PN", "SH", "ST", "TM", "UI", "UN", "UT"]:
        return str(value)
    elif VRtype in ["SL", "SS", "UL", "US"]:
        return int(value)
    elif VRtype in ["FL", "FD"]:
        return float(value)


def writeDicom(input, dicom=None, output="output.dcm", newseriesuid=False, newstudyuid=False, tags=()):

    # Scale the input:
    inputArray = itk.array_from_image(input)
    max = np.amax(inputArray)
    min = np.amin(inputArray)
    scaling = (max - min)/(2**16-1)
    intercept = min
    inputArray = (inputArray - intercept)/scaling
    inputArray = (inputArray).astype(np.uint16)
    inputImageChar = itk.image_from_array(inputArray)

    #Write the input as a new dicom
    imageIO = itk.GDCMImageIO.New()
    writer = itk.ImageSeriesWriter.New(Input=inputImageChar, ImageIO=imageIO)
    writer.SetFileNames([output])
    writer.Update()

    #Open the new dicom and change some dicom tags according dicom input or not
    dsImage = pydicom.dcmread(output)
    if dicom is not None:
        dsDicom = pydicom.dcmread(dicom)
        dsOutput = copy.deepcopy(dsDicom)
    else:
        dsOutput = copy.deepcopy(dsImage)

    now = datetime.now()
    insertTag(dsOutput, 0x00080023, now.strftime("%Y%m%d"), 'DA') #Content Date
    insertTag(dsOutput, 0x00080033, now.strftime("%H%M%S") + ".000000", 'TM') #Content Time
    insertTag(dsOutput, 0x00080060, "OT", 'CS') #Modality
    ss = 1.0
    sp = []
    for i in range(2):
        sp += [input.GetSpacing()[1-i]]
    if input.GetImageDimension() == 3:
        ss = input.GetSpacing()[2]
    insertTag(dsOutput, 0x00180050, ss, 'DS') #Slice Thickness
    insertTag(dsOutput, 0x00180088, ss, 'DS') #Spacing Between Slices
    insertTag(dsOutput, 0x00181020, "gatetools", 'LO') #Software Version(s)
    insertTag(dsOutput, 0x00181030, "", 'LO') #Protocol Name
    insertTag(dsOutput, 0x00201041, 0, 'DS') #Slice Location
    origin = []
    for i in input.GetOrigin():
        origin += [i]
    insertTag(dsOutput, 0x00200032, origin, 'DS') #Image Position (Patient)
    orientation = []
    for i in range(2):
        for j in range(input.GetImageDimension()):
            orientation += [input.GetDirection()(i, j)]
    insertTag(dsOutput, 0x00200037, orientation, 'DS') #Image Orientation (Patient)
    insertTag(dsOutput, 0x00280030, sp, 'DS') #Pixel Spacing
    insertTag(dsOutput, 0x00281006, 0, 'US') #Smallest Image Pixel Value
    insertTag(dsOutput, 0x00281007, 65535, 'US') #Largest Image Pixel Value
    insertTag(dsOutput, 0x00281050, (max + min)/2.0, 'DS') #Window Center
    insertTag(dsOutput, 0x00281051, max - min, 'DS') #Window Width
    insertTag(dsOutput, 0x00281052, intercept, 'DS') #Rescale Intercept
    insertTag(dsOutput, 0x00281053, scaling, 'DS') #Rescale Slope
    insertTag(dsOutput, 0x00281055, "auto", 'LO') #Window Center & Width Explanation
    if input.GetImageDimension() == 3:
        frameOffsetVector = [x * ss for x in range(0, input.GetLargestPossibleRegion().GetSize()[2])]
        insertTag(dsOutput, 0x3004000c, frameOffsetVector, 'DS') #Grid Frame Offset Vector

    if dicom is not None:
        dsOutput.PixelData = dsImage.PixelData
        insertTag(dsOutput.file_meta, 0x00020013, dsImage.file_meta[0x0002,0x0013].value, 'SH') #Implementation Version Name
        insertTag(dsOutput.file_meta, 0x00020016, dsImage.file_meta[0x0002,0x0016].value, 'AE') #Implementation Version Name
        insertTag(dsOutput, 0x00280008, dsImage[0x0028,0x0008].value, 'IS') #NumberOfFrames
        insertTag(dsOutput, 0x00280009, dsImage[0x0028,0x0009].value, 'AT') #Frame Increment Pointer
        insertTag(dsOutput, 0x00280010, dsImage[0x0028,0x0010].value, 'US') #Rows
        insertTag(dsOutput, 0x00280011, dsImage[0x0028,0x0011].value, 'US') #Columns
        insertTag(dsOutput, 0x00280100, dsImage[0x0028,0x0100].value, 'US') #Bits Allocated
        insertTag(dsOutput, 0x00280101, dsImage[0x0028,0x0101].value, 'US') #Bits Stored
        insertTag(dsOutput, 0x00280102, dsImage[0x0028,0x0102].value, 'US') #High Bit
        insertTag(dsOutput, 0x00280103, dsImage[0x0028,0x0103].value, 'US') #Pixel Representation
        insertTag(dsOutput, 0x00281054, dsImage[0x0028,0x1054].value, 'LO') #Rescale Type
        #insertTag(dsOutput, 0x52009229, dsImage[0x5200,0x9229].value, 'SQ') #Shared Functional Groups Sequence
        insertTag(dsOutput, 0x52009230, dsImage[0x5200,0x9230].value, 'SQ') #Per-frame Functional Groups Sequence

        if newstudyuid:
            newStudyInstanceUID = pydicom.uid.generate_uid()
            insertTag(dsOutput, 0x0020000d, newStudyInstanceUID, 'UI') #Study Instance UID
            insertTag(dsOutput, 0x00200052, dsImage[0x0020,0x0052].value, 'UI') #Frame of Reference UID
            newseriesuid = True
        if newseriesuid:
            newSeriesInstanceUID = pydicom.uid.generate_uid()
            insertTag(dsOutput, 0x0020000e, newSeriesInstanceUID, 'UI') #Series Instance UID

    # Change tag from command line:
    for tag in tags:
        try:
            VRtype = pydicom.datadict.dictionary_VR(tag[0])
        except:
            print("The tag " + tag[0] + " is not know in public pydicom dictionary")
            continue
        try:
            value = convertTagValue(tag[1], VRtype)
        except:
            print("Cannot find the correct type for " + tag[0] + " with value " + tag[1] + " and VR " + VRtype)
            continue
        insertTag(dsOutput, tag[0], value, VRtype)

    dsOutput.save_as(output)



#####################################################################################
import unittest
import sys
import tempfile
import hashlib
import shutil
import wget
import gatetools as gt
from .logging_conf import LoggedTestCase

def createImageExample():
    x = np.arange(-10, 10, 1)
    y = np.arange(-12, 15, 1)
    z = np.arange(-13, 10, 1)
    xx, yy, zz = np.meshgrid(x, y, z)
    image = itk.image_from_array(np.int16(xx))
    image.SetOrigin([7, 3.4, -4.6])
    image.SetSpacing([4, 2, 3.6])
    return image

class Test_Write_Dicom(LoggedTestCase):
    def test_write_dicom(self):
        logger.info('Test_Write_Dicom test_write_dicom')
        image = createImageExample()
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(image, os.path.join(tmpdirpath, "input.mhd"))
        filenameDcm = wget.download("https://github.com/OpenGATE/GateTools/raw/master/dataTest/rtdose.dcm", out=tmpdirpath, bar=None)
        writeDicom(image, dicom = os.path.join(tmpdirpath, filenameDcm), output = os.path.join(tmpdirpath, "output.dcm"))
        convertedDicom = gt.read_3d_dicom([os.path.join(tmpdirpath, "output.dcm")])
        itk.imwrite(convertedDicom, os.path.join(tmpdirpath, "output.mhd"))
        with open(os.path.join(tmpdirpath, "output.mhd"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("65fc74e082eb4a69b60c289435564488956ba73bb274637fe0969c2152176308" == new_hash)
        shutil.rmtree(tmpdirpath)
