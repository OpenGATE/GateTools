#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import click

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--short/--not-short', '-s',
              default=False,
              help='If true, display Gate path only')
def gt_gate_info(short):
    '''
    Print information about a Gate and the environment
    '''

    gt.print_gate_info(short)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    gt_gate_info()

