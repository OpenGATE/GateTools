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

def _image_size(img):
    # FIXME
    # Why doesn't ITK provide a simple method/function for this very basic query?
    # In SimpleITK it's img.GetSize(), but this method does not seem to exist in normal ITK.
    # Or am I overlooking something in the docs?
    # TODO: the numpy array shape is a tuple. Would it be useful to convert that tuple to a numpy array?
    return itk.GetArrayViewFromImage(img).shape

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
        elif os.path.exists(img):
            input_images.append(itk.imread(img))
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
        if not img_size == size0:
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

def _apply_operation_to_image_list(op,valtype,input_list,output_file=None):
    op_instance=None
    for i,img in enumerate(_image_list(input_list)):
        if op_instance is None:
            imgtype = itk.Image[valtype,img.GetImageDimension()]
            op_instance = op[imgtype,imgtype,imgtype].New()
        op_instance.SetInput(i,img)
    op_instance.Update()
    return _image_output(op_instance.GetOutput(),output_file)

def _apply_operation_to_image_list_v2(op, input_list, output_file=None):
    img_list = _image_list(input_list)
    if len(img_list) == 1:
        return _image_output(img_list[0], output_file)
    np_list = [ itk.GetArrayViewFromImage(img) for img in img_list]
    np_result = reduce(op, np_list)
    img = itk.GetImageFromArray(np_result)
    img.CopyInformation(img_list[0])
    return _image_output(img, output_file)


def image_sum(input_list=[],valtype=itk.F,output_file=None):
    """
    Computes element-wise sum of a list of image with equal geometry.
    """

    # WRONG with more than 2 images
    # creating 'itk.AddImageFilter' when calling that function make it very slow
    #return _apply_operation_to_image_list(itk.AddImageFilter,valtype,input_list,output_file)

    # alternative with np
    # still read *all* images in memory, may lead to memory problem if too large
    return _apply_operation_to_image_list_v2(operator.add, input_list, output_file)

def image_product(input_list=[],output_file=None,valtype=itk.F):
    """
    Computes element-wise product of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(itk.MultiplyImageFilter,valtype,input_list,output_file)

def image_min(input_list=[],output_file=None,valtype=itk.F):
    """
    Computes element-wise minimum of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(itk.MinimumImageFilter,valtype,input_list,output_file)

def image_max(input_list=[],output_file=None,valtype=itk.F):
    """
    Computes element-wise maximum of a list of image with equal geometry.
    """
    return _apply_operation_to_image_list(itk.MaximumImageFilter,valtype,input_list,output_file)

def image_divide(input_list=[], defval=0.,output_file=None):
    """
    Computes element-wise ratio of two images with equal geometry.
    Non-finite values are replaced with defvalue (unless it's None).
    """
    raw_result = _apply_operation_to_image_list(itk.DivideImageFilter,valtype=itk.F,input_list=input_list)
    # FIXME: where do numpy/ITK store the value of the "maximum value that can be respresented with a 32bit float"?
    # FIXME: maybe we should/wish to support integer division as well?
    mask = itk.GetArrayViewFromImage(raw_result)>1e38
    if np.sum(mask)==0:
        return _image_output(raw_result,output_file)
    ratios = itk.GetArrayFromImage(raw_result)
    ratios[mask] = defval
    fixed_result = itk.GetImageFromArray(ratios)
    fixed_result.CopyInformationFrom(raw_result)
    return _image_output(fixed_result,output_file)

#####################################################################################
import unittest
import sys
from datetime import datetime

class Test_Sum(unittest.TestCase):
    def test_two_2D_images(self):
        imgAf = itk.GetImageFromArray(np.arange(4*5,dtype=np.float32).reshape(4,5).copy())
        imgBf = itk.GetImageFromArray(np.arange(4*5,dtype=np.float32)[::-1].reshape(4,5).copy())
        imgCf = image_sum(input_list=[imgAf,imgBf])
        #print("got image with spacing {}".format(imgCf.GetSpacing()))
        index = imgCf.GetLargestPossibleRegion().GetSize() -1
        self.assertTrue( imgCf.GetPixel(index) == 4.*5. -1.)
        #print("at least one pixel is correct.")
        self.assertTrue( np.allclose(itk.GetArrayViewFromImage(imgCf),4.*5.-1) )
        imgAui = itk.GetImageFromArray(np.arange(40*50,dtype=np.uint16).reshape(40,50).copy())
        imgBui = itk.GetImageFromArray(np.arange(40*50,dtype=np.uint16)[::-1].reshape(40,50).copy())
        imgCui = image_sum(input_list=[imgAui,imgBui],valtype=itk.US)
        #print("got image with spacing {}".format(imgCui.GetSpacing()))
        self.assertTrue( (itk.GetArrayViewFromImage(imgCui)==40*50-1).all() )
    def test_two_3D_images(self):
        imgAf = itk.GetImageFromArray(np.arange(3*4*5,dtype=np.float32).reshape(3,4,5).copy())
        imgBf = itk.GetImageFromArray(np.arange(3*4*5,dtype=np.float32)[::-1].reshape(3,4,5).copy())
        imgCf = image_sum(input_list=[imgAf,imgBf])
        index = imgCf.GetLargestPossibleRegion().GetSize() -1
        self.assertTrue( imgCf.GetPixel(index) == 3.*4.*5. -1.)
        imgAui = itk.GetImageFromArray(np.arange(30*40*50,dtype=np.uint16).reshape(30,40,50).copy())
        imgBui = itk.GetImageFromArray(np.arange(30*40*50,dtype=np.uint16)[::-1].reshape(30,40,50).copy())
        imgCui = image_sum(input_list=[imgAui,imgBui],valtype=itk.US)
        #print("got image with spacing {}".format(imgCui.GetSpacing()))
        self.assertTrue( (itk.GetArrayViewFromImage(imgCui)==30*40*50-1).all() )
