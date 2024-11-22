#!/pbs/throng/creatis/cl7/opengate/venv/bin/python

import os
import tempfile
import shutil
import click
import socket
import subprocess
import colorama
import numpy as np
import sys
import time
import gatetools

def get_dns_domain():
    domain = socket.getfqdn().split('.', 1)
    if len(domain) >= 2:
        return domain[1]
    else:
        return domain[0]

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('script', nargs=1)
@click.option('-j', '--jobs', default=1, help='Number of jobs/core')
@click.option('-o', '--output', default='', help='Output folder path (default: run.XXX)')
@click.option('-p', '--param', default='', help='click parameter to pass to the python script (-p " --angle 10 --nbParticles 1e8"')
@click.option('--copydata', is_flag=True, help='Hard copy data into run.XXX folder (default: symbolic link)')
@click.option('-d', '--dry', is_flag=True, help='If dry is set, copy all files, write the submission command lines but do not execute them')
@click.option('--env', default='', help='Bash script to set environment variables during job. This file is source at the beginning.')
@click.option('--jobfile', default='', help='Job file for the cluster allowing to modify submission parameters (--jobfile="current" display the path of the current job file and exit)')
def runJobs_click(script, jobs, env, output, param, copydata, dry, jobfile):
    """
    \b
    Run python Gate jobs

    script: input python script filename

    """
    runJobs_opengate(script, jobs, env, output, param, copydata, dry, jobfile)



def runJobs_opengate(script, jobs=1, env='', output='', param='', copydata=False, dry=False, jobfile=''):
    directoryJobFiles = os.path.join(os.path.dirname(os.path.realpath(gatetools.__file__)), "clustertools")

    # Source env file
    envCommand = ''
    if not env == '':
        if not os.path.isabs(env):
          env = os.path.join(os.getcwd(), env)
        if not os.path.isfile(env):
            print(colorama.Fore.RED + 'ERROR: No env found : ' + env + colorama.Style.RESET_ALL)
            exit(1)
        else:
            envCommand = env
    else:
        envCommand = 'NONE'

    jobFile = ""
    # Take the correct job file according to the cluster name and jobfile option
    if jobfile == '' or jobfile == "current":
        if get_dns_domain() == 'in2p3.fr':
            jobFile = os.path.join(directoryJobFiles, 'opengate_job_ccin2p3.slurm')
        if jobfile == "current":
            print(colorama.Fore.GREEN + 'Path to the job file: ' + colorama.Style.RESET_ALL)
            print(jobFile)
            exit(1)
    else:
        jobFile = jobfile
        if not os.path.isabs(jobFile):
          jobFile = os.path.join(os.getcwd(), jobFile)
        if not os.path.isfile(jobFile):
            print(colorama.Fore.RED + 'ERROR: The job file does not exist: ' + jobFile + colorama.Style.RESET_ALL)
            exit(1)

    # Get python folder and files
    fullMacroDir = os.path.join(os.getcwd(), os.path.dirname(os.path.dirname(script)))
    fullScriptFile = os.path.join(fullMacroDir, os.path.basename(script))
    if not os.path.isfile(script):
        print(colorama.Fore.RED + 'ERROR: The python file does not exist: ' + script + colorama.Style.RESET_ALL)
        exit(1)

    # Check output path is absolute or relative
    outputDir = output
    if not outputDir == '' and not os.path.isabs(outputDir):
      outputDir = os.path.join(os.getcwd(), outputDir)
    # Create output directory
    if not outputDir == '' and os.path.isdir(outputDir):
        print(colorama.Fore.YELLOW + 'WARNING: The output folder already exist: ' + outputDir + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + 'Evereything will be overwritten' + colorama.Style.RESET_ALL)
    if outputDir == '':
        outputDir = tempfile.mkdtemp(prefix='run.', dir=fullMacroDir)
    elif not os.path.isdir(outputDir):
        os.makedirs(outputDir)
    runId = os.path.basename(outputDir)[os.path.basename(outputDir).find('.') +1:]
    if runId == '':
        runId == os.path.basename(outputDir)
    print('Run Id is: ' + runId)

    # Find qsub
    qsub = shutil.which('qsub')
    if qsub is None:
        qsub = shutil.which('sbatch')
        if qsub is None:
            print('No qsub, run Gate on multiple cores.')

    # Parameter files
    paramFileName = os.path.join(outputDir, 'run.log')
    paramFile = open(paramFileName, "w")
    paramFile.write('number of jobs = ' + str(jobs) + '\n')
    paramFile.write('script = ' + script + '\n')
    paramFile.write('runId = ' + runId + '\n')

    #Create file to write commands in it
    paramFile.write('\ncommands: \n')

    # Run jobs
    for i in range(0, jobs):
        #Set paramtogate with param for each job
        paramtogateJob = param

        if get_dns_domain() == 'in2p3.fr':
            tempParamFile = tempfile.NamedTemporaryFile(mode='w+t', delete=False, prefix='var.', dir=outputDir)
            tempParamFile.write(paramtogateJob)
            tempParamFile.close()
            command = 'sbatch -L sps -J gate.' + runId + \
                      ' -D ' + outputDir + \
                      ' --export=ALL,PARAM=\"' + tempParamFile.name + \
                      '\",INDEX=' + str(i) + \
                      ',INDEXMAX=' + str(jobs) + \
                      ',OUTPUTDIR=' + outputDir + \
                      ',MACROFILE=' + fullScriptFile + \
                      ',MACRODIR=' + os.path.dirname(fullScriptFile) + \
                      ',ENVCOMMAND=' + envCommand + \
                      ' ' + jobFile
        paramFile.write(command)
        paramFile.write("\n")
        if dry:
            print(command)
        else:
            os.system(command)
            if qsub is None:
                time.sleep(1)

    paramFile.close()
    print(str(jobs) + ' jobs running')
    print('Run folder is: ' + outputDir)


if __name__ == "__main__":
    colorama.init()
    runJobs_click()
