import sys
# Add opengate_run.py path
sys.path.append("/pbs/throng/creatis/users/tbaudier/GateTools/clustertools")
from opengate_run import *

# Alias
len_field = [[80,20],[80,50],[80,80],[80,110],[20,80],[50,80],[80,80],[110,80]]

# Go to the .py macro directory
os.chdir("/sps/creatis/tbaudier/Gate_code/")

# For all alias, run jobs (here 30)
# The alias, the .py macro must implement click options (here xf and yf)
# The output of the .py macro must be in a folder called "output"
# The jobs output are in run.XXXX folder. The name can be changed by the user (here run.<x_field>_<y_field>)
for field in len_field:
    x_field = str(field[0])
    y_field = str(field[1])
    params = "-xf {} -yf {}".format(x_field,y_field)
    runJobs_opengate("gateSimu.py", jobs=30, param=params, output="run." + str(x_field) + "_" + str(y_field))

