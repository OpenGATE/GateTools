"""
This module contains a function named `dcm_pbs_rt_plan_to_gate_conversion`, which can be
used to convert DICOM radiotherapy plan files for pencil beam scanning to the text format
that Gate uses to read in the spot specifications.
"""
import os, sys, re
import pydicom
import numpy as np
import datetime

def _check_rp_dicom_stuff(rp_filepath,verbose=False):
    """
    Auxiliary implementation function.

    Try to read the DICOM file and perform some paranoid check of the essential DICOM attributes.
    """
    # if the input file path is not readable as a DICOM file, then pydicom will throw an appropriate exception
    rp = pydicom.dcmread(rp_filepath)
    for attr in [ 'SOPClassUID', "NumberOfBeams", "IonBeamSequence" ] :
        if attr not in rp:
            raise IOError("bad DICOM file {},\nmissing '{}'".format(rp_filepath,attr))
    sop_class_name = pydicom.uid.UID_dictionary[rp.SOPClassUID][0]
    if sop_class_name != 'RT Ion Plan Storage':
        raise IOError("bad plan file {},\nwrong SOPClassUID: {}='{}',\nexpecting an 'RT Ion Plan Storage' file instead.".format(rp_filepath,rp.SOPClassUID,sop_class_name))
    n_ion_beams=int(rp.NumberOfBeams)
    ion_beams=rp.IonBeamSequence
    if len(ion_beams) != n_ion_beams:
        raise IOError("bad plan file {},\n'NumberOfBeams'={} inconsistent with length {} of 'IonBeamSequence'.".format(rp_filepath,n_ion_beams,len(ion_beams)))
    for ion_beam in ion_beams:
        for attr in [ 'BeamNumber', "IonControlPointSequence"]:
            if attr not in ion_beam:
                raise IOError("bad DICOM file {},\nmissing '{}' in ion beam".format(rp_filepath,attr))
        for cpi,icp in enumerate(ion_beam.IonControlPointSequence):
            for attr in [ 'NumberOfScanSpotPositions', "ScanSpotPositionMap", "ScanSpotMetersetWeights"]:
                if attr not in icp:
                    raise IOError("bad DICOM file {},\nmissing '{}' in {}th ion control point".format(rp_filepath,attr,cpi))
    if verbose:
        print("Input DICOM file seems to be a legit 'RT Ion Plan Storage' file.")
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
    n_ion_beams=int(rp.NumberOfBeams)
    for ion_beam in rp.IonBeamSequence:
        if input_beam_numbers_are_ok:
            nr = int(ion_beam.BeamNumber)
            if nr < 0:
                input_beam_numbers_are_ok = False
                if verbose:
                    print("CORRUPT INPUT: found a negative beam number {}.".format(nr))
            elif nr in number_list:
                input_beam_numbers_are_ok = False
                if verbose:
                    print("CORRUPT INPUT: found same beam number {} for multiple beams.".format(nr))
            else:
                # still good, keep fingers crossed...
                number_list.append(nr)
    if not input_beam_numbers_are_ok:
        if verbose:
            print("WARNING: will use simple enumeration of beams instead of the (apparently corrupt) dicom beam numbers.")
        number_list = np.arange(n_ion_beams)
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
    # each of these quantities may be missing
    fakeiso=False
    fakegantry=False
    fakepatient=False
    for ion_beam in rp.IonBeamSequence:
        icp0 = ion_beam.IonControlPointSequence[0]
        if not fakeiso:
            if "IsocenterPosition" in icp0:
                if len(icp0.IsocenterPosition) == 3.:
                    iso_center_list.append(np.array([float(v) for v in icp0.IsocenterPosition]))
                else:
                    # I got a DICOM plan file once that specified IsocenterPosition as a single number (-1).
                    fakeiso=True
                    if verbose:
                        "Got corrupted isocenter = '{}'; assuming [0,0,0] for now, keep fingers crossed.".format(self._icp0.IsocenterPosition)
            else:
                fakeiso=True
                if verbose:
                    "No isocenter specified in treatment plan; assuming [0,0,0] for now, keep fingers crossed."
        if not fakegantry:
            if "GantryAngle" in icp0:
                gantry_angle_list.append(float(icp0.GantryAngle))
            else:
                fakegantry=True
                if verbose:
                    "No gantry angle specified in treatment plan; assuming 0. for now, keep fingers crossed."
        if not fakepatient:
            if "PatientSupportAngle" in icp0:
                patient_angle_list.append(float(icp0.PatientSupportAngle))
            else:
                fakepatient=True
                if verbose:
                    "No patient support angle specified in treatment plan; assuming 0. for now, keep fingers crossed."
    if fakeiso:
        iso_center_list = [np.zeros(3)]*n_ion_beams
    if fakegantry:
        gantry_angle_list = np.zeros(n_ion_beams)
    if fakepatient:
        patient_angle_list = np.zeros(n_ion_beams)
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
    rp = _check_dicom_stuff(rp_filepath,verbose)
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
    if len(txt_output)<5:
        raise IOError("Output file name should have at least one charachter before the txt/dat suffix.")
    if os.path.exists(txt_output) and verbose:
        print("WARNING: going to overwrite existing file {}".format(txt_output))
    badchars=re.compile("[^a-zA-Z0-9_]")
    planname = re.sub(badchars,"_",txt_output[:-4])
    if verbose:
        print("using plan name '{}'".format(planname))
    return planname

def dcm_pbs_rt_plan_to_gate_conversion(dcm_input,txt_output,allow0=False,verbose=False):
    """
    Function to create GATE plan description corresponding to DICOM plan file.

    * :param dcm_input: string with the file path of the input DICOM plan file
    * :param txt_output: string with the file path of the output Gate PBS spot specification text file (suffix .txt)
    """
    planname = _check_output_filename(txt_output,verbose)
    nspots_written = 0
    msw_cumsum = 0.
    nlayers = 0
    nspots_ignored = 0
    rp,mswtots,beamnrs,iso_Cs,g_angles,p_angles = _read_and_check_dicom_plan_file(dcm_input,verbose)
    filehandle=open(txt_output,"w")
    # FILE HEADER
    filehandle.write(_file_header.format(name=planname,fields=int(rp.NumberOfBeams)))
    for beamnr in beamnrs:
        filehandle.write("###FieldsID\n{}\n".format(beamnr))
    filehandle.write("#TotalMetersetWeightOfAllFields\n{0:f}\n\n".format(sum(mswtots)))
    for ionbeam,beamnr,mswtot,iso_C,g_angle,p_angle in zip(rp.IonBeamSequence,nrs,mswtots,iso_Cs,g_angles,p_angles):
        filehandle.write(_beam_header.format(fid=beamnr,mswtot=mswtot,ga=ga,psa=psa,isox=iso_C[0],isoy=iso_C[1],isoz=iso_C[2],ncp=len(ion.IonControlPointSequence)))
        msw_cumsum = 0.
        for cpi,icp in enumerate(ionbeam.IonControlPointSequence):
            nspot_nominal = int(icp.NumberOfScanSpotPositions)
            # TODO: some TPS insert spots with weight 0, which only has meaning for the beam delivery system software. Remove them?
            xy = np.array([float(pos) for pos in icp.ScanSpotPositionMap]).reshape(nspot_nominal,2)
            if nspot_nominal == 1:
                w_all = np.array([float(icp.ScanSpotMetersetWeights)])
            else:
                w_all = np.array([float(w) for w in icp.ScanSpotMetersetWeights])
            if allow0:
                nspot = nspot_nominal
                w=w_all
                x=xy[:,0]
                y=xy[:,1]
            else:
                mask=(w_all>0.)
                nspot = np.sum(mask)
                nspot_ignored += nspot_nominal-nspot
                w=w_all[mask]
                x=xy[mask,0]
                y=xy[mask,1]
            energy = float(self._cp.NominalBeamEnergy)
            tuneID = "0.0" if not "ScanSpotTuneID" in icp else str(icp.ScanSpotTuneID) # Maybe we should emit noisy warnings if this is missing?
            filehandle.write(_layer_header.format(cpi=cpi,stid=tuneID,mswtot=msw_cumsum,energy=energy,nspot=nspot))
            for spotx,spoty,spotw in zip(x,y,w):
                self.filehandle.write("{0:g} {1:g} {2:g}\n".format(spotx,spoty,spotw))
            nspots_written += nspots
    if verbose:
        print("Converted DICOM file {} to Gate PBS spot specification text file {}".format(dcm_input,txt_output))
        print("# beams = {}".format(len(rp.IonBeamSequence)))
        print("# control points = {}".format(nlayers))
        print("# spots written = {}".format(nspots))
        if not allow0:
            print("# spots ignored (because msw<=0) = {}".format(nspot_ignored))



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
{ga:g}
###PatientSupportAngle
{psa}
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
{nspot:g}
####X Y Weight (spot position at isocenter in mm, with weight in MU (default) or number of protons "setSpotIntensityAsNbProtons true")
"""

################################################################################
# UNIT TESTS                                                                   #
################################################################################

import unittest

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
        #file_meta.FileMetaInformationGroupLength = 200 # arbitrary?
        #file_meta.FileMetaInformationVersion = b'\x00\x01'
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
                       icp.GantryAngle = beamdata.get('G',-1.)
                       icp.PatientSupportAngle = beamdata.get('P',-1.)
                       icp.IsocenterPosition = list([str(v) for v in beamdata.get('I',(0.,0.,0.))])
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
            print("number of beams is {}".format(self.ds.NumberOfBeams))
        dt = datetime.datetime.now()
        self.ds.ContentDate = dt.strftime('%Y%m%d')
        timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
        self.ds.ContentTime = timeStr
        self.ds.is_little_endian = True
        self.ds.is_implicit_VR = True
        self.ds.fix_meta_info()
        self.ds.save_as(self.dcm_filename)
        if self.verbose:
            print("wrote dicom file {}".format(self.dcm_filename))
    def __del__(self):
        os.remove(self.dcm_filename)
        if self.verbose:
            print("deleted dicom file {}".format(self.dcm_filename))
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
                     controlpoints=[dict(SSW=[0.4,0.6],E=100.,T="3.0",
                                         SSP=[(2.,1),(3.,4.)])])
        beam6 = dict(Nm="baz", Nr=6, G=60., P=30., I=(-10.,-150.,40.),
                     controlpoints=[dict(SSW=[0.4,0.6,0.8],E=70.,T="3.1",
                                         SSP=[(2.,1),(3.,4.),(6.,5.)]),
                                    dict(SSW=[0.4,0.5],E=120.,T="3.1",
                                         SSP=[(7.,8.),(3.,4.)])])
        self.beams = [beam4,beam5,beam6]
        self.verbose = True
        self.helper = _tmp_test_plan_writer("test.dcm",spotspecs=[beam4,beam5,beam6])
        #self.helper = _test_plan_creator("test.dcm",spotspecs=[beam0])
    def tearDown(self):
        del self.helper
    def test_dicom(self):
        """
        Self consistency check for test dicom file.
        """
        test_rp = _check_rp_dicom_stuff("test.dcm",self.verbose)
        self.assertEqual(3,len(test_rp.IonBeamSequence))
        self.assertEqual(4,int(test_rp.IonBeamSequence[0].BeamNumber))
        self.assertEqual(5,int(test_rp.IonBeamSequence[1].BeamNumber))
        self.assertEqual(6,int(test_rp.IonBeamSequence[2].BeamNumber))
        self.assertEqual("3.0",test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotTuneID)
        self.assertAlmostEqual(120.0,test_rp.IonBeamSequence[2].IonControlPointSequence[1].NominalBeamEnergy)
        self.assertAlmostEqual(0.42,test_rp.IonBeamSequence[0].IonControlPointSequence[0].ScanSpotMetersetWeights)
        self.assertAlmostEqual(0.6,test_rp.IonBeamSequence[1].IonControlPointSequence[0].ScanSpotMetersetWeights[1])
        self.assertAlmostEqual(0.4,test_rp.IonBeamSequence[2].IonControlPointSequence[1].ScanSpotMetersetWeights[0])
        self.assertAlmostEqual(45.,test_rp.IonBeamSequence[1].IonControlPointSequence[0].PatientSupportAngle)
        self.assertAlmostEqual(60.,test_rp.IonBeamSequence[2].IonControlPointSequence[0].GantryAngle)
    def test_mswtot(self):
        test_rp = _check_rp_dicom_stuff("test.dcm",self.verbose)
        mswtot_list = _get_mswtot_list(test_rp,self.verbose)
        self.assertEqual(3,len(mswtot_list))
        self.assertAlmostEqual(0.42,mswtot_list[0])
        self.assertAlmostEqual(1.0,mswtot_list[1])
        self.assertAlmostEqual(2.7,mswtot_list[2])
    def test_beam_numbers(self):
        test_rp = _check_rp_dicom_stuff("test.dcm",self.verbose)
        numbers = _get_beam_numbers(test_rp,self.verbose)
        self.assertEqual([4,5,6],numbers)
    def test_angles_and_iscoCs(self):
        test_rp = _check_rp_dicom_stuff("test.dcm",self.verbose)
        gantry_angles, patient_angles, iso_centers = _get_angles_and_isoCs(test_rp,self.verbose)
        for g,p,i,b in zip(gantry_angles, patient_angles, iso_centers, self.beams):
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
        self.assertEqual("ab_c",_check_output_filename("ab.c.txt",self.verbose))
        self.assertEqual("_",_check_output_filename(" .txt",self.verbose))
        self.assertEqual("_Box_6__0__0__25___Rashi",_check_output_filename("_Box 6 (0, 0, 25) ^Rashi.txt",self.verbose))

# vim: set et ts=4 ai sw=4:
