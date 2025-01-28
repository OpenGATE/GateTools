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
import csv
import os
import matplotlib
matplotlib.get_backend()
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import logging
logger=logging.getLogger(__name__)


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--dose','-d', help='Input dose filename', required=True,
              type=click.Path(dir_okay=False))
@click.option('--roi','-r', help='Input roi filename', required=True,
              type=click.Path(dir_okay=False))
@click.option('--output','-o', help='Output base filename. Without output, it displays the DVH ',
              type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

@click.option('--bins', '-b', default=1000, help='Number of dose bins for the histogram')
@click.option('--label', '-l', default=1, help='Label of the pixels for the roi mask')
@click.option('--usecm3', '-cm3', is_flag=True, help='The volume output is in cm3 instead of %')
@click.option('--d', type=float, help='Compute DX')
@click.option('--v', type=float, help='Compute VX')

@gt.add_options(gt.common_options)
def gt_dvh_main(dose, roi, output, bins, label, usecm3, d, v, **kwargs):
    '''
    Tool to create dose volume histogram

    eg:

    gt_dvh -d dose.mhd -r roi.mhd -o output

    Display without output option or save the graph to csv and png formats if output is set
    If v is set, do not display and save the graph but print the VX, ie. the volume receiving at least XGy
    If d is set, do not display and save the graph but print the DX, ie. the dose received by at least X% (or X cm3 is the flag is set) of the volume
    '''

    # logger
    gt.logging_conf(**kwargs)

    doseImage = itk.imread(dose)
    roiImage = itk.imread(roi)

    doseValues, volumePercentage = gt.createDVH(doseImage, roiImage, bins, label, usecm3)

    if v is not None:
        volume = gt.computeV(doseValues, volumePercentage, v)
        string = "V" + str(v) + " = " + str(volume)
        if usecm3:
            string += " cm3"
        else:
            string += " %"
        print(string)
    elif d is not None:
        dose = gt.computeD(doseValues, volumePercentage, d)
        print("D" + str(d) + " = " + str(dose) + " Gy")
    else:
        plt.plot(doseValues, volumePercentage)
        if usecm3:
            plt.ylabel('Volume cm3')
        else:
            plt.ylabel('Volume %')
        plt.xlabel('Dose Gy')
        if output is None:
            plt.show()
        else:
            plt.savefig(output+'.png')
            with open(output+'.csv', 'w', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow(['Dose Gy'] + ['Volume %'])
                for x, y in zip(doseValues, volumePercentage):
                    spamwriter.writerow([x, y])


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_dvh_main()
