#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import logging
import click
import itk
import pydicom
import os
from tqdm import tqdm
logger=logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('filename_struct', type=str, required=True)
@click.argument('filename_img', type=str, required=False)
@click.option('--list_roi', '-l', help='List all ROI names only', is_flag=True)
@click.option('--crop', '-c', help='Crop output mask image', is_flag=True)
@click.option('--roi', '-r', help='Convert the ROI with this name', multiple=True)
@click.option('--output', '-o', help='Output folder for roi image', type=click.Path(file_okay=False, dir_okay=True))
@gt.add_options(gt.common_options)
def gt_dicom_rt_struct_to_image(list_roi, filename_struct, filename_img, roi, crop,verbose,output,logfile):
    '''
    \b
    Convert Dicom RT Struct into mask images

    \b
    <FILENAME_STRUCT> : input DICOM RT STRUCT
    <FILENAME_IMG>    : input ct associated image (mask will have the same size than this image)

    output is the output folder where the roi images are stored. By default, they are saved in the same folder than FILENAME_IMG
    '''

    # logger
    gt.logging_conf(verbose=(verbose or list_roi),logfile=logfile)

    # read dicom struct
    structset = pydicom.dcmread(filename_struct, force=True)

    # print roi names
    roi_names = gt.list_roinames(structset)
    if list_roi:
        s = ' / '.join(roi_names)
        logger.info(s)
        exit(0)

    # filename_img is required (except if list_roi)
    if filename_img == None:
        logger.error('filename_img is required')
        exit(0)

    if len(roi) == 0:
        roi = roi_names

    img = itk.imread(filename_img)
    if output is None:
        base_filename, extension = os.path.splitext(filename_img)
    else:
        base_filename = os.path.abspath(os.path.join(output, "roi"))
        extension = os.path.splitext(filename_img)[1]

    roi_objs=list()
    npbar=0
    pbar = None
    for r in roi:
        try:
            aroi = gt.region_of_interest(structset, r)
            if not aroi.have_mask():
                raise ValueError(f"mask for {r} not possible")
            roi_objs.append(aroi)
            if verbose:
                npbar += aroi.get_ncorners(img)
        except Exception as e:
            logger.error(f"something is wrong with ROI '{r}'")
            roi.remove(r)
    if npbar>0:
        pbar = tqdm(total=npbar, leave=False)
    for roiname,aroi in zip(roi,roi_objs):
        try:
            mask = aroi.get_mask(img, corrected=False,pbar=pbar)
            if crop:
                mask = gt.image_auto_crop(mask, bg=0)
            output_filename = base_filename + '_' + ''.join(e for e in roiname if e.isalnum()) +'.mhd'
            itk.imwrite(mask, output_filename, compression=True)
        except Exception as e:
            tqdm.write(str(e))
    if npbar>0:
        pbar.close()

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_dicom_rt_struct_to_image()
