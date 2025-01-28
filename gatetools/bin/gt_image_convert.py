#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import click
import itk
import os
import logging
logger=logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-o', '--output', type=str, required=True, help='Output image name')
@click.option('-p', '--pixeltype', type=str, help='Pixel type conversion')
@click.option('-f', '--flip', is_flag=True, help='If a negative spacing is present in 3D Dicom tags, flip the image to have a positive spacing and identity matrix')
@click.option('-an', '--accessionnumber', is_flag=True, help='For dicoms with multiple accession number, create a 4D image')
@click.argument('input', type=str, required=True, nargs=-1)
@gt.add_options(gt.common_options)
def gt_image_convert(input, output, pixeltype, flip, accessionnumber, **kwargs):
    '''
    Convert the input to the output with pixeltype. If pixeltype is
    not set, the output has the same pixel type than the input.

    Available formats: (2D) .bmp .jpeg .png, (3D) .mhd .nii .nhdr .nrrd .tiff

    Available pixel types: unsigned char, short, unsigned short, float

    To convert Dicom to another format, set the folder fullpath
    containing the .dcm files as input, eg:

       ~/path/to/dcm/*dcm
       or
       ~/path/to/dcm/toto.dcm
    If a negative spacing is present in the dicom tag, you can set the flag flip to save the same image but without this negative spacing along z axis. The coordinates are preserved with this flip.
    The series are automatically separated and the duplicated slices (based on sopInstanceUID) are removed.
    '''

    # logger
    gt.logging_conf(**kwargs)

    #Check if input is available
    for inputFile in input:
        if not os.path.isfile(inputFile):
            logger.error('no existing input: ' + inputFile)
            return

    #Read input
    inputImages = []
    if len(input) == 1 and not (input[0].endswith(".dcm") or input[0].endswith(".IMA")):
        logger.info(f'Reading input image with itk {input[0]}')
        inputImages.append(itk.imread(input[0]))
    else:
        series = gt.separate_series(input)
        series = gt.separate_sequenceName_series(series)
        if accessionnumber:
            series = gt.separate_accessionNumber_series(series)
        for serie in series.keys():
            if len(series[serie]) > 1:
                logger.info(f'Reading input dicom {len(series[serie])} input files')
                inputImages.append(gt.read_dicom(series[serie]))
            elif len(series[serie]) == 1 and (series[serie][0].endswith(".dcm") or series[serie][0].endswith(".IMA")):
                logger.info(f'Reading input 3D dicom {series[serie][0]}')
                inputImages.append(gt.read_3d_dicom(series[serie], flip))
            else:
                logger.error('no input available')
                return

    if len(inputImages) > 1:
        logger.info(f'Warning: more than one serie found')
    for indexImage, inputImage in enumerate(inputImages):
        if inputImage == None:
            logger.error('no image available')
            return

        # convert image
        if pixeltype != None:
            logger.info(f'Convert pixel type to {pixeltype}')
        outputImage = gt.image_convert(inputImage, pixeltype)

        # write file
        outputName = output
        if len(inputImages) > 1:
            directory = os.path.dirname(output)
            base = os.path.basename(output)
            name = os.path.splitext(base)[0]
            extension = os.path.splitext(base)[1]
            outputName = os.path.join(directory, name + "_" + str(indexImage) + extension)
        logger.info(f'Write {outputName}')
        itk.imwrite(outputImage, outputName)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_image_convert()
