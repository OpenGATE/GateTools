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
import logging
logger=logging.getLogger(__name__)

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
        logger.info(path)
        return

    # get gatetools version
    gtv = pkg_resources.get_distribution("gatetools").version

    # get G4 env variables
    g4_list = ['G4ABLADATA', 'G4ENSDFSTATEDATA', 'G4INCLDATA', 'G4LEDATA', 'G4LEVELGAMMADATA', 'G4NEUTRONHPDATA', 'G4PARTICLEXSDATA', 'G4PIIDATA', 'G4RADIOACTIVEDATA', 'G4REALSURFACEDATA', 'G4SAIDXSDATA']

    logger.info('Gate path:         ', path)
    logger.info('Version:           ', output)
    logger.info('Machine type:      ', platform.machine())
    logger.info('Hostname:          ', platform.node())
    logger.info('Platform:          ', platform.platform())
    logger.info('Processor:         ', platform.processor())
    logger.info('Python:            ', platform.python_version())
    logger.info('System:            ', platform.system())
    logger.info('GateTools version: ', gtv)
    for g in g4_list:
        try:
            logger.info('{:<19} {}'.format(g, os.environ[g]))
        except:
            logger.info('{:<19} NOT FOUND'.format(g))
