# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import shutil
import platform

# -----------------------------------------------------------------------------
def print_gate_info(short_verbose, cmd_gate_name = 'Gate'):
    '''
    Print information about 'Gate' executablea and system
    '''

    path = shutil.which(cmd_gate_name)
    if path == None:
        path = cmd_gate_name+' not found'

    if short_verbose:
        print(path)
        return
    
    print('Gate path:    ', path)    
    print('Machine type: ', platform.machine())
    print('Hostname:     ', platform.node())
    print('Platform:     ', platform.platform())
    print('Processor:    ', platform.processor())
    print('Python:       ', platform.python_version())
    print('System:       ', platform.system())


