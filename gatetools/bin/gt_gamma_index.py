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
import logging
logger=logging.getLogger(__name__)

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('reference',
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
                                writable=False, readable=True, resolve_path=True,
                                allow_dash=False, path_type=None))
@click.argument('target',
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
                                writable=False, readable=True, resolve_path=True,
                                allow_dash=False, path_type=None))
@click.option('--dd','-d', help=\
'"Dose distance"; you can choose the unit with the --dd-unit/-u option (default is "percent").', default=3.)
@click.option('--ddunit','-u', help=\
'''With "percent" (default), the "Dose distance" value is interpreted as a
percentage.  With "absolute", the "dose distance" value is taken as an absolute
value in the same units as the reference and target images.''',
        default="percent",
        type=click.Choice(["percent","%","absolute","abs"],case_sensitive=False))
@click.option('--dta','-r', help='"Distance To Agreement" [same unit as used for the voxel spacing]', default=3.)
@click.option('--threshold','-T', help='Threshold dose value (exclusive) [same unit as ref/target input files].', default=0.)
@click.option('--defvalue','-D', help='Default value for voxels that are outside of the overlap region with the reference image, or that have dose less than the th.', default=-1.)
@click.option('--output','-o',
              help='Output filename',
              required=True,
              type=click.Path(exists=False, file_okay=False, dir_okay=False,
                              writable=True, readable=False, resolve_path=True,
                              allow_dash=False, path_type=None))
@gt.add_options(gt.common_options)
def gt_gamma_index_main(reference,target,dd,ddunit,dta,threshold,defvalue,output,**kwargs):
    '''
    Compute the gamma index [Daniel Low, 1998] between a reference image and a
    target image.  For every voxel i in the target image, determine the gamma
    value of the reference image voxels j near to it:

    gamma(i,j) = sqrt((dose(i)-dose(j))**2/dref**2 + (pos(i)-pos(i))**2/dta**2)

    where:

    \b
    - dose(i): the dose in voxel i=(ix,iy,iz) in the target image
    - dose(j): the dose in voxel j=(jx,jy,jz) in the reference image
    - pos(i): the position of the voxel i in the target image
    - pos(j): the position of the voxel j in the reference image
    - dref: if `ddunit` is "percent" or "%", then dref=max(refdose)*dd/100.0, otherwise dref=dd.
    
    For every voxel i (with dose greater than the threshold value) in the target image we determine:
    gamma(i) = min(gamma(i,j) | j in ref image).

    For finding the minimum, we do not loop over the entire reference image:
    for each voxel i in the target image we need to search only within a radius
    of dta*abs(dose(i)-dose(jc))/dref, where jc is the index of the voxel in
    the reference image that is closest to i.

    The output image has the same geometry as the input target image. Voxels
    that are located outside of the overlap region of reference and target
    image, as well as voxels that have a dose less or equal to the threshold
    dose (configurable with the -T option), are not checked with the referenced
    and get assigned the "default value". If such unchecked voxels should look
    like "good" voxels, then the "default gamma value" (configurable with the
    -D option) should be set to 0.

    REFERENCE: File path to reference dose image.

    TARGET: File path to target dose image. Dose is assumed to be given in the same units as the reference image.

    Example (2% 2.5mm gamma index with a threshold of 0.2 in the target image):
    
    gate_gamma_index data/tps_dose.mhd result.XYZ/gate-DoseToWater.mhd -o gamma.mhd --dd 2 --dta 2.5 -u "%" -T 0.2
    '''

    # logger
    gt.logging_conf(**kwargs)

    verbose=kwargs["verbose"]
    logfile=kwargs["logfile"]
    logger.debug(f"reference: {reference}")
    logger.debug(f"target: {target}")
    logger.debug(f"dd: {dd}")
    logger.debug(f"ddunit: {ddunit}")
    logger.debug(f"dta: {dta}")
    logger.debug(f"threshold: {threshold}")
    logger.debug(f"defvalue: {defvalue}")
    logger.debug(f"output: {output}")
    logger.debug(f"verbose: {verbose}")
    logger.debug(f"debugging_logfile: '{logfile}'")

    # compute gamma
    ref_img=itk.imread(reference)
    target_img=itk.imread(target)
    ddpercent = (ddunit.lower()=="percent" or ddunit=="%")
    o = gt.get_gamma_index(ref_img,target_img,dd=dd,dta=dta,
                           ddpercent=ddpercent,threshold=threshold,defvalue=defvalue,verbose=verbose)

    # write file
    itk.imwrite(o, output)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_gamma_index_main()
