#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uproot
import click
import gatetools as gt

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('root_filename', nargs=1)
def pet_necr(root_filename):
    """
    Input : root file, output from GATE PET simulation
    Output : analyse the Coincidences events from the root file and extract:
        - Trues counts
        - Random counts
        - Delays counts -> estimation of the random counts
        - Scatter counts
        - Total counts (prompts)
        And compute the NECR
    """

    # read the root file
    try:
        f = uproot.open(root_filename)
    except Exception:
        print(f'Cannot open the file {root_filename}. Is this a root file ?')
        exit(-1)

    # Compute the types of events
    data = gt.get_pet_counts(f)
    print(f'Prompt events    {data.prompts_count} \t(all coincidences)')
    print(f'Delayed events   {data.delays_count}  \t(approximation of the number of random events)')
    print(f'Random events    {data.randoms_count} \t(including noise event)')
    print(f'Scattered events {data.scatter_count}')
    print(f'Trues events     {data.trues_count}')

    # Compute the rate -> divide the counts per seconds (if available)
    d = gt.get_pet_data(f)
    if not d:
        print('Need the acquisition time to compute the NECR')
        exit(0)

    # Compute NECR (Noise Equivalent Count Rate)
    Rt = data.trues_count / d.stop_time_sec
    Rtot = data.prompts_count / d.stop_time_sec
    Rsc = data.scatter_count / d.stop_time_sec
    necr = Rt ** 2 / Rtot
    sf = Rsc / (Rt + Rsc)
    print(f'NECR             {necr}')
    print(f'ScatterFraction  {sf}')


# --------------------------------------------------------------------------
if __name__ == '__main__':
    pet_necr()
