# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module provides basic arithmatic image operations for ITK images, e.g. dose distributions computed with GATE:
    Two or more images:
    0. img1+img2+...
    1. img1*img2*...
    2. img1/img2
    3. max(img1,img2,...)
    4. min(img1,img2,...)
    5. abs_diff(img1,img2)
    6. squared_diff(img1,img2)
    7. diff(img1,img2)
    8. rel_diff(img1,img2)
    One images and an optional scalar:
    0. img + offset
    1. img * scalar
    2. 1./img
    3. max(img)
    4. min(img)
    5. abs(img)
    6. squareval(img)
    7. ln(img)
    8. exp(img)
    9. sqrt(img)
    10. EPID(img)
    11. img / scalar
    12. normalize(img) (divide by max)
    13. -ln(img/I0)
    Some of these operations are quite directly possible with SimpleITK, for
    instance the image objects in SimpleITK have a 'plus' operator defined, so
    that you can literally write imgsum = img1+img1, which will do what you
    expect when the images are geometrically compatible, and raise an exception
    otherwise. We are using directly using the ITK python bindings, which do
    not seem to have this nifty feature, so we are providing it here.
"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import os
import itk
import numpy as np
from functools import reduce
import operator
import ctypes # needed for definition of "unsigned long", as np.uint32 is not recognized as such
import logging
logger=logging.getLogger(__name__)

def _image_size(img):
    # FIXME
    # Why doesn't ITK provide a simple method/function for this very basic query?
    # In SimpleITK it's img.GetSize(), but this method does not seem to exist in normal ITK.
    # Or am I overlooking something in the docs?
    # TODO: the numpy array shape is a tuple. Would it be useful to convert that tuple to a numpy array?
    return img.GetLargestPossibleRegion().GetSize()

def _image_list(input_list):
    """
    Helper function to turn a list of  filenames and/or image objects into a list of image objects.

    Image objects are used as they are, without creating a copy.
    For each valid image filename an image object is created.
    All images with the same size, spacing and origin as the first image are returned as a list.
    Images with incompatible geometry are silently ignored.
    TODO: should we sound the alarm (warnings/errors, raise exceptions) in case of incompatible geometries?
    TODO: discuss policy in case of empty/erroneous input
    TODO: is a 'TypeError' the correct exception to raise in case of incompatible image types, or should it be InputError?
    """
    input_images=list()
    for img in input_list:
        if hasattr(img,"GetSpacing") and hasattr(img,"GetOrigin"):
            # semi-duck-typing
            input_images.append(img)
        elif isinstance(img, str) and os.path.exists(img):
            input_images.append(itk.imread(img))
        elif (not hasattr(img, 'len')) and (not isinstance(img, str)):
            if not input_images:
              raise RuntimeError("Pass an image before a scalar to have a model")
            duplicator = itk.ImageDuplicator.New(input_images[0])
            duplicator.Update()
            InputType = type(input_images[0])
            input_dimension = input_images[0].GetImageDimension()
            OutputType = itk.Image[itk.F, input_dimension]
            castFilter = itk.CastImageFilter[InputType, OutputType].New()
            castFilter.SetInput(duplicator.GetOutput())
            castFilter.Update()
            scalarImage = castFilter.GetOutput()
            scalarImage.FillBuffer(img)
            input_images += [scalarImage]
        else:
            raise TypeError("ERROR: {} is not an ITK image object nor a path to an existing image file".format(img))
    if not input_images:
        raise RuntimeError("got no images")
    # check that they have the same geometry
    checked_images=list()
    origin0 = input_images[0].GetOrigin()
    spacing0 = input_images[0].GetSpacing()
    size0 = _image_size(input_images[0])
    for img in input_images:
        img_size = _image_size(img)
        if not np.allclose(img_size, size0):
            raise TypeError("images have incompatible size: {} versus {}".format(size0,img_size))
        elif not np.allclose(img.GetOrigin(),origin0):
            raise TypeError("images have incompatible origins: {} versus {}".format(origin0,img.GetOrigin()))
        elif not np.allclose(img.GetSpacing(),spacing0):
            raise TypeError("images have incompatible {} spacing: {} versus {}".format(
                "pixel" if len(spacing0)==2 else "voxel",spacing0,img.GetSpacing()))
        else:
            # TODO: maybe we should also check pixel types?
            checked_images.append(img)
    return checked_images

def _image_output(img,filename=None):
    """
    Helper function for optional writing to file of output images.
    """
    if filename is not None:
        itk.imwrite(img,filename)
    return img

def _apply_operation_to_image_list(op, input_list, output_file=None):
    img_list = _image_list(input_list)
    if len(img_list) == 1:
        return _image_output(img_list[0], output_file)
    np_list = [ itk.array_view_from_image(img) for img in img_list]
    np_result = reduce(op, np_list)
    img = itk.image_from_array(np_result)
    img.CopyInformation(img_list[0])
    return _image_output(img, output_file)


def image_sum(input_list=[],output_file=None):
    """
    Computes element-wise sum of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(operator.add,input_list,output_file)


def image_mean(input_list=[],output_file=None):
    """
    Computes element-wise mean of a list of image with equal geometry.
    """
    img_list = _image_list(input_list)
    if len(img_list) == 1:
        return _image_output(img_list[0], output_file)
    np_list = [ itk.array_view_from_image(img) for img in img_list]
    np_result = np.mean(np_list, axis=0)
    img = itk.image_from_array(np_result)
    img.CopyInformation(img_list[0])
    return _image_output(img, output_file)
    

def image_std(input_list=[],output_file=None):
    """
    Computes element-wise standard deviation of a list of image with equal geometry.
    """
    img_list = _image_list(input_list)
    if len(img_list) == 1:
        return _image_output(img_list[0], output_file)
    np_list = [ itk.array_view_from_image(img) for img in img_list]
    np_result = np.std(np_list, axis=0)
    img = itk.image_from_array(np_result)
    img.CopyInformation(img_list[0])
    return _image_output(img, output_file)

def image_sem(input_list=[],output_file=None):
    """
    Computes element-wise standard deviation of a list of image with equal geometry.
    """
    img_list = _image_list(input_list)
    if len(img_list) == 1:
        return _image_output(img_list[0], output_file)
    np_list = [ itk.array_view_from_image(img) for img in img_list]
    N = len(img_list)
    np_result = np.std(np_list, axis=0)/np.sqrt(N)
    img = itk.image_from_array(np_result)
    img.CopyInformation(img_list[0])
    return _image_output(img, output_file)
    

def image_product(input_list=[],output_file=None):
    """
    Computes element-wise product of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(operator.mul,input_list,output_file)

def image_min(input_list=[],output_file=None):
    """
    Computes element-wise minimum of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(np.minimum,input_list,output_file)

def image_max(input_list=[],output_file=None):
    """
    Computes element-wise maximum of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(np.maximum,input_list,output_file)

def image_divide(input_list=[], defval=0.,output_file=None):
    """
    Computes element-wise ratio of two images with equal geometry.
    Non-finite values are replaced with defvalue (unless it's None).
    """
    np.seterr(divide='ignore', invalid='ignore')
    raw_result = _apply_operation_to_image_list(operator.truediv,input_list=input_list)
    # FIXME: where do numpy/ITK store the value of the "maximum value that can be respresented with a 32bit float"?
    # FIXME: maybe we should/wish to support integer division as well?
    mask = itk.array_view_from_image(raw_result)>1e38
    if np.sum(mask)==0:
        return _image_output(raw_result,output_file)
    ratios = itk.array_from_image(raw_result)
    ratios[mask] = defval
    fixed_result = itk.image_from_array(ratios)
    fixed_result.CopyInformation(raw_result)
    return _image_output(fixed_result,output_file)

def image_absolute_relative_difference_max(input_list=[], defval=0.,output_file=None):
    """    
    Computes element-wise absolute relative difference (|A-B|)/max(A) of
    two images with equal geometry.  Non-finite values are replaced
    with defvalue (unless it's None).    
    """

    if len(input_list) != 2:
        raise RuntimeError("Two images must be provided to reldiff operator")

    img_list = _image_list(input_list)
    np_list = [ itk.array_view_from_image(img) for img in img_list]
    np_1 = np_list[0]
    np_2 = np_list[1]
    m = np.max(np_1)
    np_result = np.divide((np.abs(np_1-np_2)), m, out=np.zeros_like(np_1), where=np_1 != 0)
    img = itk.image_from_array(np_result)
    img.CopyInformation(img_list[0])
    return _image_output(img, output_file)

def image_invert(input_list=[],output_file=None):
    """
    Computes element-wise invert of a list of image with equal geometry.
    Add image with ones at the beginning of the list and use the division
    """
    duplicator = itk.ImageDuplicator.New(input_list[0])
    duplicator.Update()
    InputType = type(input_list[0])
    input_dimension = input_list[0].GetImageDimension()
    OutputType = itk.Image[itk.F, input_dimension]
    castFilter = itk.CastImageFilter[InputType, OutputType].New()
    castFilter.SetInput(duplicator.GetOutput())
    castFilter.Update()
    scalarImage = castFilter.GetOutput()
    scalarImage.FillBuffer(1.0)
    input_list = [scalarImage] + input_list
    return image_divide(input_list=input_list,output_file=output_file)


#####################################################################################
import unittest
import sys
from datetime import datetime
from .logging_conf import LoggedTestCase

class Test_Sum(LoggedTestCase):
    def test_five_2D_images(self):
        logger.info('Test_Sum test_five_2D_images')
        nx,ny = 4,5
        hundred = 100
        thousand = 1000
        spacing = (42.,24.)
        origin = (4242.,2424.)
        # float images
        imglistF = [ itk.image_from_array(np.arange(nx*ny,dtype=np.float32).reshape(nx,ny).copy()),
                     itk.image_from_array(np.arange(nx*ny,dtype=np.float32)[::-1].reshape(nx,ny).copy()),
                     itk.image_from_array(np.arange(0,nx*ny*hundred,hundred,dtype=np.float32).reshape(nx,ny).copy()),
                     itk.image_from_array(np.arange(0,nx*ny*hundred,hundred,dtype=np.float32)[::-1].reshape(4,5).copy()),
                     itk.image_from_array(thousand*np.ones((nx,ny),dtype=np.float32)) ]
        for imgF in imglistF:
            imgF.SetSpacing( spacing )
            imgF.SetOrigin( origin )
        imgsumF = image_sum(input_list=imglistF)
        logger.debug("got image with spacing {}".format(imgsumF.GetSpacing()))
        index = imgsumF.GetLargestPossibleRegion().GetSize() -1
        logger.debug("get sum value {} while expecting {}".format(imgsumF.GetPixel(index),4.*5. -1.))
        self.assertTrue( np.allclose(itk.array_view_from_image(imgsumF),nx*ny-1.+(nx*ny-1.)*hundred +thousand) ) # floats: approximate equality
        self.assertTrue( itk.array_from_image(imgsumF).shape == (nx,ny))
        self.assertTrue( np.allclose(imgsumF.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgsumF.GetOrigin(),origin))
        # unsigned short int images ("US" in itk lingo)
        nx,ny = 40,50
        ten = 10
        thirteen = 13
        spacing = (32.,23.)
        origin = (3232.,2323.)
        imglistUS = [ itk.image_from_array(np.arange(nx*ny,dtype=np.uint16).reshape(nx,ny).copy()),
                      itk.image_from_array(np.arange(nx*ny,dtype=np.uint16)[::-1].reshape(nx,ny).copy()),
                      itk.image_from_array(np.arange(0,ten*nx*ny,ten,dtype=np.uint16).reshape(nx,ny).copy()),
                      itk.image_from_array(np.arange(0,ten*nx*ny,ten,dtype=np.uint16)[::-1].reshape(nx,ny).copy()),
                      itk.image_from_array(thirteen*np.ones((nx,ny),dtype=np.uint16)) ]
        for imgUS in imglistUS:
            imgUS.SetSpacing( spacing )
            imgUS.SetOrigin( origin )
        imgsumUS = image_sum(input_list=imglistUS)
        logger.debug("got image with spacing {}".format(imgsumUS.GetSpacing()))
        logger.debug("get sum value {} while expecting {}".format(imgsumUS.GetPixel(index),40*50-1+10*40*50-10+13))
        self.assertTrue( (itk.array_view_from_image(imgsumUS)==nx*ny-1+ten*nx*ny-ten+thirteen).all() ) # ints: exact equality
        self.assertTrue( itk.array_from_image(imgsumUS).shape == (nx,ny))
        self.assertTrue( np.allclose(imgsumUS.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgsumUS.GetOrigin(),origin))
    def test_five_3D_images_and_scalar(self):
        logger.info('Test_Sum test_five_3D_images_and_scalar')
        nx,ny,nz = 3,4,5
        hundred = 100
        thirteen = 13.333
        spacing = (421.,214.,142.)
        origin = (421421.,214214.,142142.)
        # float images
        imglistF = [ itk.image_from_array(        np.arange(nx*ny*nz,dtype=np.float32).reshape(nx,ny,nz).copy()),
                     itk.image_from_array(        np.arange(nx*ny*nz,dtype=np.float32)[::-1].reshape(nx,ny,nz).copy()),
                     itk.image_from_array(hundred*np.arange(nx*ny*nz,dtype=np.float32).reshape(nx,ny,nz).copy()),
                     itk.image_from_array(hundred*np.arange(nx*ny*nz,dtype=np.float32)[::-1].reshape(nx,ny,nz).copy()),
                     itk.image_from_array(thirteen*np.ones((nx,ny,nz),dtype=np.float32)) ]
        for imgF in imglistF:
            imgF.SetSpacing( spacing )
            imgF.SetOrigin( origin )
        imglistF = imglistF[:-1] + [42.0, imglistF[-1]]
        imgsumF = image_sum(input_list=imglistF)
        index = imgsumF.GetLargestPossibleRegion().GetSize() -1
        self.assertTrue( np.allclose(itk.array_from_image(imgsumF),(hundred+1)*(nx*ny*nz -1.)+thirteen+42.0))
        self.assertTrue( np.allclose(imgsumF.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgsumF.GetOrigin(),origin))
        # unsigned short int images ("US" in itk lingo)
        nx,ny,nz = 30,40,50
        thirteen = 13
        spacing = (321.,213.,132.)
        origin = (321321.,213213.,132132.)
        imglistUS = [ itk.image_from_array( np.arange(nx*ny*nz,dtype=np.uint16).reshape(nx,ny,nz).copy()),
                      itk.image_from_array( np.arange(nx*ny*nz,dtype=np.uint16)[::-1].reshape(nx,ny,nz).copy()),
                      itk.image_from_array((np.arange(nx*ny*nz,dtype=np.uint16)%nz).reshape(nx,ny,nz).copy()),
                      itk.image_from_array((np.arange(nx*ny*nz,dtype=np.uint16)[::-1]%nz).reshape(nx,ny,nz).copy()),
                      itk.image_from_array(thirteen*np.ones((nx,ny,nz),dtype=np.uint16)) ]
        for imgUS in imglistUS:
            imgUS.SetSpacing( spacing )
            imgUS.SetOrigin( origin )
        imgsumUS = image_sum(input_list=imglistUS)
        logger.debug("got sum image with spacing {}".format(imgsumUS.GetSpacing()))
        self.assertTrue( (itk.array_view_from_image(imgsumUS)==nx*ny*nz-1+nz-1+thirteen).all() )
        self.assertTrue( np.allclose(imgsumUS.GetSpacing(),spacing) )
        self.assertTrue( np.allclose(imgsumUS.GetOrigin(),origin) )
        self.assertTrue( itk.array_from_image(imgsumUS).shape == (nx,ny,nz))

class Test_Product(LoggedTestCase):
    # TODO: also test correct behavior in case of NAN, zero, etc
    def test_three_float_3D_images(self):
        logger.info('Test_Product test_three_float_3D_images')
        nx,ny,nz = 2,3,4
        minlog,maxlog=-5.,5.
        spacing = (421.,214.,142.)
        origin = (421421.,214214.,142142.)
        thirteen = 13.333
        imglistF = [ itk.image_from_array(np.logspace(minlog,maxlog,nx*ny*nz).reshape(nx,ny,nz).astype(np.float32)),
                     itk.image_from_array(np.logspace(minlog,maxlog,nx*ny*nz)[::-1].reshape(nx,ny,nz).astype(np.float32)),
                     itk.image_from_array(thirteen*np.ones((nx,ny,nz),dtype=np.float32)) ]
        for imgF in imglistF:
            imgF.SetSpacing(spacing)
            imgF.SetOrigin(origin)
        imgprodF = image_product(input_list=imglistF)
        self.assertTrue( np.allclose(itk.array_from_image(imgprodF),thirteen))
        self.assertTrue( itk.array_from_image(imgprodF).shape == (nx,ny,nz))
        self.assertTrue( np.allclose(imgprodF.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgprodF.GetOrigin(),origin))
        self.assertTrue( type(imgprodF) == itk.Image[itk.F,3])
    def test_five_int_3D_images(self):
        logger.info('Test_Product test_five_int_3D_images')
        nx,ny,nz = 30,40,50
        spacing = (321.,213.,132.)
        origin = (321321.,213213.,132132.)
        pval=np.ones(5)/5.0
        p2=np.random.multinomial(1,pval,(nz,nx,ny)).swapaxes(0,3).copy()
        p3=np.random.multinomial(2,pval,(nz,nx,ny)).swapaxes(0,3).copy()
        p7=np.random.multinomial(2,pval,(nz,nx,ny)).swapaxes(0,3).copy()
        p13=np.random.multinomial(1,pval,(nz,nx,ny)).swapaxes(0,3).copy()
        p37=np.random.multinomial(1,pval,(nz,nx,ny)).swapaxes(0,3).copy()
        a0,a1,a2,a3,a4 = 2**p2*3**p3*7**p7*13**p13*37**p37
        imglist = list()
        for a in (a0,a1,a2,a3,a4):
            img = itk.image_from_array(a.astype(ctypes.c_ulong))
            img.SetSpacing( spacing )
            img.SetOrigin( origin )
            imglist.append(img)
        imgprodUS = image_product(input_list=imglist)
        answer = 424242
        self.assertTrue( type(imgprodUS) == itk.Image[itk.UL,3])
        self.assertTrue( (itk.array_from_image(imgprodUS) == answer).all() )
        self.assertTrue( itk.array_from_image(imgprodUS).shape == (nx,ny,nz))
        self.assertTrue( np.allclose(imgprodUS.GetSpacing(),spacing) )
        self.assertTrue( np.allclose(imgprodUS.GetOrigin(),origin) )

class Test_MinMax(LoggedTestCase):
    def test_eight_3D_images(self):
        logger.info('Test_MinMax test_eight_3D_images')
        nx,ny,nz = 30,40,50
        dmin,dmax = np.float32(-20.5), np.float32(31230.5)
        spacing = (321.,213.,132.)
        origin = (321321.,213213.,132132.)
        alist = [ np.random.uniform(dmin,dmax,nx*ny*nz).astype(np.float32) for i in range(8)]
        indices = np.arange(nx*ny*nz,dtype=np.uint32)
        imglist=list()
        for (j,a) in enumerate(alist):
            a[indices%8 == j] = dmin
            a[indices%8 == (j+4)%8] = dmax
            img=itk.image_from_array(a.reshape(nx,ny,nz).copy())
            img.SetSpacing(spacing)
            img.SetOrigin(origin)
            imglist.append(img)
        imgmin = image_min(imglist)
        imgmax = image_max(imglist)
        self.assertTrue( type(imgmin) == itk.Image[itk.F,3])
        self.assertTrue( type(imgmax) == itk.Image[itk.F,3])
        self.assertTrue( np.allclose(itk.array_from_image(imgmin),dmin))
        self.assertTrue( np.allclose(itk.array_from_image(imgmax),dmax))
        self.assertTrue( np.allclose(imgmin.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgmax.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgmin.GetOrigin(),origin))
        self.assertTrue( np.allclose(imgmax.GetOrigin(),origin))

class Test_Divide(LoggedTestCase):
    def test_three_3D_images(self):
        logger.info('Test_Divide test_nine_3D_images')
        nx,ny,nz = 30,40,50
        spacing = (321.,213.,132.)
        origin = (321321.,213213.,132132.)
        imgList = [ itk.image_from_array(5.0 * np.ones((nx, ny, nz), dtype=np.float32)),
                    itk.image_from_array(2.0 * np.ones((nx, ny, nz), dtype=np.float32)),
                    itk.image_from_array(2.5 * np.ones((nx, ny, nz), dtype=np.float32))]
        for img in imgList:
            img.SetSpacing(spacing)
            img.SetOrigin(origin)
        imgdivide = image_divide(input_list=imgList)
        self.assertTrue( type(imgdivide) == itk.Image[itk.F,3])
        self.assertTrue( np.allclose(itk.array_from_image(imgdivide),1.0))
        self.assertTrue( np.allclose(imgdivide.GetSpacing(),spacing))
        self.assertTrue( np.allclose(imgdivide.GetOrigin(),origin))

class Test_Invert(LoggedTestCase):
    def test_three_3D_images(self):
        logger.info('Test_Invert test_ten_3D_images')
        nx, ny, nz = 30, 40, 50
        spacing = (321., 213., 132.)
        origin = (321321., 213213., 132132.)
        imgList = [itk.image_from_array(5.0 * np.ones((nx, ny, nz), dtype=np.float32)),
                   itk.image_from_array(2.0 * np.ones((nx, ny, nz), dtype=np.float32)),
                   itk.image_from_array(2.5 * np.ones((nx, ny, nz), dtype=np.float32))]
        for img in imgList:
            img.SetSpacing(spacing)
            img.SetOrigin(origin)
        imginvert = image_invert(input_list=imgList)
        self.assertTrue(type(imginvert) == itk.Image[itk.F, 3])
        self.assertTrue(np.allclose(itk.array_from_image(imginvert), 0.04))
        self.assertTrue(np.allclose(imginvert.GetSpacing(), spacing))
        self.assertTrue(np.allclose(imginvert.GetOrigin(), origin))


# TODO: test division
