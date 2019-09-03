#!/usr/bin/env python

import os
import tempfile
import shutil
import click
import socket
from distutils.spawn import find_executable
import colorama
import numpy as np
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
print(sys.path)

from parserMacro import *


def get_dns_domain():
    return socket.getfqdn().split('.', 1)[1]

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('mac', nargs=1)
@click.option('-j', '--jobs', default=1, help='Number of jobs/core')
@click.option('-n', '--primaries', default=0.0, help='Total number of primaries for all jobs')
@click.option('--env', default='', help='Bash script to set environment variables during job')
@click.option('--releasedir', default='', help='Gate release directory for the jobs (none means Gate in PATH)')
@click.option('--paramtogate', default='', help='Parameters for Gate')
@click.option('--timestart', default=0.0, help='Set time start for the first job')
@click.option('--timeslice', default=0.0, help='Set time duration for one job')
@click.option('--timestop', default=0.0, help='Set time stop for the last job')
@click.option('--splittime', is_flag=True, help='Divide time duration into the number of jobs')
@click.option('-o', '--output', default='', help='Output fullpath folder (default: run.XXX)')
@click.option('-a', '--alias', type=(str, str), multiple=True, help='Alias (-a exemple Lu-177 -a foo 72.3)')
@click.option('--copydata', is_flag=True, help='Hard copy data into run.XXX folder (default: symbolic link)')
@click.option('-d', '--dry', is_flag=True, help='If dry is set, copy all files, write the submission command lines but do not execute them')
def runJobs(mac, jobs, primaries, env, releasedir, paramtogate, timestart, timeslice, timestop, splittime, output, alias, copydata, dry):
    """
    \b
    Run Gate jobs

    MAC: input mac filename

    """

    #
    numberprimaries = primaries
    
    #Control if options are correct:
    if numberprimaries != 0:
        if timestart != 0 or timeslice != 0 or timestop != 0:
            print(colorama.Fore.YELLOW + "WARNING: Cannot use time options (timestart, timeslice or timestop) with numberprimaries." + colorama.Style.RESET_ALL)

    directoryJobFiles = os.path.dirname(os.path.abspath(__file__))
    jobFile = ""
    # Take the correct job file according to the cluster name
    if get_dns_domain() == 'in2p3.fr':
        jobFile = os.path.join(directoryJobFiles, 'gate_job_ccin2p3.job')
    else:
        jobFile = os.path.join(directoryJobFiles, 'gate_job_cluster.job')
    if not os.path.isfile(jobFile):
        print(colorama.Fore.RED + 'ERROR: The job file does not exist: ' + jobFile + colorama.Style.RESET_ALL)
        exit(1)

    # Get the release of Gate used for the simulation
    if (releasedir == ''):
        try:
            releasedir = os.path.dirname(find_executable('Gate'))
        except:
            print(colorama.Fore.RED + 'ERROR: No Gate found in PATH' + colorama.Style.RESET_ALL)
            exit(1)
        else:
            print('Found Gate in folder: ' + releasedir)
            releasedir = 'NONE'
    else:
        if not os.path.isdir(releasedir):
            print(colorama.Fore.RED + 'ERROR: This folder does not exist: ' + releasedir + colorama.Style.RESET_ALL)
            exit(1)
        if not os.path.isfile(os.path.join(releasedir, 'Gate')):
            print(colorama.Fore.RED + 'ERROR: There is no release of Gate in that folder: ' + releasedir + colorama.Style.RESET_ALL)
            exit(1)

    # Get macro folder and files
    fullMacroDir = os.path.join(os.getcwd(), os.path.dirname(os.path.dirname(mac)))
    relativeMacroDir = os.path.dirname(os.path.dirname(mac))
    mainMacroFile = mac[len(relativeMacroDir)+1:]
    if relativeMacroDir == '':
        relativeMacroDir = '.'
        mainMacroFile = mac
    if not os.path.isdir(os.path.join(fullMacroDir, 'mac')):
        print(colorama.Fore.RED + 'ERROR: The mac folder does not exist: ' + os.path.join(fullMacroDir, 'mac') + colorama.Style.RESET_ALL)
        exit(1)
    if not os.path.isdir(os.path.join(fullMacroDir, 'data')):
        print(colorama.Fore.RED + 'ERROR: The data folder does not exist: ' + os.path.join(fullMacroDir, 'data') + colorama.Style.RESET_ALL)
        exit(1)
    if not os.path.isfile(mac):
        print(colorama.Fore.RED + 'ERROR: The mac file does not exist: ' + mac + colorama.Style.RESET_ALL)
        exit(1)

    # Create output directory
    outputDir = output
    if not outputDir == '' and os.path.isdir(outputDir):
        print(colorama.Fore.RED + 'ERROR: The output folder already exist (remove it): ' + outputDir + colorama.Style.RESET_ALL)
        exit(1)
    if outputDir == '':
        outputDir = tempfile.mkdtemp(prefix='run.', dir=fullMacroDir)
    elif not os.path.isdir(outputDir):
        os.mkdir(outputDir)
    runId = os.path.basename(outputDir)[os.path.basename(outputDir).find('.') +1:]
    print('Run Id is: ' + runId)

    # Find qsub
    qsub = shutil.which('qsub')
    if qsub is None:
        print('No qsub, run Gate on multiple cores.')

    # Parameter files
    paramFileName = os.path.join(outputDir, 'params.txt')
    paramFile = open(paramFileName, "w")
    paramFile.write('njobs = ' + str(jobs))
    paramFile.write('macro = ' + mac)
    if paramtogate != '':
        paramFile.write('param = ' + paramtogate)
    paramFile.close()

    #Parse macro files and sub-Macro
    os.mkdir(os.path.join(outputDir, 'mac'))
    parserMacro = ParserMacro()
    parserMacro.setAlias(alias, jobs)
    parserMacro.parseMainMacFiles(fullMacroDir, mainMacroFile)

    # Copy data
    if copydata:
        shutil.copytree(os.path.join(fullMacroDir, 'data'), os.path.join(outputDir, 'data'))
    else:
        os.symlink(os.path.join(fullMacroDir, 'data'), os.path.join(outputDir, 'data'))

    # Set number of Primaries
    if numberprimaries != 0.0:
        parserMacro.setAttributes('setTotalNumberOfPrimaries', jobs*[int(numberprimaries/jobs)])

    # Set time options
    if timestart != 0:
        parserMacro.setAttributes('setTimeStart', jobs*[timestart])
    if timeslice != 0:
        parserMacro.setAttributes('setTimeSlice', jobs*[timeslice])
    if timestop != 0:
        parserMacro.setAttributes('setTimeStop', jobs*[timestop])

    #Manage split time option
    #Divide the time into jobs range of time
    if splittime:
        startTime = float(parserMacro.getAttributes('setTimeStart')[0])
        stopTime = float(parserMacro.getAttributes('setTimeStop')[0])
        slicedTime = (stopTime - startTime)/jobs
        arrayStartTime = []
        arrayStopTime = []
        for i in range(0, jobs):
            arrayStartTime += [startTime + i*slicedTime]
            arrayStopTime += [startTime + (i+1)*slicedTime]
        parserMacro.setAttributes('setTimeStart', arrayStartTime)
        parserMacro.setAttributes('setTimeSlice', np.array(arrayStopTime) - np.array(arrayStartTime))
        parserMacro.setAttributes('setTimeStop', arrayStopTime)

    #Write mac files into output folder
    parserMacro.writeMacFiles(outputDir)

    #Create file to write commands in it
    commandsFile = open(os.path.join(outputDir, "commands.txt"), "a")

    # Run jobs
    for i in range(0, jobs):
        #Set paramtogate with alias for each job
        paramtogateJob = paramtogate
        if len(parserMacro.aliasToGate) != 0:
            indexAlias = paramtogate.find('-a')
            if indexAlias != -1:
                paramtogateEnd = paramtogate[indexAlias+3:]
                paramtogateJob = paramtogate[:indexAlias+2]
                for aliasMac in parserMacro.aliasToGate:
                    paramtogateJob += '[' + aliasMac + ',' + str(parserMacro.aliasToGate[aliasMac][i]) + ']'
                    paramtogateJob += paramtogateEnd
            else:
                paramtogateJob += ' -a '
                for aliasMac in parserMacro.aliasToGate:
                    paramtogateJob += '[' + aliasMac + ',' + str(parserMacro.aliasToGate[aliasMac][i]) + ']'

        if qsub is None:
            command = 'PARAM=\" ' + paramtogateJob + \
                      '\" INDEX=' + str(i) + \
                      ' INDEXMAX=' + str(jobs) + \
                      ' OUTPUTDIR=' + outputDir + \
                      ' RELEASEDIR=' + releasedir + \
                      ' MACROFILE=' + os.path.join(outputDir, mainMacroFile) + \
                      ' MACRODIR=' + outputDir + \
                      ' PBS_JOBID=\"local_' + str(i) + \
                      '\" bash ' + jobFile
        elif get_dns_domain() == 'in2p3.fr':
            command = 'qsub -o ' + outputDir + \
                      ' -e ' + outputDir + \
                      ' -l sps=1 -N \"gate.' + runId + \
                      '\" -v \"PARAM=\\\"' + paramtogateJob + \
                      '\\\",INDEX=' + str(i) + \
                      ',INDEXMAX=' + str(jobs) + \
                      ',OUTPUTDIR=' + outputDir + \
                      ',RELEASEDIR=' + releasedir + \
                      ',MACROFILE=' + os.path.join(outputDir, mainMacroFile) + \
                      ',MACRODIR=' + outputDir + \
                      ',ENV=' + env + \
                      '\" ' + jobFile
        else:
            command = 'qsub -N \"gatejob.' + runId + \
                      ' -o ' + outputDir + \
                      ' -v \"PARAM=\\\"' + paramtogateJob + \
                      '\\\",INDEX=' + str(i) + \
                      ',INDEXMAX=' + str(jobs) + \
                      ',OUTPUTDIR=' + outputDir + \
                      ',RELEASEDIR=' + releasedir + \
                      ',MACROFILE=' + os.path.join(outputDir, mainMacroFile) + \
                      ',MACRODIR=' + outputDir + \
                      '\" ' + jobFile
        commandsFile.write(command)
        commandsFile.write("\n")
        if dry:
            print(command)
        else:
            os.system(command)



if __name__ == "__main__":
    colorama.init()
    runJobs()
