"""
This module provides single threaded and multithreaded functions for mass
weighted resampling an image file that contains a 3D dose distribution to match
the geometry (origin, spacing, number of voxels per dimension) of a reference
image.

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

def mass_weighted_resampling(dose,mass,newgrid,nthreads=1):
    """
    This function computes a dose distribution using the geometry (origin,
    size, spacing) of the `newgrid` image, using the energy deposition and mass
    with some different geometry. A typical use case is that a Gate simulation first
    computes the dose w.r.t. a patient CT (exporting also the mass image),
    and then we want to resample this dose distribution to the geometry of the
    new grid, e.g. from the dose distribution computed by a TPS.

    If nthreads==1 (default), then the resampling will be computed using a
    single thread.  If nthreads>1, then the resampling will be computed using
    multiple threads, unless the output grid is too course to split up the
    calculation.  If nthreads=0, then a guess will be made based on the
    available RAM, number cores and the current workload on the machine.
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
    xyz_ol = [ _overlaps(*xyz) for xyz in zip(dose.GetOrigin(),
                                              dose.GetSpacing(),
                                              dose.GetLargestPossibleRegion().GetSize(),
                                              newgrid.GetOrigin(),
                                              newgrid.GetSpacing(),
                                              newgrid.GetLargestPossibleRegion().GetSize()) ]
    nxyz = np.array(dose.GetLargestPossibleRegion().GetSize())
    mxyz = np.array(newgrid.GetLargestPossibleRegion().GetSize())
    mzyx = mxyz[::-1].tolist()
    if mxyz[0]<nthreads:
        print(f"WARNING: going to use {mx} threads instead of {nthreads}")
        nthreads=mxyz[0]
    if nthreads==0:
        nthreads = _guess_n_threads(np.prod(nxyz),np.prod(mxyz))
    adose = itk.array_from_image(dose)
    amass = itk.array_from_image(mass)
    anew = np.zeros(mzyx,dtype=float)
    wsum = np.zeros(mzyx,dtype=float)
    if nthreads==1:
        _mass_weighted_summing(xyz_ol,adose,amass,anew,wsum)
    else:
        import multiprocessing
        from multiprocessing import Queue
        qoutput=Queue()
        threads = []
        for ithread in range(nthreads):
            t = multiprocessing.Process(target=_mass_weighted_summing_mt,args=[xyz_ol,adose.copy(),amass.copy(),qoutput,ithread,nthreads])
            t.start()
            threads.append(t)
        #print("collecting output data")
        for i in range(nthreads):
            #print(f"waiting {i}th process to finish...")
            j,janew,jwsum=qoutput.get()
            #print(f"i={i} j={j} dsum={np.sum(janew)} wsum={np.sum(jwsum)}")
            for jx in range(janew.shape[2]):
                ix=jx*nthreads+j
                wsum[:,:,ix]+=jwsum[:,:,jx]
                anew[:,:,ix]+=janew[:,:,jx]
        for it,t in enumerate(threads):
            #print(f"waiting for thread nr {it} to join")
            t.join()
    #print(f"top 2x2x2 weights: {wsum[:2,:2,:2]}")
    #print(f"top 2x2x2 doses: {anew[:2,:2,:2]}")
    mask=(wsum>0)
    anew[mask]/=wsum[mask]
    newdose=itk.image_from_array(anew)
    newdose.CopyInformation(newgrid)
    t1=datetime.now()
    dt=(t1-t0).total_seconds()
    print(f"resampling using {nthreads} thread(s) took {dt:.3f} seconds")
    return newdose
    

#def resample_dose(dose,mass,newgrid):
#    """
#    This function computes a dose distribution using the geometry (origin,
#    size, spacing) of the `newgrid` image, using the energy deposition and mass
#    with some different geometry. A typical use case is that a Gate simulation first
#    computes the dose w.r.t. a patient CT (exporting also the mass image),
#    and then we want to resample this dose distribution to the geometry of the
#    new grid, e.g. from the dose distribution computed by a TPS.
#
#    This is the single threaded implementation.
#    """
#    t0=datetime.now()
#    assert(_equal_geometry(dose,mass))
#    if _equal_geometry(dose,newgrid):
#        newdose=itk.image_from_array(itk.array_from_image(dose))
#        newdose.CopyInformation(dose)
#        return newdose
#    if not _enclosing_geometry(dose,newgrid):
#        raise RuntimeError("new grid must be inside the old one")
#    xol,yol,zol = [ _overlaps(*xyz) for xyz in zip(dose.GetOrigin(),
#                                                  dose.GetSpacing(),
#                                                  dose.GetLargestPossibleRegion().GetSize(),
#                                                  newgrid.GetOrigin(),
#                                                  newgrid.GetSpacing(),
#                                                  newgrid.GetLargestPossibleRegion().GetSize()) ]
#    adose = itk.array_from_image(dose)
#    amass = itk.array_from_image(mass)
#    nz,ny,nx = adose.shape
#    mz,my,mx = itk.array_from_image(newgrid).shape
#    assert(xol.shape==(nx,mx))
#    assert(yol.shape==(ny,my))
#    assert(zol.shape==(nz,mz))
#    anew = np.zeros((mz,my,mx),dtype=float)
#    wsum = np.zeros((mz,my,mx),dtype=float)
#    N_ops = 0
#    for (ixs,ixd) in zip(*np.nonzero(xol)):
#        dx=xol[ixs,ixd]
#        for (iys,iyd) in zip(*np.nonzero(yol)):
#            dy=yol[iys,iyd]
#            for (izs,izd) in zip(*np.nonzero(zol)):
#                dz=zol[izs,izd]
#                w = dx*dy*dz*amass[izs,iys,ixs]
#                anew[izd,iyd,ixd] += adose[izs,iys,ixs]*w
#                wsum[izd,iyd,ixd] += w
#                N_ops += 1
#    mask=(wsum>0)
#    anew[mask]/=wsum[mask]
#    newdose=itk.image_from_array(anew)
#    newdose.CopyInformation(newgrid)
#    t1=datetime.now()
#    print("resampling with numpy magic took {}, preformed {} ops".format(t1-t0,N_ops))
#    return newdose
    
################################################################################
# IMPLEMENTATION DETAILS, DO NOT USE IN CLIENT CODE                            #
################################################################################

def _mass_weighted_summing(xyz_ol,adose,amass,anew,wsum):
    """
    This function loops over the intersecting source/destination bins and computes the
    numerator & denominator sums for each destination voxel. No threading.
    """
    assert(len(xyz_ol)==3)
    xol,yol,zol=xyz_ol[:]
    N_ops = 0
    for (ixs,ixd) in zip(*np.nonzero(xol)):
        dx = xol[ixs,ixd]
        for (iys,iyd) in zip(*np.nonzero(yol)):
            dy = yol[iys,iyd]
            for (izs,izd) in zip(*np.nonzero(zol)):
                dz = zol[izs,izd]
                w = dx*dy*dz*amass[izs,iys,ixs]
                anew[izd,iyd,ixd] += adose[izs,iys,ixs]*w
                wsum[izd,iyd,ixd] += w
                N_ops += 1
    #print(f"Unthreaded implementation performed {N_ops} ops, sum of dose values is {np.sum(anew)} total weight is {np.sum(wsum)}")

def _mass_weighted_summing_mt(xyz_ol,adose,amass,qoutput,ithread,nthread):
    """
    This function loops over the intersecting source/destination bins and
    computes the numerator & denominator sums for each destination voxel.
    Multithreaded implementation.  Only the destination x-slices with (index
    modulo nthreads) equal to (the thread number) will be computed (and the
    results will be combined by the main thread). This way each thread will
    write to a different subset of the output dose array.
    """
    assert(nthread>1)
    assert(0<=ithread<nthread)
    assert(len(xyz_ol)==3)
    xol,yol,zol=xyz_ol[:]
    nx,mx=xol.shape
    ny,my=yol.shape
    nz,mz=zol.shape
    mxmod=mx//nthread
    if mx%nthread>ithread:
        mxmod+=1
    anew = np.zeros((mz,my,mxmod),dtype=float)
    wsum = np.zeros((mz,my,mxmod),dtype=float)
    N_ops = 0
    for (ixs,ixd) in zip(*np.nonzero(xol)):
        if nthread>1 and (ixd%nthread) != ithread:
            continue
        dx = xol[ixs,ixd]
        ixdmod=ixd//nthread
        for (iys,iyd) in zip(*np.nonzero(yol)):
            dy = yol[iys,iyd]
            for (izs,izd) in zip(*np.nonzero(zol)):
                dz = zol[izs,izd]
                w = dx*dy*dz*amass[izs,iys,ixs]
                anew[izd,iyd,ixdmod] += adose[izs,iys,ixs]*w
                wsum[izd,iyd,ixdmod] += w
                N_ops += 1
    #print(f"thread {ithread}/{nthread} performed {N_ops} ops, sum of dose values is {np.sum(anew)} total weight is {np.sum(wsum)}")
    qoutput.put([ithread,anew,wsum])

def _mwr_simplistically(dose,mass,newgrid):
    """
    This function computes the same thing as `mass_weighted_resampling`, only
    with a much more simplistic implementation that is only intended to be used
    in the unit tests.
    """
    t0=datetime.now()
    assert(_equal_geometry(dose,mass))
    if _equal_geometry(dose,newgrid):
        newdose=itk.image_from_array(itk.array_from_image(dose))
        newdose.CopyInformation(dose)
        return newdose
    if not _enclosing_geometry(dose,newgrid):
        raise RuntimeError("new grid must be inside the old one")
    xol,yol,zol = [ _overlaps(*xyz,center=True) for xyz in zip(dose.GetOrigin(),
                                                              dose.GetSpacing(),
                                                              dose.GetLargestPossibleRegion().GetSize(),
                                                              newgrid.GetOrigin(),
                                                              newgrid.GetSpacing(),
                                                              newgrid.GetLargestPossibleRegion().GetSize()) ]
    adose = itk.array_from_image(dose)
    amass = itk.array_from_image(mass)
    nz,ny,nx = adose.shape
    mz,my,mx = itk.array_from_image(newgrid).shape
    assert(xol.shape==(nx,mx))
    assert(yol.shape==(ny,my))
    assert(zol.shape==(nz,mz))
    anew = np.zeros((mz,my,mx),dtype=float)
    wsum = np.zeros((mz,my,mx),dtype=float)
    N_ops = 0
    for ix in range(mx):
        for iy in range(my):
            for iz in range(mz):
                for jx in range(nx):
                    dx = xol[jx,ix]
                    if dx==0:
                        continue
                    for jy in range(ny):
                        dy = yol[jy,iy]
                        if dy==0:
                            continue
                        for jz in range(nz):
                            dz = zol[jz,iz]
                            if dz==0:
                                continue
                            w = dx*dy*dz*amass[jz,jy,jx]
                            anew[iz,iy,ix] += adose[jz,jy,jx]*w
                            wsum[iz,iy,ix] += w
                            N_ops += 1
    mask=(wsum>0)
    anew[mask]/=wsum[mask]
    newdose=itk.image_from_array(anew)
    newdose.CopyInformation(newgrid)
    t1=datetime.now()
    #print("resampling with brute force took {}, performed {} ops".format(t1-t0,N_ops))
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
            #print(f"o[{ia},{ib}]={o[ia,ib]:.2f}")
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

def _guess_n_threads(nvoxels_in,nvoxels_out):
    # we need two float32 input images (dose and mass) per process
    # we need two float32 output images (dose and mass) per process
    ram_bytes_per_process = 2*4*nvoxels_in+2*nvoxels_out
    import psutil
    ram_bytes_available = psutil.virtual_memory().available
    ram_bytes_arbitrary_margin = 500*1024*1024 # 500 MiB
    nram = max(1,int(np.floor(ram_bytes_available-ram_bytes_arbitrary_margin) / ram_bytes_per_process))
    n_physical_cores = psutil.cpu_count(False)
    n_busy_cores = sum(psutil.cpu_percent(percpu=True))/100.
    ncpu=max(1,int(n_physical_cores-n_busy_cores))
    nthreads=min(nram,ncpu)
    print(f"nthreads guess: {nthreads} (CPU limit: {ncpu}, RAM limit: {nram})")
    return nthreads


################################################################################
# UNIT TESTS                                                                   #
################################################################################

import unittest

class overlaptests(unittest.TestCase):
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

class dose_resampling_tests(unittest.TestCase):
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
        #resampled0=_mwr_simplistically(self.dose,self.mass,self.newdose)
        resampled1=mass_weighted_resampling(self.dose,self.mass,self.newdose)
        self.assertTrue(_equal_geometry(resampled1,self.newdose))
        ar1=itk.array_from_image(resampled1)
        nmax=_guess_n_threads(np.prod(self.dims),np.prod(self.newdims))
        print(f"going to check nthreads=2..{nmax}")
        for nthreads in range(2,nmax+1):
            resampledN=mass_weighted_resampling(self.dose,self.mass,self.newdose,nthreads)
            self.assertTrue(_equal_geometry(resampledN,self.newdose))
            arN=itk.array_from_image(resampledN)
            #print("number of nonzero voxel values: {}, {}".format(np.sum(ar1>0),np.sum(arN>0)))
            #print("number of voxels NOT close: {} (out of {})".format(np.sum(np.logical_not(np.isclose(ar1,arN))),np.prod(self.newdims)))
            self.assertTrue(np.allclose(ar1,arN))
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
        value=_mwr_simplistically(dose,mass,newgrid).GetPixel((0,0,0))
        value2=mass_weighted_resampling(dose,mass,newgrid).GetPixel((0,0,0))
        # intersection volumes are all equal
        expval = np.sum(adose*amass)/np.sum(amass)
        self.assertAlmostEqual(value,expval,places=5)
        self.assertAlmostEqual(value2,expval,places=5)
        # now try with intersection volumes NOT equal
        # source grid is unchanged: 2x2x2 voxels with spacing 1x1x1, centered on (0,0,0)
        # dest grid is shifted: 1x1x1 voxels with spacing 1x1x1, centered on (dx,dy,dz)
        dx,dy,dz=0.1,-0.15,0.2
        newgrid.SetOrigin((dx,dy,dz))
        value=_mwr_simplistically(dose,mass,newgrid).GetPixel((0,0,0))
        value2=mass_weighted_resampling(dose,mass,newgrid).GetPixel((0,0,0))
        expval = 0.
        norm = 0.
        for ix,wx in enumerate([0.5-dx, 0.5+dx]):
            for iy,wy in enumerate([0.5-dy, 0.5+dy]):
                for iz,wz in enumerate([0.5-dz, 0.5+dz]):
                    expval += dose.GetPixel((ix,iy,iz))*mass.GetPixel((ix,iy,iz))*wx*wy*wz
                    norm += mass.GetPixel((ix,iy,iz))*wx*wy*wz
        #print(f"value = {value}")
        #print(f"exp value = {expval}")
        #print(f"norm = {norm}")
        expval/=norm
        #print(f"normalized exp value = {expval}")
        self.assertAlmostEqual(expval,value,places=5)
        self.assertAlmostEqual(expval,value2,places=5)
