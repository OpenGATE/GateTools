#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import click
import sys
import os
import logging
logger=logging.getLogger(__name__)


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--output','-o', help='Output root filename', required=True,
              type=click.Path(dir_okay=False))
@click.option('--incrementrunid','-r', help='Increment RunId', is_flag=True)
@click.argument('inputsroot', nargs=-1, type=click.Path(dir_okay=False))

@gt.add_options(gt.common_options)
def gt_merge_root_main(output, incrementrunid, inputsroot, **kwargs):
    '''
    Tool to merge root files and create a new output root file

    eg:

    gt_merge_root -d output.root root1.root root2.root

    Due to uproot3, it cannot merge TTree with string variables

    This tool has different behavior to merge Id:

      - by default, if runId and eventId are present, increment the eventId whithout change runId

      - with incrementrunid flag, increment runId without change eventId
    '''

    # logger
    gt.logging_conf(**kwargs)
    inputs = [x for x in inputsroot]
    print("Merge these root files: ")
    print(inputs)
    gt.merge_root(inputs, output, incrementrunid)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_merge_root_main()
