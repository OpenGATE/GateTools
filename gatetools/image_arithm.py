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
"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import os
import SimpleITK as sitk
from functools import reduce
import operator

def _image_list(input_list):
    """
    Helper function to turn a list of  filenames and/or image objects into a list of image objects.

    Image objects are used as they are, without creating a copy.
    For each valid image filename an image object is created.
    All images with the same size, spacing and origin as the first image are returned as a list.
    Images with incompatible geometry are silently ignored.
    TODO: should we sound the alarm (warnings/errors, raise exceptions) in case of incompatible geometries?
    TODO: discuss policy in case of empty/erroneous input
    """
    output_list=list()
    for img in input_list:
        # TODO: try to implement this with duck typing instead of explicit type checks.
        if type(img)==sitk.SimpleITK.Image:
            output_list.append(img)
        elif type(img)==str and os.path.exists(img):
            output_list.append(sitk.ReadImage(img))
        else:
            raise TypeError("ERROR: {} is not an SimpleITK image object nor a filename".format(img))
    if not output_list:
        raise RuntimeError("got no images")
    # check that they have the same geometry
    origin0 = output_list[0].GetOrigin()
    spacing0 = output_list[0].GetSpacing()
    size0 = output_list[0].GetSize()
    return [ img for img in output_list \
            if np.allclose(img.GetOrigin(),origin0) and \
               np.allclose(img.GetSpacing(),spacing0) and \
               (img.GetSize()==size0) ]

def _image_output(img,filename=None):
    """
    Helper function for optional writing to file of output images.
    """
    if filename is not None:
        sitk.WriteImage(img,filename)
    return img

def image_sum(input_list=[],output_file=None):
    """
    Computes element-wise sum of a list of image with equal geometry.
    """
    return _image_output(reduce(operator.add,_image_list(input_list)),output_file)

def image_product(input_list=[],output_file=None):
    """
    Computes element-wise product of a list of image with equal geometry.
    """
    return _image_output(reduce(operator.mul,_image_list(input_list)),output_file)

def image_min(input_list=[],output_file=None):
    """
    Computes element-wise minimum of a list of image with equal geometry.
    """
    images = _image_list(input_list)
    output_array = sitk.GetArrayFromImage(images[0])
    for img in images[1:]:
        output_array = np.fmin(output_array,sitk.GetArrayFromImage(img))
    output_image = sitk.GetImageFromArray(output_array)
    output_image.CopyInformation(images[0])
    return _image_output(output_image,output_file)

def image_max(input_list=[],output_file=None):
    """
    Computes element-wise maximum of a list of image with equal geometry.
    """
    images = _image_list(input_list)
    output_array = sitk.GetArrayFromImage(images[0])
    for img in images[1:]:
        output_array = np.fmax(output_array,sitk.GetArrayFromImage(img))
    output_image = sitk.GetImageFromArray(output_array)
    output_image.CopyInformation(images[0])
    return _image_output(output_image,output_file)

def image_divide(input1,input2,defval=0.,output_file=None):
    """
    Computes element-wise ratio of two images with equal geometry.
    Non-finite values are replaced with defvalue (unless it's None).
    """
    images = _image_list([input1,input2])
    assert(len(images)==2)
    ratio_img = images[0] / images[1]
    if defval is None:
        return ratio_img
    ratio_array = sitk.GetArrayFromImage(ratio_img)
    mask = np.logical_not( np.isfinite(ratio_array) )
    if mask.any():
        ratio_array[mask] = defval
        ratio_img = sitk.GetImageFromArray(ratio_array)
        ratio_img.CopyInformation(images[0])
    return _image_output(ratio_img,output_file)
