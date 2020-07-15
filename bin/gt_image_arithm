#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import itk
import click
import sys
import logging
logger=logging.getLogger(__name__)

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.argument('files',
                nargs=-1,
                required=True, # this ensures nargs>=1, but the click docs recommend against it
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
                                writable=False, readable=True, resolve_path=True,
                                allow_dash=False, path_type=None))

@click.option('--operation','-O', help='Operation',
              type=click.Choice(['sum', 'product', 
                                 'divide', 'invert',
                                 'min', 'max', 'absreldiffmax',
                                 'mean', 'std', 'sem']))

@click.option('--scalar','-s', help='scalar for operation', type=float)

@click.option('--output','-o', help='Output filename', required=True,
              type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

@gt.add_options(gt.common_options)
def gt_image_arithm_main(files, operation, scalar, output, **kwargs):
    '''
    Basic pixel-wise (or voxel-wise) arithmetic operations on one or
    more images of the same type and geometry. Currently :
    
    \b
    - sum                          : A + B + C + ...
    - product                      : A * B * C * ...
    - divide                       : A / B / C
    - invert                       : 1 / A / B / C
    - minimum                      : min(A, B, C, ...)
    - maximum                      : max(A, B, C, ...)
    - abs max relative difference  : |A-B|/max(A) (two input images only, not more)
    - mean                         : mean (A+B+C)/n
    - std                          : standard deviation
    - sem                          : standard error mean = std/sqrt(N)

    FILES: the given files are the input for the arithmetic operations
    and will not be modified. Note that the standard ITK python
    bindings do NOT support images with double precision float values.

    SCALAR: when --scalar option is given, creates a constant image
    with this scalar value for all pixels and perform the operation.

    OUTPUT: File path to store the result.

    \b
    Examples:
    \b
    gt_image_arithm -O sum     -o sum.mhd  input1.mhd input2.mhd input3.mhd
    gt_image_arithm -O sum -s 0.2 -o sum.mhd  input1.mhd input2.mhd
    gt_image_arithm -O product -o prod.mhd input1.mhd input2.mhd
    gt_image_arithm -O divide  -o divide.mhd  input1.mhd input2.mhd input3.mhd input4.mhd
    gt_image_arithm -O invert  -o invert.mhd  input1.mhd input2.mhd input3.mhd input4.mhd
    gt_image_arithm -O min     -o min.mhd  input1.mhd input2.mhd input3.mhd
    gt_image_arithm -O max     -o max.mhd  input1.mhd input2.mhd input3.mhd input4.mhd
    gt_image_arithm -O absreldiffmax -o diff.mhd input1.mhd input2.mhd 
    '''

    # logger
    gt.logging_conf(**kwargs)

    try:
        input_images = [itk.imread(fpath) for fpath in files]
    except Exception as ke:
        logger.error("Looks like you are trying to read images of a type that are not supported by the ITK python bindings on your system.")
        logger.error("This Exception was raised by ITK: {}".format(ke))
        logger.error("Sorry!")
        sys.exit(1)
        #raise # the full traceback is scary and uninformative

    if not scalar == None:
        input_images += [scalar]
        
    n = len(input_images)    
    if n == 1 and operation != "invert":
        logger.info("Only one input file => output is equal to input !")
        itk.imwrite(input_images[0], output)
        return
    
    opdict = dict([("sum",gt.image_sum),
                   ("product",gt.image_product),
                   ("min",gt.image_min),
                   ("max",gt.image_max),
                   ("absreldiffmax",gt.image_absolute_relative_difference_max),
                   ("divide",gt.image_divide),
                   ("invert", gt.image_invert),
                   ("mean", gt.image_mean),
                   ("std", gt.image_std),
                   ("sem", gt.image_sem)
    ])

    prefix="\n - "
    logger.info("Compute {} of input files:{}{}".format(operation,prefix,prefix.join(files)))
    logger.info("Output will be written to: {}".format(output))
    try:
        opdict[operation](input_list=input_images,output_file=output)
    except TypeError as te:
        logger.error("Looks like the input files had incompatible types and/or geometries.")
        logger.error("Specifically: '{}'".format(te))
        sys.exit(2)
        #raise # the full traceback is scary and uninformative


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_arithm_main()
