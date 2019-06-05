import numpy as np
import itk

# dref, dtarget maybe scalars or arrays
def reldiff2(dref,dtarget,ddref):
    ddiff=dtarget-dref
    reldd2=(ddiff/ddref)**2
    return reldd2


def gamma_index_3d_equal_geometry(imgref,imgtarget,dtamax,relddmax=None,absddmax=None,defvalue=-1.):
    """
    Compare two equally shaped images, using the gamma index formalism, popular in medical physics.
    ddmax indicates maximum relative dose difference scale (e.g. 0.02 for "2%")
    dtamax indicates maximum "distance to agreement" (in mm)
    defvalue is the gamma value expected for voxels in which the reference value is not positive.
    """
    aref=itk.GetArrayViewFromImage(imgref).swapaxes(0,2)
    atarget=itk.GetArrayViewFromImage(imgtarget).swapaxes(0,2)
    if aref.shape != atarget.shape:
        # print warning/error?
        # raise exception?
        return None
    if not np.allclose(imgref.GetSpacing(),imgtarget.GetSpacing()):
        # print warning/error?
        # raise exception?
        return None
    if not np.allclose(imgref.GetOrigin(),imgtarget.GetOrigin()):
        # print warning/error?
        # raise exception?
        return None
    assert((relddmax is None) ^ (absddmax is None))
    if (relddmax is None):
        ddmax = absddmax
    else:
        ddmax = relddmax*np.max(aref)
    relspacing = np.array(imgref.GetSpacing(),dtype=float)/dtamax
    inv_spacing = np.ones(3,dtype=float)/relspacing
    g00=np.ones(aref.shape,dtype=float)*-1
    mask=aref>0.
    g00[mask]=np.sqrt(reldiff2(aref[mask],atarget[mask],ddmax))
    #print("g00 min=%g, max=%g; %d nonzero gmax" % (np.min(g00),np.max(g00),np.sum(g00>0.0)))
    nx,ny,nz=atarget.shape
    g2=np.zeros((nx,ny,nz),dtype=float)
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if g00[x,y,z] < 0:
                    continue
                igmax=np.round(g00[x,y,z]*inv_spacing).astype(int) # maybe we should use "floor" instead of "round"
                if (igmax==0).all():
                    g2[x,y,z]=g00[x,y,z]**2
                else:
                    ixmin = max(x-igmax[0],0)
                    ixmax = min(x+igmax[0]+1,nx)
                    iymin = max(y-igmax[1],0)
                    iymax = min(y+igmax[1]+1,ny)
                    izmin = max(z-igmax[2],0)
                    izmax = min(z+igmax[2]+1,nz)
                    ix,iy,iz = np.meshgrid(np.arange(ixmin,ixmax),
                                           np.arange(iymin,iymax),
                                           np.arange(izmin,izmax),indexing='ij')
                    g2mesh = reldiff2(aref[ix,iy,iz],atarget[x,y,z],ddmax)
                    g2mesh += ((relspacing[0]*(ix-x)))**2
                    g2mesh += ((relspacing[1]*(iy-y)))**2
                    g2mesh += ((relspacing[2]*(iz-z)))**2
                    g2[x,y,z] = np.min(g2mesh)
                    #DEBUG
                    #if x==1 and y==1 and z==1:
                    #    print("igmax={}".format(igmax))
                    #    print("ix={}".format(ix))
                    #    print("iy={}".format(iy))
                    #    print("iz={}".format(iz))
                    #    print("g2mesh={}".format(g2mesh))
    g=np.sqrt(g2)
    g[np.logical_not(mask)]=defvalue
    gimg=itk.GetImageFromArray(g.swapaxes(0,2))
    gimg.CopyInformation(imgtarget)
    return gimg

def gamma_index_3d_unequal_geometry(imgref,imgtarget,dtamax,relddmax=None,absddmax=None,dmin=0.,defvalue=-1.):
    """
    Compare 3-dimensional arrays with possibly different spacing and different origin, using the
    gamma index formalism, popular in medical physics.
    We assume that the meshes are *NOT* rotated w.r.t. each other.
    ddmax indicates (relative) dose difference scale (e.g. 0.02)
    dtamax indicates distance scale in millimeter (e.g. 3mm)
    refdmin indicates minimum dose value for calculating gamma values
    (voxels with dose<refdmin are skipped, get gamma=0)
    Returns None if the reference and target images have no overlap.
    Returns an image with the same geometry as the target image.
    For all target voxels that are in the overlap region with the refernce image and that have d>dmin,
    a gamma index value is given. For all other voxels the "defvalue" is given.
    """
    # test consistency: both must be 3D
    aref  = itk.GetArrayViewFromImage(imgref).swapaxes(0,2)
    atarget = itk.GetArrayViewFromImage(imgtarget).swapaxes(0,2)
    assert((relddmax is None) ^ (absddmax is None))
    if (relddmax is None):
        ddmax = absddmax
    else:
        ddmax = relddmax*np.max(aref)
    if len(aref.shape) != len(atarget.shape):
        return None
    #bbref  = bounding_box(imgref)
    #bbtarget = bounding_box(imgtarget)
    areforigin = np.array(imgref.GetOrigin())
    arefspacing = np.array(imgref.GetSpacing())
    atargetorigin = np.array(imgtarget.GetOrigin())
    atargetspacing = np.array(imgtarget.GetSpacing())
    nx,ny,nz = atarget.shape
    mx,my,mz = aref.shape
    dtamax2  = dtamax**2
    mask     = atarget>dmin
    # now define the indices of the target image voxel centers
    ixtarget, iytarget, iztarget = np.meshgrid(np.arange(nx),np.arange(ny),np.arange(nz),indexing='ij')
    xtarget = atargetorigin[0]+ixtarget*atargetspacing[0]
    ytarget = atargetorigin[1]+iytarget*atargetspacing[1]
    ztarget = atargetorigin[2]+iztarget*atargetspacing[2]
    # indices ref image voxel centers that are closest to the target image voxel centers
    ixref = np.round((xtarget-areforigin[0])/arefspacing[0]).astype(int)
    iyref = np.round((ytarget-areforigin[1])/arefspacing[1]).astype(int)
    izref = np.round((ztarget-areforigin[2])/arefspacing[2]).astype(int)
    # keep withing range
    mask *= (ixref>=0)
    mask *= (iyref>=0)
    mask *= (izref>=0)
    mask *= (ixref<mx)
    mask *= (iyref<my)
    mask *= (izref<mz)
    if np.sum(mask)==0:
        return None
    # grid of "close points" in reference image
    xref = areforigin[0]+ixref*arefspacing[0]
    yref = areforigin[1]+iyref*arefspacing[1]
    zref = areforigin[2]+izref*arefspacing[2]
    # a grid of corresponding x,y,z mesh coordinates
    #xrefmeshgrid, yrefmeshgrid, zrefmeshgrid = np.meshgrid(xref,yref,zref,indexing='ij')
    # get a gamma value on this closest point
    gclose2 = np.zeros([nx,ny,nz],dtype=float)
    gclose2[mask] = reldiff2(aref[ixref[mask],iyref[mask],izref[mask]],atarget[mask],ddmax) + \
                                              ((xtarget[mask]-xref[mask])**2 + \
                                               (ytarget[mask]-yref[mask])**2 + \
                                               (ztarget[mask]-zref[mask])**2)/dtamax2
    gclose = np.array(np.sqrt(gclose2))
    #igclose = np.array(np.ceil(np.sqrt(gclose2)),dtype=int)
    g2=np.zeros([nx,ny,nz],dtype=float)
    #print("going to loop over {} voxels with large enough dose in reference image".format(np.sum(mask)))
    for mixref,miyref,mizref,mixtarget,miytarget,miztarget,mgclose in zip(ixref[mask], iyref[mask], izref[mask],
                                                                    ixtarget[mask],iytarget[mask],iztarget[mask],gclose[mask]):
        #dtarget = atarget[mixtarget,miytarget,miztarget]
        #dref = aref[mixref,miyref,mizref]
        ixyztarget = np.array((mixtarget,miytarget,miztarget))
        ixyzref = np.array((mixref,miyref,mizref))
        targetpos = atargetorigin + ixyztarget*atargetspacing
        refpos = areforigin  + ixyzref*arefspacing
        dixyz = np.floor(mgclose*dtamax/arefspacing).astype(int) # or round, or ceil?
        imax = np.minimum(ixyzref+dixyz+1,(mx,my,mz))
        imin = np.maximum(ixyzref-dixyz  ,( 0, 0, 0))
        mixnear,miynear,miznear = np.meshgrid(np.arange(imin[0],imax[0]),np.arange(imin[1],imax[1]),np.arange(imin[2],imax[2]),indexing='ij')
        g2near  = reldiff2(aref[mixnear,miynear,miznear],atarget[mixtarget,miytarget,miztarget],ddmax)
        g2near += (areforigin[0]+mixnear*arefspacing[0]-targetpos[0])**2/dtamax2
        g2near += (areforigin[1]+miynear*arefspacing[1]-targetpos[1])**2/dtamax2
        g2near += (areforigin[2]+miznear*arefspacing[2]-targetpos[2])**2/dtamax2
        g2[mixtarget,miytarget,miztarget] = np.min(g2near)
    g=np.sqrt(g2)
    g[np.logical_not(mask)]=defvalue
    gimg=itk.GetImageFromArray(g.swapaxes(0,2))
    gimg.CopyInformation(imgtarget)
    return gimg

#####################################################################################
import unittest
import sys
from datetime import datetime

class Test_GammaIndex3dIdenticalMesh(unittest.TestCase):
    def test_identity(self):
        # two identical images should give gamma=0.0 in all voxels
        #print("test identity")
        np.random.seed(1234567)
        a_rnd = np.random.uniform(0.,10.,(4,5,6))
        img1 = itk.GetImageFromArray(a_rnd)
        img2 = itk.GetImageFromArray(a_rnd)
        img_gamma = gamma_index_3d_equal_geometry(img1,img2,relddmax=0.03,dtamax=2.0)
        self.assertTrue( (itk.GetArrayViewFromImage(img_gamma) == 0.).all())
        #print("DONE test identity")
    def test_scaling_small(self):
        #print("test scaling small")
        # two images identical up to a scaling factor 1.03 should give gamma(3%)<=1.0 in all voxels
        np.random.seed(1234567)
        a_rnd = np.random.uniform(0.,10.,(4,5,6))
        img1 = itk.GetImageFromArray(a_rnd)
        img2 = itk.GetImageFromArray(1.03*a_rnd)
        img_gamma = gamma_index_3d_equal_geometry(img1,img2,relddmax=0.03,dtamax=2.0)
        self.assertTrue( (itk.GetArrayViewFromImage(img_gamma) < 1.0001).all())
        #print("DONE test scaling small")
    def test_scaling_large(self):
        #print("test scaling large")
        # two images identical up to a scaling factor 1.03 should give gamma(3%)<=1.0 in all voxels
        a_rnd = np.ones((4,5,6),dtype=float)
        img1 = itk.GetImageFromArray(a_rnd)
        img2 = itk.GetImageFromArray(1.03*a_rnd)
        img_gamma = gamma_index_3d_equal_geometry(img1,img2,relddmax=0.02,dtamax=2.0)
        #print("gamma value in 1,1,1: {}".format(img_gamma[1,1,1]))
        # allow for rounding errors, in some voxels we may have 1.000000001 or somesuch
        self.assertTrue( np.allclose(itk.GetArrayViewFromImage(img_gamma),1.5) )
        #print("DONE test scaling large")
    def test_checkerboards(self):
        #print("test 3D checkerboards: have D=0.25 in even voxels and D=0.75 in odd voxels for ref image, vice versa for test image.")
        #for every voxel in the test image, the neighboring voxels in the ref image has the same dose
        #therefore the gamma index should be equal to spacing/dtamax for all voxels.
        nx,ny,nz=4,5,6
        ix,iy,iz = np.meshgrid(np.arange(nx,dtype=int),np.arange(ny,dtype=int),np.arange(nz,dtype=int),indexing='ij')
        a_odd  = 0.5*(((ix+iy+iz) % 2) == 1).astype(float)+0.25
        a_even = 0.5*(((ix+iy+iz) % 2) == 0).astype(float)+0.25
        img_odd = itk.GetImageFromArray(a_odd)
        img_even = itk.GetImageFromArray(a_even)
        img_gamma_even_odd = gamma_index_3d_equal_geometry(img_even,img_odd,relddmax=0.1,dtamax=2.)
        img_gamma_odd_even = gamma_index_3d_equal_geometry(img_odd,img_even,relddmax=0.1,dtamax=2.)
        self.assertTrue(np.allclose(itk.GetArrayViewFromImage(img_gamma_odd_even),itk.GetArrayViewFromImage(img_gamma_even_odd)))
        self.assertTrue(np.allclose(itk.GetArrayViewFromImage(img_gamma_odd_even),0.5))
        #print("DONE test checkerboards")
    def test_large_image(self):
        #for N in [1,2,5,10,20,50,100]:
        for N in [1,2,5,10,20]:
            tgen = datetime.now()
            img_ref = itk.GetImageFromArray(np.ones((N,N,N),dtype=float))
            img_target = itk.GetImageFromArray(np.random.normal(1.,0.02,(N,N,N)))
            tbefore = datetime.now()
            print("{}^3 voxels generating images took {}".format(N,tbefore-tgen))
            img_NNN_gamma = gamma_index_3d_equal_geometry(img_ref,img_target,relddmax=0.02,dtamax=2.0)
            tafter = datetime.now()
            print("{}^3 voxels calculating gamma took {}".format(N,tafter-tbefore))

class Test_GammaIndex3dUnequalMesh(unittest.TestCase):
    def test_EqualMesh(self):
        #for equal meshes, the "unequalmesh" implementation should give the same results as "equal mesh" implementation.
        np.random.seed(71234567)
        nxyz=(24,25,26)
        oxyz=(1.4,1.5,1.6)
        img_ref = itk.GetImageFromArray(np.ones(nxyz,dtype=float))
        img_ref.SetSpacing(oxyz)
        for i in range(10):
            img_target = itk.GetImageFromArray(np.random.normal(1.,0.05,nxyz))
            img_target.SetSpacing(oxyz)
            t0 = datetime.now()
            img_gamma_equal = gamma_index_3d_equal_geometry(img_ref,img_target,relddmax=0.03,dtamax=2.0)
            t1 = datetime.now()
            print("{}. equal implementation took {}".format(i,t1-t0))
            img_gamma_unequal = gamma_index_3d_unequal_geometry(img_ref,img_target,relddmax=0.03,dtamax=2.0)
            t2 = datetime.now()
            print("{}. unequal implementation took {}".format(i,t2-t1))
            aeq = itk.GetArrayViewFromImage(img_gamma_equal)
            auneq = itk.GetArrayViewFromImage(img_gamma_unequal)
            self.assertTrue( np.allclose(aeq,auneq) )
            #self.assertTrue( np.allclose(itk.GetArrayViewFromImage(img_gamma_equal),itk.GetArrayViewFromImage(img_gamma_unequal)))
            #print("Yay! min/median/mean/max={}/{}/{}/{}".format(np.min(aeq),np.median(aeq),np.mean(aeq),np.max(aeq)))
    def test_scaling_small(self):
        #print("test scaling small")
        # two images identical up to a scaling factor 1.03 should give gamma(3%)<=1.0 in all voxels
        np.random.seed(1234567)
        a_rnd = np.random.uniform(0.,10.,(4,5,6))
        img1 = itk.GetImageFromArray(a_rnd)
        img2 = itk.GetImageFromArray(1.03*a_rnd)
        img_gamma = gamma_index_3d_unequal_geometry(img1,img2,relddmax=0.03,dtamax=2.0)
        self.assertTrue( (itk.GetArrayViewFromImage(img_gamma) < 1.0001).all())
        #print("DONE test scaling small")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()

# vim: set et ts=4 ai sw=4:
