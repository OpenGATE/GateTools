# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module contains a function named `dicom_rt_pbs_plan_to_gate_conversion`,
which can be used to convert DICOM radiotherapy plan files for pencil beam
scanning to the text format that Gate uses to read in the spot specifications.
"""

import numpy as np
import logging
logger=logging.getLogger(__name__)

def dicom_rt_pbs_plan_to_gate_conversion(dcm_input,txt_output,allow0=False,verbose=False):
    """
    Function to create GATE plan description corresponding to DICOM plan file.

    * :param dcm_input: string with the file path of the input DICOM plan file
    * :param txt_output: string with the file path of the output Gate PBS spot specification text file (suffix .txt or .dat)
    """
    planname = _check_output_filename(txt_output,verbose)
    nspots_written = 0
    nlayers_written = 0
    nspots_ignored = 0
    nlayers_ignored = 0
    rp,mswtots,beamnrs,iso_Cs,g_angles,p_angles = _read_and_check_dicom_plan_file(dcm_input,verbose)
    filehandle=open(txt_output,"w")
    # FILE HEADER
    filehandle.write(_file_header.format(name=planname,nfields=len(rp.IonBeamSequence)))
    for beamnr in beamnrs:
        filehandle.write("###FieldsID\n{}\n".format(beamnr))
    filehandle.write("#TotalMetersetWeightOfAllFields\n{0:f}\n\n".format(sum(mswtots)))
    # stupidity check...
    assert(len(rp.IonBeamSequence)== len(beamnrs))
    assert(len(rp.IonBeamSequence)== len(mswtots))
    assert(len(rp.IonBeamSequence)== len(iso_Cs))
    assert(len(rp.IonBeamSequence)== len(g_angles))
    assert(len(rp.IonBeamSequence)== len(p_angles))
    for ion_beam,beamnr,mswtot,iso_C,g_angle,p_angle in zip(rp.IonBeamSequence,
                                                           beamnrs,
                                                           mswtots,
                                                           iso_Cs,
                                                           g_angles,
                                                           p_angles):
        nspots_list=list()
        mask_list=list()
        weights_list=list()
        for icp in ion_beam.IonControlPointSequence:
            nspots_nominal = int(icp.NumberOfScanSpotPositions)
            if nspots_nominal == 1:
                w_all = np.array([float(icp.ScanSpotMetersetWeights)])
            else:
                w_all = np.array([float(w) for w in icp.ScanSpotMetersetWeights])
            mask = (w_all>=0.) if allow0 else (w_all>0.)
            nspots_list.append(np.sum(mask))
            mask_list.append(mask)
            weights_list.append(w_all)

        filehandle.write(_beam_header.format(fid=beamnr,
                                             mswtot=mswtot,
                                             g_angle=g_angle,
                                             p_angle=p_angle,
                                             isox=iso_C[0],
                                             isoy=iso_C[1],
                                             isoz=iso_C[2],
                                             ncp=np.sum(np.array(nspots_list)>0)))
        msw_cumsum = 0.
        cpi=0
        for icp,nspots,mask,w_all in zip(ion_beam.IonControlPointSequence,nspots_list,mask_list,weights_list):
            nspots_nominal = int(icp.NumberOfScanSpotPositions)
            if nspots == 0:
                if allow0:
                    logger.warning("this should not happen, nspots_nominal={}",format(nspots_nominal))
                nlayers_ignored += 1
                nspots_ignored += nspots_nominal
                continue
            xy = np.array([float(pos) for pos in icp.ScanSpotPositionMap]).reshape(nspots_nominal,2)
            nspots_ignored += nspots_nominal-nspots
            w=w_all[mask]
            x=xy[mask,0]
            y=xy[mask,1]
            msw=np.sum(w_all[mask])
            energy = float(icp.NominalBeamEnergy)
            # Maybe we should emit noisy warnings if the tune ID is missing?
            tuneID = "0.0" if not "ScanSpotTuneID" in icp else str(icp.ScanSpotTuneID)
            # TODO: what if all spot weights in this ICP are zero?
            filehandle.write(_layer_header.format(cpi=cpi,stid=tuneID,mswtot=msw_cumsum,energy=energy,nspots=nspots))
            for spotx,spoty,spotw in zip(x,y,w):
                filehandle.write("{0:g} {1:g} {2:g}\n".format(spotx,spoty,spotw))
            nspots_written += nspots
            nlayers_written += 1
            msw_cumsum+=msw
            cpi+=1
    filehandle.close()
    if verbose:
        logger.info("Converted DICOM file {} to Gate PBS spot specification text file {}".format(dcm_input,txt_output))
        logger.info("# beams = {}".format(len(rp.IonBeamSequence)))
        logger.info("# control points written = {}".format(nlayers_written))
        logger.info("# spots written = {}".format(nspots_written))
        if not allow0:
            # number of beams ignored, because msw<=0 for all spots? :-)
            logger.info("# control points ignored (because msw<=0 for all spots) = {}".format(nlayers_ignored))
            logger.info("# spots ignored (because msw<=0) = {}".format(nspots_ignored))

###############################################################################
# IMPLEMENTATION DETAILS                                                      #
###############################################################################

import os, re
import pydicom

def _check_rp_dicom_file(rp_filepath,verbose=False):
    """
    Auxiliary implementation function.

    Try to read the DICOM file and perform some paranoid check of the essential DICOM attributes.
    """
    # if the input file path is not readable as a DICOM file, then pydicom will throw an appropriate exception
    rp = pydicom.dcmread(rp_filepath)
    for attr in [ 'SOPClassUID', "IonBeamSequence" ] :
        if attr not in rp:
            raise IOError("bad DICOM file {},\nmissing '{}'".format(rp_filepath,attr))
    if rp.SOPClassUID.name != 'RT Ion Plan Storage':
        raise IOError("bad plan file {},\nwrong SOPClassUID: {}='{}',\nexpecting an 'RT Ion Plan Storage' file instead.".format(rp_filepath,rp.SOPClassUID,rp.SOPClassUID.name))
    n_ion_beams=len(rp.IonBeamSequence)
    ion_beams=rp.IonBeamSequence
    for ion_beam in ion_beams:
        for attr in [ 'BeamNumber', "IonControlPointSequence"]:
            if attr not in ion_beam:
                raise IOError("bad DICOM file {},\nmissing '{}' in ion beam".format(rp_filepath,attr))
        for cpi,icp in enumerate(ion_beam.IonControlPointSequence):
            for attr in [ 'NumberOfScanSpotPositions', "ScanSpotPositionMap", "ScanSpotMetersetWeights"]:
                if attr not in icp:
                    raise IOError("bad DICOM file {},\nmissing '{}' in {}th ion control point".format(rp_filepath,attr,cpi))
    if verbose:
        logger.info("Input DICOM file seems to be a legit 'RT Ion Plan Storage' file.")
    return rp

def _get_beam_numbers(rp,verbose=False):
    """
    Auxiliary implementation function.

    Extract beam numbers from the DICOM plan dataset, and create better ones in
    case the stored ones are useless for some reason.

    Most treatment planning systems will assign a non-negative unique beam
    number to each ion beam, but some TPS (ones used to generate artificial
    plans for testing and commissioning purposes) are negligent in that regard.
    Since Gate needs the beam numbers in order to allow the user to select
    which beams to simulate (or conversely, which beams to ignore), this script
    will create fake but usable beam numbers in such cases.
    """
    number_list = list()
    input_beam_numbers_are_ok = True
    n_ion_beams=len(rp.IonBeamSequence)
    for ion_beam in rp.IonBeamSequence:
        if input_beam_numbers_are_ok:
            nr = int(ion_beam.BeamNumber)
            if nr < 0:
                input_beam_numbers_are_ok = False
                if verbose:
                    logger.info("CORRUPT INPUT: found a negative beam number {}.".format(nr))
            elif nr in number_list:
                input_beam_numbers_are_ok = False
                if verbose:
                    logger.info("CORRUPT INPUT: found same beam number {} for multiple beams.".format(nr))
            else:
                # still good, keep fingers crossed...
                number_list.append(nr)
    if not input_beam_numbers_are_ok:
        if verbose:
            logger.warning("will use simple enumeration of beams instead of the (apparently corrupt) dicom beam numbers.")
        number_list = np.arange(1,n_ion_beams+1).tolist()
    return number_list

def _get_mswtot_list(rp,verbose=False):
    """
    Auxiliary implementation function.

    Retrieve the total weight of all spots for one "control point" (or "layer",
    or "energy").  TODO: it could be useful to enable a conversion function
    here, e.g. to convert from "monitor units" to "number of protons". However,
    this can also be taken care of in Gate itself, via the beam calibration
    polynomial in the "source properties file".
    """
    mswtot_list = list()
    for ion_beam in rp.IonBeamSequence:
        mswtot=0.
        for icp in ion_beam.IonControlPointSequence:
            nspot =int(icp.NumberOfScanSpotPositions)
            if nspot == 1:
                mswtot += float(icp.ScanSpotMetersetWeights)
            else:
                # Weights should be non-negative, but let's be paranoid.
                mswtot += np.sum(np.array([float(w) for w in icp.ScanSpotMetersetWeights if w>0.]))
        mswtot_list.append(mswtot)
    return mswtot_list

def _get_angles_and_isoCs(rp,verbose):
    """
    Auxiliary implementation function.

    For each beam, retrieve the gantry angle, patient support angle and
    isocenter, if available.  (Most TPS will of course specify this info, but
    some medical physicists use an in-house TPS for generating special plans
    for beam verification and commissioning, with incomplete planning
    information.) For some unclear reasons, the angles and isocenter
    coordinates are not stored as attributes of the ion beam, but rather as
    attributes to the first "ion control point".
    """
    gantry_angle_list = list()
    patient_angle_list = list()
    iso_center_list = list()
    n_ion_beams=len(rp.IonBeamSequence)
    dubious = False
    for i,ion_beam in enumerate(rp.IonBeamSequence):
        # each of these quantities may be missing
        beamname = str(i) if not hasattr(ion_beam,"BeamName") else str(ion_beam.BeamName)
        icp0 = ion_beam.IonControlPointSequence[0]
        # check isocenter
        if "IsocenterPosition" in icp0 and icp0.IsocenterPosition is not None:
            if len(icp0.IsocenterPosition)==3:
                iso_center_list.append(np.array([float(icp0.IsocenterPosition[j]) for j in range(3)]))
        else:
            logger.warning("absent/corrupted isocenter for beam '{}'; assuming [0,0,0] for now, please fix this manually.".format(beamname))
            iso_center_list.append(np.zeros(3,dtype=float))
            dubious = True
        # check gantry angle
        if "GantryAngle" in icp0 and icp0.GantryAngle is not None:
            gantry_angle_list.append(float(icp0.GantryAngle))
        else:
            logger.warning("no gantry angle specified for beam '{}' in treatment plan; assuming 0. for now, please fix this manually.".format(beamname))
            gantry_angle_list.append(0.)
            dubious = True
        # check couch angle
        if "PatientSupportAngle" in icp0 and icp0.PatientSupportAngle is not None:
            patient_angle_list.append(float(icp0.PatientSupportAngle))
        else:
            logger.warning("no patient support angle specified for beam '{}' in treatment plan; assuming 0. for now, please fix this manually.".format(beamname))
            patient_angle_list.append(0.)
            dubious = True
    if verbose and not dubious:
         logger.info("patient/gantry angles and isocenters all seem fine.")
    return gantry_angle_list, patient_angle_list, iso_center_list

def _read_and_check_dicom_plan_file(rp_filepath,verbose=False):
    """
    Auxiliary implementation function.

    The existence of a DICOM 'standard' does not mean that all 'DICOM plan
    files' look alike, unfortunately; every TPS has its own dialect, and some medical
    physicists use their own hobby TPS to create "DICOM plan files" that are lacking
    the most basic ingredients. We need to check our assumptions based on the
    TPS plan files that we have had access to, and define workarounds for the
    problematic "plan files".
    """
    # Crude checks of DICOM file structure.
    rp = _check_rp_dicom_file(rp_filepath,verbose)
    # Get mswtot of each beam.
    mswtot_list = _get_mswtot_list(rp,verbose)
    # Get 'number' of each beam.
    # (Name would more more useful, but Gate uses the number in its interface for "allowing" and "disallowing" beams ("fields").)
    number_list = _get_beam_numbers(rp,verbose)
    # Get the things that *should* be attributes of an "ion beam" object but which are buried in "control point number 0".
    gantry_angles,patient_angles,isoCs = _get_angles_and_isoCs(rp,verbose)

    return rp, mswtot_list, number_list, isoCs, gantry_angles, patient_angles

def _check_output_filename(txt_output,verbose):
    """
    Let's assume that the user chose an informative name for the spot file,
    and use that for the plan name. Gate does not actually use that name,
    so it's not so important. But it *is* important to make sure that it is
    a single word (without spaces or other non-alphanumerical characters).
    """
    if txt_output[-4:].lower() != ".txt" and txt_output[-4:].lower() != ".dat":
        raise IOError("Output file name should have a '.txt' or '.dat' suffix.")
    base_txt_output = os.path.basename(txt_output)
    if len(base_txt_output)<5:
        raise IOError("Output file name should have at least one charachter before the txt/dat suffix.")
    if os.path.exists(txt_output) and verbose:
        logger.warning("going to overwrite existing file {}".format(txt_output))
    badchars=re.compile("[^a-zA-Z0-9_]")
    planname = re.sub(badchars,"_",base_txt_output[:-4])
    if verbose:
        logger.info("using plan name '{}'".format(planname))
    return planname



_file_header="""#TREATMENT-PLAN-DESCRIPTION
#PlanName
{name:s}
#NumberOfFractions
1
##FractionID
1
##NumberOfFields
{nfields:d}
"""

_beam_header="""#FIELD-DESCRIPTION
###FieldID
{fid}
###FinalCumulativeMeterSetWeight
{mswtot:g}
###GantryAngle (in degrees)
{g_angle:g}
###PatientSupportAngle
{p_angle}
###IsocenterPosition
{isox:g} {isoy:g} {isoz:g}
###NumberOfControlPoints
{ncp:d}
#SPOTS-DESCRIPTION
"""

_layer_header="""####ControlPointIndex
{cpi:d}
####SpotTuneID
{stid:s}
####CumulativeMetersetWeight
{mswtot:g}
####Energy (MeV)
{energy:g}
####NbOfScannedSpots
{nspots:g}
####X Y Weight (spot position at isocenter in mm, with weight in MU (default) or number of protons "setSpotIntensityAsNbProtons true")
"""

################################################################################
# UNIT TESTS                                                                   #
################################################################################

import unittest
import sys
import datetime

class _tmp_test_plan_writer:
    def __init__(self,fname,spotspecs=None,uid=None,verbose=False):
        """
        Create a fake treatment plan DICOM file for unit testing.  The spot
        specs are a list of dictionaries, one dictionary per beam.  Each beam
        dictionary contains optional entries for gantry angle, patient support
        angle and isocenter position and an obligatory list of "controlpoints".

        A file with filename `fname` should not yet exist. A DICOM file with
        name `fname` will be written by _test_plan_creator, and also be deleted
        when the creator goes out of scope.
        """
        assert(sys.version_info.major == 3)
        self.verbose=verbose
        assert(not os.path.exists(fname))
        self.dcm_filename=fname
        classUID='1.2.840.10008.5.1.4.1.1.481.8' if uid is None else uid
        instanceUID=pydicom.uid.generate_uid()

        # File meta info data elements
        file_meta = pydicom.Dataset()
        file_meta.MediaStorageSOPClassUID = str(classUID)
        file_meta.MediaStorageSOPInstanceUID = str(instanceUID)
        file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
        #FIXME: we probably need to apply for an official UID here
        file_meta.ImplementationClassUID = '1.2.826.0.1.3680043.1.2.100.6.40.0.76'
        file_meta.ImplementationVersionName = 'DicomObjects.NET'

        self.ds=pydicom.FileDataset(self.dcm_filename,{},file_meta=file_meta,preamble=b"\0"*128)
        self.ds.SOPClassUID=classUID
        self.ds.SOPInstanceUID=instanceUID
        self.ds.PatientName="unit test"
        self.ds.PatientID="42"
        #print("trying to fix 'is_little_endian'")

        if spotspecs:
            self.ds.IonBeamSequence=pydicom.Sequence()
            self.ds.NumberOfBeams = len(spotspecs)
            for beamdata in spotspecs:
                beam=pydicom.Dataset()
                beam.BeamName = beamdata.get('Nm','noname')
                beam.BeamNumber = beamdata.get('Nr',-1)
                beam.NumberOfIonControlPoints=len(beamdata["controlpoints"])
                beam.IonControlPointSequence=pydicom.Sequence()
                for i,icpdata in enumerate(beamdata["controlpoints"]):
                   icp=pydicom.Dataset()
                   if i==0:
                       if 'G' in beamdata:
                           icp.GantryAngle = beamdata['G']
                       if 'P' in beamdata:
                           icp.PatientSupportAngle = beamdata['P']
                       if "I" in beamdata:
                           icp.IsocenterPosition = list([str(v) for v in beamdata.get('I')])
                       else:
                           icp.IsocenterPosition = ""
                   icp.NominalBeamEnergy = icpdata.get('E',100.)
                   if 'T' in icpdata:
                       icp.ScanSpotTuneID = icpdata['T']
                   #unfortunately, this does not work
                   icp.ScanSpotMetersetWeights = [float(v) for v in icpdata['SSW']]
                   icp.ScanSpotPositionMap = [float(v) for v in np.array(icpdata['SSP']).flatten()]
                   icp.NumberOfScanSpotPositions = int(icpdata.get('NSSP',len(icp.ScanSpotPositionMap)/2))
                   beam.IonControlPointSequence.append(icp)
                self.ds.IonBeamSequence.append(beam)
        else:
            self.ds.NumberOfBeams = 0
        if verbose:
            logger.info("number of beams is {}".format(self.ds.NumberOfBeams))
        dt = datetime.datetime.now()
        self.ds.ContentDate = dt.strftime('%Y%m%d')
        timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
        self.ds.ContentTime = timeStr
        self.ds.is_little_endian = True
        self.ds.is_implicit_VR = True
        self.ds.fix_meta_info()
        self.ds.save_as(self.dcm_filename)
        if self.verbose:
            logger.info("wrote dicom file {}".format(self.dcm_filename))
    def __del__(self):
        os.remove(self.dcm_filename)
        if self.verbose:
            logger.info("deleted dicom file {}".format(self.dcm_filename))
        del self.ds

class test_small_normal_plan(unittest.TestCase):
    """
    Normal plan with three properly numbered beams and all data needed by Gate for a simulation.
    """
    def setUp(self):
        beam4 = dict(Nm="foo", Nr=4, G=45., P=225., I=(120.,130.,140.),
                     controlpoints=[dict(SSW=[0.42],E=100.,T="3.0",
                                         SSP=[(2.,1)])])
        beam5 = dict(Nm="bar", Nr=5, G=30., P=45., I=(100.,150.,-140.),
                     controlpoints=[dict(SSW=[0.,0.4,0.,0.6],E=100.,T="3.0",
                                         SSP=[(2.,1.),(2.,1),(3.,4.),(3.,4.)])])
        beam6 = dict(Nm="baz", Nr=6, G=60., P=30., I=(-10.,-150.,40.),
                     controlpoints=[dict(SSW=[0.4,0.6,0.8],E=70.,T="3.1",
                                         SSP=[(2.,1),(3.,4.),(6.,5.)]),
                                    dict(SSW=[0.4,0.5],E=120.,T="3.1",
                                         SSP=[(7.,8.),(3.,4.)])])
        self.testbeams = [beam4,beam5,beam6]
        # while debugging, set this to True
        self.verbose = False
        self.helper = _tmp_test_plan_writer("test.dcm",spotspecs=self.testbeams)
        #self.helper = _test_plan_creator("test.dcm",spotspecs=[beam0])
    def tearDown(self):
        del self.helper
    def test_dicom(self):
        """
        Self consistency check for test dicom file.
        """
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        self.assertEqual(3,len(test_rp.IonBeamSequence))
        self.assertEqual(4,int(test_rp.IonBeamSequence[0].BeamNumber))
        self.assertEqual(5,int(test_rp.IonBeamSequence[1].BeamNumber))
        self.assertEqual(6,int(test_rp.IonBeamSequence[2].BeamNumber))
        self.assertEqual("3.0",test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotTuneID)
        self.assertAlmostEqual(120.0,test_rp.IonBeamSequence[2].IonControlPointSequence[1].NominalBeamEnergy)
        self.assertAlmostEqual(0.42,test_rp.IonBeamSequence[0].IonControlPointSequence[0].ScanSpotMetersetWeights)
        self.assertAlmostEqual(0.0,test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotMetersetWeights[0])
        self.assertAlmostEqual(0.6,test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotMetersetWeights[3])
        self.assertAlmostEqual(0.4,test_rp.IonBeamSequence[2].IonControlPointSequence[1].ScanSpotMetersetWeights[0])
        self.assertAlmostEqual(45.,test_rp.IonBeamSequence[1].IonControlPointSequence[0].PatientSupportAngle)
        self.assertAlmostEqual(60.,test_rp.IonBeamSequence[2].IonControlPointSequence[0].GantryAngle)
    def test_mswtot(self):
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        mswtot_list = _get_mswtot_list(test_rp,self.verbose)
        self.assertEqual(3,len(mswtot_list))
        self.assertAlmostEqual(0.42,mswtot_list[0])
        self.assertAlmostEqual(1.0,mswtot_list[1])
        self.assertAlmostEqual(2.7,mswtot_list[2])
    def test_beam_numbers(self):
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        numbers = _get_beam_numbers(test_rp,self.verbose)
        self.assertEqual([4,5,6],numbers)
    def test_angles_and_iscoCs(self):
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        gantry_angles, patient_angles, iso_centers = _get_angles_and_isoCs(test_rp,self.verbose)
        nbeams=len(self.testbeams)
        self.assertEqual(len(gantry_angles),nbeams)
        self.assertEqual(len(patient_angles),nbeams)
        self.assertEqual(len(iso_centers),nbeams)
        for g,p,i,b in zip(gantry_angles, patient_angles, iso_centers, self.testbeams):
            self.assertAlmostEqual(g,b["G"])
            self.assertAlmostEqual(p,b["P"])
            self.assertEqual(3,len(i))
            for j in range(3):
                self.assertAlmostEqual(i[j],b["I"][j])
    def test_check_output_filename(self):
        with self.assertRaisesRegex(IOError,"suffix"):
            _check_output_filename("error.dcm",self.verbose)
        with self.assertRaisesRegex(IOError,"suffix"):
            _check_output_filename("also_error",self.verbose)
        with self.assertRaisesRegex(IOError,"at least one charachter"):
            _check_output_filename(".txT",self.verbose)
        self.assertEqual("abc",_check_output_filename("abc.txt",self.verbose))
        self.assertEqual("abc",_check_output_filename("/foo/bar/abc.txt",self.verbose))
        self.assertEqual("ab_c",_check_output_filename("ab.c.txt",self.verbose))
        self.assertEqual("_",_check_output_filename(" .txt",self.verbose))
        self.assertEqual("_Box_6__0__0__25___Rashi",_check_output_filename("_Box 6 (0, 0, 25) ^Rashi.txt",self.verbose))
    def test_the_whole_thing_already(self):
        dicom_rt_pbs_plan_to_gate_conversion("test.dcm","zero_tolerance.txt",allow0=True,verbose=self.verbose)
        dicom_rt_pbs_plan_to_gate_conversion("test.dcm","zero_nontolerance.txt",allow0=False,verbose=self.verbose)

class test_workarounds(unittest.TestCase):
    """
    Check that the workarounds for missing information are indeed working.
    """
    def setUp(self):
        self.testbeams = list()
        # now all beams have the same name and number
        # (I saw this in an actual treatment plan, not for a patient but used in commissioning / beam delivery verification.)
        self.testbeams.append(dict(Nm="foo", Nr=-1, # G=90., P=90., I=-1.,
                                   # let's remove the tune ID
                                   controlpoints=[dict(SSW=[0.42e9],E=100., # T="3.0",
                                                       SSP=[(2.,1)])]))
        self.testbeams.append(dict(Nm="foo", Nr=-1, #G=90., P=90., I=-1,
                                   # half of the spots have zero weight
                                   controlpoints=[dict(SSW=[0.,0.4e9,0.,0.6e9],E=110.,T="3.0",
                                                       SSP=[(2.,1.),(2.,1),(3.,4.),(3.,4.)])]))
        self.testbeams.append(dict(Nm="foo", Nr=-1, #G=90., P=90., I=-1,
                                   # All spots in first control point have zero weight
                                   # This actually happens in actual patient plans as well.
                                   controlpoints=[dict(SSW=[0.0,0.0,0.0],E=120.,T="3.1",
                                                       SSP=[(2.,1),(3.,4.),(6.,5.)]),
                                                  dict(SSW=[0.4e9,0.5e9,0.6e9],E=120.,T="3.1",
                                                       SSP=[(2.,1),(3.,4.),(6.,5.)])]))
        # while debugging, set this to True
        self.verbose = False
        self.helper = _tmp_test_plan_writer("test.dcm",spotspecs=self.testbeams)
        #self.helper = _test_plan_creator("test.dcm",spotspecs=[beam0])
    def tearDown(self):
        del self.helper
    def test_dicom(self):
        """
        Self consistency check for test dicom file.
        """
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        self.assertEqual( 3,len(test_rp.IonBeamSequence))
        self.assertEqual(-1,int(test_rp.IonBeamSequence[0].BeamNumber))
        self.assertEqual(-1,int(test_rp.IonBeamSequence[1].BeamNumber))
        self.assertEqual(-1,int(test_rp.IonBeamSequence[2].BeamNumber))
        self.assertEqual("3.1",test_rp.IonBeamSequence[2].IonControlPointSequence[1].ScanSpotTuneID)
        self.assertEqual("",test_rp.IonBeamSequence[0].IonControlPointSequence[0].IsocenterPosition)
        self.assertEqual("",test_rp.IonBeamSequence[1].IonControlPointSequence[0].IsocenterPosition)
        self.assertEqual("",test_rp.IonBeamSequence[2].IonControlPointSequence[0].IsocenterPosition)
        self.assertAlmostEqual(120.0   ,test_rp.IonBeamSequence[2].IonControlPointSequence[1].NominalBeamEnergy)
        self.assertAlmostEqual(  0.42e9,test_rp.IonBeamSequence[0].IonControlPointSequence[0].ScanSpotMetersetWeights)
        self.assertAlmostEqual(  0.0   ,test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotMetersetWeights[0])
        self.assertAlmostEqual(  0.6e9 ,test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotMetersetWeights[3])
        self.assertAlmostEqual(  0.5e9 ,test_rp.IonBeamSequence[2].IonControlPointSequence[1].ScanSpotMetersetWeights[1])
        self.assertFalse( hasattr(test_rp.IonBeamSequence[1].IonControlPointSequence[0], "PatientSupportAngle"))
        self.assertFalse( hasattr(test_rp.IonBeamSequence[2].IonControlPointSequence[0], "GantryAngle"))
    def test_mswtot(self):
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        mswtot_list = _get_mswtot_list(test_rp,self.verbose)
        self.assertEqual(3,len(mswtot_list))
        self.assertAlmostEqual(0.42e9,mswtot_list[0])
        self.assertAlmostEqual(1.0e9,mswtot_list[1])
        self.assertAlmostEqual(1.5e9,mswtot_list[2])
    def test_beam_numbers(self):
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        numbers = _get_beam_numbers(test_rp,self.verbose)
        # These numbers are now fixed, right?
        self.assertEqual([1,2,3],numbers)
    def test_angles_and_iscoCs(self):
        test_rp = _check_rp_dicom_file("test.dcm",self.verbose)
        # The "unittest" module has an "assertWarning" test, maybe we should apply that here.
        logger.info("After this message you should see 3x3 warnings about 'absent/corrupted isocenter' and missing patient & gantry angles.")
        gantry_angles, patient_angles, iso_centers = _get_angles_and_isoCs(test_rp,self.verbose)
        for g,p,i in zip(gantry_angles, patient_angles, iso_centers):
            # missing in input, therefore all zero!
            self.assertEqual(g,0.)
            self.assertEqual(p,0.)
            self.assertEqual(3,len(i))
            for j in range(3):
                self.assertEqual(i[j],0.)
    def test_the_whole_thing_already(self):
        # "unittest" has an "assertWarning" test, maybe we should apply that here.
        logger.info("After this message you should see 3x3 warnings about 'absent/corrupted isocenter' and missing patient & gantry angles.")
        dicom_rt_pbs_plan_to_gate_conversion("test.dcm","zero_tolerance.txt",allow0=True,verbose=self.verbose)
        # "unittest" has an "assertWarning" test, maybe we should apply that here.
        logger.info("After this message you should see 3x3 warnings about 'absent/corrupted isocenter' and missing patient & gantry angles.")
        dicom_rt_pbs_plan_to_gate_conversion("test.dcm","zero_nontolerance.txt",allow0=False,verbose=self.verbose)

# vim: set et ts=4 ai sw=4:
