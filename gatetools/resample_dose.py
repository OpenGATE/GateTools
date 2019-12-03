"""
This module provides a function for mass weighted resampling of an image file
that contains a 3D dose distribution to match the geometry (origin, spacing,
number of voxels per dimension) of a reference image.

The resampled dose R_j in voxel j of the new grid is computed as follows from the
dose D_i of voxels i in the input dose distribution, the corresponding masses (or mass densities) M_i
and the volumes V_i_j of each pair of input voxel i and output voxel j:
    R_j = Sum_i w_i_j D_i / N_j
    w_i_j = V_i_j * M_i
    N_j = Sum_i w_i_j

If you choose to run the multithreaded version, then it is your own
responsibility to make wise choice for the number of threads, based on (e.g.)
the number of physical cores, the available RAM and the current workload on the
machine.
"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import numpy as np
import itk
from datetime import datetime
import logging
logger = logging.getLogger()

def mass_weighted_resampling(dose,mass,newgrid):
    """
    This function computes a dose distribution using the geometry (origin,
    size, spacing) of the `newgrid` image, using the energy deposition and mass
    with some different geometry. A typical use case is that a Gate simulation first
    computes the dose w.r.t. a patient CT (exporting also the mass image),
    and then we want to resample this dose distribution to the geometry of the
    new grid, e.g. from the dose distribution computed by a TPS.

    This implementation relies on a bit of numpy magic (np.tensordot,
    repeatedly).  A intuitively more clear but in practice much slower
    implementation is given by `_mwr_wit_loops(dose,mass,newgrid)`; the unit
    tests are verifying that these two implementation indeed yield the same
    result. 
    """
    assert(_equal_geometry(dose,mass))
    if _equal_geometry(dose,newgrid):
        # If input and output geometry are equal, then we don't need to do anything, just copy the input dose.
        newdose=itk.image_from_array(itk.array_from_image(dose))
        newdose.CopyInformation(dose)
        return newdose
    if not _enclosing_geometry(dose,newgrid):
        # In a later release we may provide some smart code to deal with dose resampling outside of the input geometry.
        raise RuntimeError("new grid must be inside the old one")
    # start the timer
    t0=datetime.now()
    xol,yol,zol = [ _overlaps(*xyz) for xyz in zip(dose.GetOrigin(),
                                                   dose.GetSpacing(),
                                                   dose.GetLargestPossibleRegion().GetSize(),
                                                   newgrid.GetOrigin(),
                                                   newgrid.GetSpacing(),
                                                   newgrid.GetLargestPossibleRegion().GetSize()) ]
    adose = itk.array_from_image(dose)
    amass = itk.array_from_image(mass)
    aedep = adose*amass
    # now the magic happens :-)
    anew = np.tensordot(zol,np.tensordot(yol,np.tensordot(xol,aedep,axes=(0,2)),axes=(0,2)),axes=(0,2))
    wsum = np.tensordot(zol,np.tensordot(yol,np.tensordot(xol,amass,axes=(0,2)),axes=(0,2)),axes=(0,2))
    # paranoia
    mzyx = tuple(np.array(newgrid.GetLargestPossibleRegion().GetSize())[::-1])
    assert(anew.shape==mzyx)
    assert(wsum.shape==mzyx)
    # dose=edep/mass, but only if mass>0
    mask=(wsum>0)
    anew[mask]/=wsum[mask]
    newdose=itk.image_from_array(anew)
    newdose.CopyInformation(newgrid)
    # stop the timer
    t1=datetime.now()
    dt=(t1-t0).total_seconds()
    logger.debug(f"resampling using `np.tensordot` took {dt:.3f} seconds")
    return newdose

    
################################################################################
# IMPLEMENTATION DETAILS, DO NOT USE IN CLIENT CODE                            #
################################################################################

def _mwr_with_loops(dose,mass,newgrid):
    """
    Reference implementation, only for testing.

    This function computes a dose distribution using the geometry (origin,
    size, spacing) of the `newgrid` image, using the energy deposition and mass
    with some different geometry. A typical use case is that a Gate simulation first
    computes the dose w.r.t. a patient CT (exporting also the mass image),
    and then we want to resample this dose distribution to the geometry of the
    new grid, e.g. from the dose distribution computed by a TPS.
    """
    assert(_equal_geometry(dose,mass))
    if _equal_geometry(dose,newgrid):
        # If input and output geometry are equal, then we don't need to do anything, just copy the input dose.
        newdose=itk.image_from_array(itk.array_from_image(dose))
        newdose.CopyInformation(dose)
        return newdose
    if not _enclosing_geometry(dose,newgrid):
        # In a later release we may provide some smart code to deal with dose resampling outside of the input geometry.
        raise RuntimeError("new grid must be inside the old one")
    t0=datetime.now()
    xol,yol,zol = [ _overlaps(*xyz) for xyz in zip(dose.GetOrigin(),
                                                   dose.GetSpacing(),
                                                   dose.GetLargestPossibleRegion().GetSize(),
                                                   newgrid.GetOrigin(),
                                                   newgrid.GetSpacing(),
                                                   newgrid.GetLargestPossibleRegion().GetSize()) ]
    nxyz = np.array(dose.GetLargestPossibleRegion().GetSize())
    mxyz = np.array(newgrid.GetLargestPossibleRegion().GetSize())
    mzyx = mxyz[::-1].tolist()
    adose = itk.array_from_image(dose)
    amass = itk.array_from_image(mass)
    anew = np.zeros(mzyx,dtype=float)
    wsum = np.zeros(mzyx,dtype=float)
    N_ops = 0
    # loop over nonzero overlaps of x-internvals
    for (ixs,ixd) in zip(*np.nonzero(xol)):
        dx = xol[ixs,ixd]
        # loop over nonzero overlaps of y-internvals
        for (iys,iyd) in zip(*np.nonzero(yol)):
            dy = yol[iys,iyd]
            # loop over nonzero overlaps of z-internvals
            for (izs,izd) in zip(*np.nonzero(zol)):
                dz = zol[izs,izd]
                w = dx*dy*dz*amass[izs,iys,ixs]
                anew[izd,iyd,ixd] += adose[izs,iys,ixs]*w
                wsum[izd,iyd,ixd] += w
                N_ops += 1
    mask=(wsum>0)
    anew[mask]/=wsum[mask]
    newdose=itk.image_from_array(anew)
    newdose.CopyInformation(newgrid)
    t1=datetime.now()
    dt=(t1-t0).total_seconds()
    logger.debug(f"resampling using explicit loops over nonzero voxel overlaps took {dt:.3f} seconds")
    return newdose
    

def _equal_geometry(img1,img2):
    """
    Do img1 and img2 have the same geometry (same voxels)?

    This is an auxiliary function for `mass_weighted_resampling`.
    """
    if not np.allclose(img1.GetOrigin(),img2.GetOrigin()):
        return False
    if not np.allclose(img1.GetSpacing(),img2.GetSpacing()):
        return False
    if (np.array(img1.GetLargestPossibleRegion().GetSize())==np.array(img2.GetLargestPossibleRegion().GetSize())).all():
        return True
    return False

def _enclosing_geometry(img1,img2):
    """
    Does img1 enclose img2?
    """
    if _equal_geometry(img1,img2):
        return True
    o1=np.array(img1.GetOrigin())
    o2=np.array(img2.GetOrigin())
    s1=np.array(img1.GetSpacing())
    s2=np.array(img2.GetSpacing())
    # check the lower corner
    if ((o1-0.5*s1)>(o2-0.5*s2)).any():
        return False
    n1=np.array(img1.GetLargestPossibleRegion().GetSize())
    n2=np.array(img2.GetLargestPossibleRegion().GetSize())
    # check the upper corner
    if ((o1+(n1-0.5)*s1)<(o2+(n2-0.5)*s2)).any():
        return False
    return True

def _overlaps(a0,da,na,b0,db,nb,label="",center=True):
    """
    This function returns an (na,nb) array with the length of the overlaps in
    two ranges of intervals. In other words, the value of the element (i,j)
    represents the length that the i'th interval of A overlaps with the j'th
    interval of B.

    If center is True, then a0 and b0 are assumed to be the *centers* of the first
    interval of range A and B, respectively. 
    If center is False, then a0 and b0 are assumed to be the *left edge* of the first
    interval of range A and B, respectively. 

    This is an auxiliary function for `mass_weighted_resampling`.
    """
    # paranoid checks :-)
    assert(da>0)
    assert(db>0)
    assert(type(na)==int)
    assert(type(nb)==int)
    assert(na>0)
    assert(nb>0)
    assert(a0<np.inf)
    assert(b0<np.inf)
    assert(a0>-np.inf)
    assert(b0>-np.inf)
    if center:
        # Assume that the given a0 and b0 values represent the center of the first bin.
        # In these calculations it's more convenient to work with the left edge.
        a0-=0.5*da
        b0-=0.5*db
    o=np.zeros((na,nb),dtype=float)
    if a0+na*da<b0 or b0+nb*db<a0:
        # no overlap at all
        return o
    ia,a,ada=0,a0,a0+da
    ib,b,bdb=0,b0,b0+db
    while ia<na and ib<nb:
        if ada<b or np.isclose(ada,b):
            ab=True
        elif bdb<a or np.isclose(bdb,a):
            ab=False
        else:
            o[ia,ib]=min(ada,bdb)-max(a,b)
            logger.debug(f"o[{ia},{ib}]={o[ia,ib]:.2f}")
            ab = (ada<bdb)
        if ab:
            ia+=1
            a=ada
            ada=a0+(ia+1)*da
        else:
            ib+=1
            b=bdb
            bdb=b0+(ib+1)*db
    return o


################################################################################
# UNIT TESTS                                                                   #
################################################################################

import unittest
from .logging_conf import LoggedTestCase

class overlaptests(LoggedTestCase):
    def test_IdenticalRanges(self):
        # 10 bins with step 1
        idr1=_overlaps(0,1,10,0,1,10,"idr1",center=False)
        self.assertTrue(idr1.shape==(10,10))
        self.assertTrue(np.allclose(idr1,1.*np.identity(10)))
        # 11 bins with step 2
        idr2=_overlaps(10.,2.,11,10.,2.,11,"idr2",center=False)
        self.assertTrue(idr2.shape==(11,11))
        self.assertTrue(np.allclose(idr2,2.*np.identity(11)))
        # 20 bins with step 0.5, starting value is negative
        idr3=_overlaps(-5.,0.5,20,-5.,0.5,20,"idr3",center=False)
        self.assertTrue(idr3.shape==(20,20))
        self.assertTrue(np.allclose(idr3,0.5*np.identity(20)))
    def test_center_vs_left_edge(self):
        # 10 identical bins with step 1
        oc1=_overlaps(0,1,10,0,1,10,"oc1",center=False)
        oc2=_overlaps(0.5,1,10,0.5,1,10,"oc2",center=True)
        self.assertTrue(oc1.shape==(10,10))
        self.assertTrue(oc2.shape==(10,10))
        self.assertTrue(np.allclose(oc1,oc2))
        # 10 shifted bins with step 1
        oc3=_overlaps(  0,1,10,0.1,1,10,"oc3",center=False)
        oc4=_overlaps(0.5,1,10,0.6,1,10,"oc4",center=True)
        oc5=_overlaps(0.5,1,10,0.7,1,10,"oc5",center=True) # deliberate error in b0
        self.assertTrue(oc3.shape==(10,10))
        self.assertTrue(oc4.shape==(10,10))
        self.assertTrue(oc5.shape==(10,10))
        self.assertTrue(np.allclose(oc3,oc4))
        self.assertFalse(np.allclose(oc3,oc5))
        # integer overlap
        oc6=_overlaps(0.0,1,10,0.00,0.1,100,"oc6",center=False)
        oc7=_overlaps(0.5,1,10,0.05,0.1,100,"oc7",center=True)
        self.assertTrue(oc6.shape==(10,100))
        self.assertTrue(oc7.shape==(10,100))
        self.assertTrue(np.allclose(oc6,oc7))
    def test_NonOverlap(self):
        # two consecutive ranges
        no1=_overlaps(0,1,10,10,1,10,"no1",center=False)
        self.assertTrue(no1.shape==(10,10))
        self.assertTrue(np.allclose(no1,0.))
        # two consecutive ranges (second before the first)
        no2=_overlaps(0,1,10,-10,1,10,"no2",center=False)
        self.assertTrue(no2.shape==(10,10))
        self.assertTrue(np.allclose(no2,0.))
        # two nonconsecutive non-overlapping ranges
        no3=_overlaps(0,1,10,-20,0.5,15,"no3",center=False)
        self.assertTrue(no3.shape==(10,15))
        self.assertTrue(np.allclose(no3,0.))
    def test_IntegerOverlap(self):
        # divide bins up in 10 
        io1=_overlaps(0,1,10,0,0.1,100,"io1",center=False)
        self.assertTrue(io1.shape==(10,100))
        io1exp=np.zeros((10,100),dtype=float)
        for i in range(10):
            io1exp[i,10*i:10*(i+1)]=0.1
        self.assertTrue(np.allclose(io1,io1exp))
        # divide half of the bins up in 20 pieces
        io2=_overlaps(-5,1,10,0,0.05,100,"io2",center=False)
        self.assertTrue(io2.shape==(10,100))
        io2exp=np.zeros((10,100),dtype=float)
        for i in range(5):
            io2exp[i+5,20*i:20*(i+1)]=0.05
        self.assertEqual(np.sum(np.isclose(io2,0.05)),100)
        self.assertTrue(np.allclose(io2,io2exp))
        # divide half of the bins up in 20 pieces, flip
        io3=_overlaps(-5,0.05,100,-5,1,10,"io3",center=False)
        self.assertTrue(io3.shape==(100,10))
        io3exp=np.zeros((100,10),dtype=float)
        for i in range(5):
            io3exp[20*i:20*(i+1),i]=0.05
        self.assertEqual(np.sum(np.isclose(io3,0.05)),100)
        self.assertTrue(np.allclose(io3,io3exp))
    def test_NonTrivial(self):
        # interval lengths have non-integer ratio and start/end points have no nice relation either
        nt1=_overlaps(-1.1,0.4,5,-0.9,0.55,4,"nt1",center=False)
        # a: -1.10 (0) -0.70 (1) -0.30 (2) +0.10 (3) +0.50 (4) +0.90
        # b: -0.90 (0) -0.35 (1) +0.20 (2) +0.75 (3) +1.30
        nt1exp=np.zeros((5,4),dtype=float)
        nt1exp[0,0]=0.20 # -0.9 till -0.7
        nt1exp[1,0]=0.35 # -0.7 till -0.35
        nt1exp[1,1]=0.05 # -0.35 till -0.30
        nt1exp[2,1]=0.40 # -0.30 till +0.10
        nt1exp[3,1]=0.10 # +0.10 till +0.20
        nt1exp[3,2]=0.30 # +0.20 till +0.50
        nt1exp[4,2]=0.25 # +0.50 till +0.75
        nt1exp[4,3]=0.15 # +0.75 till +0.90
        self.assertEqual(np.sum(nt1>0),np.sum(nt1exp>0))
        self.assertTrue(np.allclose(nt1,nt1exp))
        nt2=_overlaps(-0.9,0.55,4,-1.1,0.4,5,"flipped",center=False)
        nt2exp=nt1exp.T
        self.assertEqual(np.sum(nt2>0),np.sum(nt2exp>0))
        self.assertTrue(np.allclose(nt2,nt2exp))

class dose_resampling_tests(LoggedTestCase):
    def setUp(self):
        self.dims = (200,300,40)
        self.spacing = (0.06,0.05,0.4)
        self.origin = (-4.4,5.5,-6.6)
        self.adose = np.random.normal(1.,0.05,self.dims[::-1]).astype(np.float32)
        self.amass = np.ones(self.dims[::-1],dtype=np.float32)
        self.aedep = self.adose * self.amass
        self.dose = itk.image_from_array(self.adose)
        self.mass = itk.image_from_array(self.amass)
        self.edep = itk.image_from_array(self.aedep)
        for img in [self.dose,self.mass,self.edep]:
            img.SetSpacing(self.spacing)
            img.SetOrigin(self.origin)
        self.newdims  = (150,200,10)
        self.newspacing  = (0.05,0.06,0.5)
        self.neworigin  = (-4.0,5.95,-6.0)
        self.anewdose = np.zeros(self.newdims[::-1],dtype=np.float32)
        self.newdose = itk.image_from_array(self.anewdose)
        self.newdose.SetSpacing(self.newspacing)
        self.newdose.SetOrigin(self.neworigin)
    def test_big(self):
        resampled_loops=_mwr_with_loops(self.dose,self.mass,self.newdose)
        resampled=mass_weighted_resampling(self.dose,self.mass,self.newdose)
        self.assertTrue(_equal_geometry(resampled_loops,self.newdose))
        self.assertTrue(_equal_geometry(resampled,self.newdose))
        ar0=itk.array_from_image(resampled_loops)
        ar1=itk.array_from_image(resampled)
        self.assertTrue(np.allclose(ar0,ar1))
    def test_single_voxel(self):
        # source grid is 2x2x2 voxels with spacing 1x1x1, centered on (0,0,0)
        # dest grid is 1x1x1 voxels with spacing 1x1x1, centered on (0,0,0)
        amass = np.float32(1+np.arange(8)).reshape(2,2,2)
        adose = np.float32(np.random.normal(1.,0.05,(2,2,2)))
        anew = np.ones((1,1,1),dtype=np.float32)
        dose=itk.image_from_array(adose)
        mass=itk.image_from_array(amass)
        for img in (dose,mass):
            img.SetOrigin((-0.5,-0.5,-0.5))
        newgrid=itk.image_from_array(anew)
        value1=_mwr_with_loops(dose,mass,newgrid).GetPixel((0,0,0))
        value2=mass_weighted_resampling(dose,mass,newgrid).GetPixel((0,0,0))
        # intersection volumes are all equal
        expval = np.sum(adose*amass)/np.sum(amass)
        self.assertAlmostEqual(value1,expval,places=5)
        self.assertAlmostEqual(value2,expval,places=5)
        # now try with intersection volumes NOT equal
        # source grid is unchanged: 2x2x2 voxels with spacing 1x1x1, centered on (0,0,0)
        # dest grid is shifted: 1x1x1 voxels with spacing 1x1x1, centered on (dx,dy,dz)
        dx,dy,dz=0.1,-0.15,0.2
        newgrid.SetOrigin((dx,dy,dz))
        value1=_mwr_with_loops(dose,mass,newgrid).GetPixel((0,0,0))
        value2=mass_weighted_resampling(dose,mass,newgrid).GetPixel((0,0,0))
        expval = 0.
        norm = 0.
        for ix,wx in enumerate([0.5-dx, 0.5+dx]):
            for iy,wy in enumerate([0.5-dy, 0.5+dy]):
                for iz,wz in enumerate([0.5-dz, 0.5+dz]):
                    expval += dose.GetPixel((ix,iy,iz))*mass.GetPixel((ix,iy,iz))*wx*wy*wz
                    norm += mass.GetPixel((ix,iy,iz))*wx*wy*wz
        logger.debug(f"value1 = {value1}")
        logger.debug(f"exp value = {expval}")
        logger.debug(f"norm = {norm}")
        expval/=norm
        logger.debug(f"normalized exp value = {expval}")
        self.assertAlmostEqual(expval,value1,places=5)
        self.assertAlmostEqual(expval,value2,places=5)
