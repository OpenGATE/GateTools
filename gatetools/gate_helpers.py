# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import shutil
import platform
import subprocess
import pkg_resources
import os
import itk
import numpy as np

# -----------------------------------------------------------------------------
def print_gate_info(short_verbose, cmd_gate_name = 'Gate'):
    '''
    Print information about 'Gate' executablea and system
    '''

    # get Gate path
    path = shutil.which(cmd_gate_name)

    # get version info
    if path == None:
        path = cmd_gate_name+' not found'
        output = ''
    else:
        result = subprocess.run(['Gate', '--version'], stdout=subprocess.PIPE)
        output = result.stdout.decode("utf-8").splitlines()[0]

    if short_verbose:
        print(path)
        return

    # get gatetools version
    gtv = pkg_resources.get_distribution("gatetools").version

    # get G4 env variables
    g4_list = ['G4ABLADATA', 'G4ENSDFSTATEDATA', 'G4INCLDATA', 'G4LEDATA', 'G4LEVELGAMMADATA', 'G4NEUTRONHPDATA', 'G4PARTICLEXSDATA', 'G4PIIDATA', 'G4RADIOACTIVEDATA', 'G4REALSURFACEDATA', 'G4SAIDXSDATA']

    print('Gate path:         ', path)
    print('Version:           ', output)
    print('Machine type:      ', platform.machine())
    print('Hostname:          ', platform.node())
    print('Platform:          ', platform.platform())
    print('Processor:         ', platform.processor())
    print('Python:            ', platform.python_version())
    print('System:            ', platform.system())
    print('GateTools version: ', gtv)
    for g in g4_list:
        try:
            print('{:<19} {}'.format(g, os.environ[g]))
        except:
            print('{:<19} NOT FOUND'.format(g))


def img_size(image):
    return np.array(image.GetLargestPossibleRegion().GetSize())

def img_spacing(image):
    return np.array(image.GetSpacing())
