#!/usr/bin/env python

import os
import tempfile
import shutil
import click
import socket
from distutils.spawn import find_executable
import colorama
import numpy as np


def get_dns_domain():
    return socket.getfqdn().split('.', 1)[1]

class ParserMacro:
    def __init__(self):
        self.parserAllFiles = {}
        self.aliasToGate = {}
        self.aliasNumber = 0
        self.parserAlias = {}
        self.parserAttributes = {}
        self.macFiles = []
        self.fullMacroDir = ""

    def parseMacFiles(self, fullMacroDir, mainMacroFile):
        self.fullMacroDir = fullMacroDir
        self.macFiles = [os.path.join(self.fullMacroDir, mainMacroFile)]
        while len(self.macFiles) != 0:
            #Take first macro file in the list
            currentMacFiles = self.macFiles[0]

            # Structure containing all lines of the macro file
            self.parserAllFiles[currentMacFiles] = []
            with open(os.path.join(fullMacroDir, currentMacFiles)) as f:  # open file
                for line in f:
                    self.parserAllFiles[currentMacFiles] += [line]

            #Start to parse the macro file
            self.parseControlCommand(currentMacFiles)
            self.parseAttributes(currentMacFiles)

            #Take next file
            del self.macFiles[0]

    def parseControlCommand(self, file):
        #Parse macro file to get /control/ commands
        for index, line in enumerate(self.parserAllFiles[file]):
            if not line.startswith('#') and not line == '\n':
                line = line.strip()
                splitLine = line.split(" ")
                splitLine = [x for x in splitLine if x]
                if len(splitLine) > 0 and splitLine[0][:9] == '/control/':
                    self.checkControlCommand(splitLine, file, index)

    def checkControlCommand(self, splitLine, file, index):
        if len(splitLine) > 0 and splitLine[0] == '/control/alias':
            self.parseAlias(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/strdoif':
            newSplitLine = self.parseCondition(splitLine)
            if len(newSplitLine) > 0:
                newLine = " ".join(newSplitLine)
                newLine += '\n'
                self.parserAllFiles[file][index] = newLine
                if newSplitLine[0][:9] == '/control/':
                    self.checkControlCommand(newSplitLine, file, index)
            else:
                self.parserAllFiles[file][index] = "\n"
        elif len(splitLine) > 0 and splitLine[0] == '/control/execute':
            self.getMacroFiles(splitLine)
        elif len(splitLine) > 0 and (splitLine[0] == '/control/add' or
                                     splitLine[0] == '/control/substract' or
                                     splitLine[0] == '/control/multiply' or
                                     splitLine[0] == '/control/divide'):
            value = self.parseOperation(splitLine)
            if value is not None:
                newLine = '/control/alias ' + splitLine[1] + " " + str(value) + '\n'
                self.parserAllFiles[file][index] = newLine
        elif len(splitLine) > 0 and splitLine[0] != '/control/verbose' and splitLine[0] != '/control/listAlias':
            print(colorama.Fore.YELLOW + "WARNING: "
                  "Unrecognized /control command: " + splitLine[0] + colorama.Style.RESET_ALL)

    def parseAlias(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/alias':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            self.parserAlias[splitLine[1]] = splitLine[2]

    def parseCondition(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/strdoif':
            #left condition
            splitLine[1] = self.decriptAlias(splitLine[1])
            splitLine[1] = " ".join(splitLine[1])
            #right condition
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            if splitLine[2] == "==":
                if splitLine[1] == splitLine[3]:
                    return splitLine[4:]
            elif splitLine[2] == "!=":
                if splitLine[1] != splitLine[3]:
                    return splitLine[4:]
            else:
                print(colorama.Fore.YELLOW + "WARNING: Not possible to decrypt: " + " ".join(splitLine) + colorama.Style.RESET_ALL)
            return []

    def getMacroFiles(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/execute':
            splitLine[1] = self.decriptAlias(splitLine[1])
            splitLine[1] = " ".join(splitLine[1])
            self.macFiles.append(os.path.join(self.fullMacroDir, splitLine[1]))

    def parseOperation(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/add':
            return self.parseAdd(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/subtract':
            return self.parseSubtract(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/multiply':
            return self.parseMultiply(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/divide':
            return self.parseDivide(splitLine)
        return None

    def parseAdd(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/add':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) + float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseSubtract(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/subtract':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) - float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseMultiply(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/multiply':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) * float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseDivide(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/divide':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) / float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseAttributes(self, file):
        for index, line in enumerate(self.parserAllFiles[file]):
            if not line.startswith('#') and not line == '\n':
                line = line.strip() #Remove trailing whitespace
                if line.startswith('/gate/application/setTimeStart'):
                    self.parserAttributes["setTimeStart"] = [file, index]
                elif line.startswith('/gate/application/setTimeSlice'):
                    self.parserAttributes["setTimeSlice"] = [file, index]
                elif line.startswith('/gate/application/setTimeStop'):
                    self.parserAttributes["setTimeStop"] = [file, index]
                elif line.startswith('/gate/application/setTotalNumberOfPrimaries'):
                    self.parserAttributes["setTotalNumberOfPrimaries"] = [file, index]

    def setAlias(self, alias, jobs):
        for a in alias:
            self.parserAlias[a[0]] = str(a[1])
            self.aliasToGate[a[0]] = jobs*[str(a[1])]
            self.aliasNumber += 1

    def setAttributes(self, attribute, valuesForAllJobs):
        line = self.parserAllFiles[self.parserAttributes[attribute][0]][self.parserAttributes[attribute][1]]
        line = line.strip() #Remove trailing whitespace
        splitLine = line.split(" ")
        splitLine = [x for x in splitLine if x]
        if not isinstance(valuesForAllJobs[0], list):
            splitLine[1] = '{' + attribute + '_' + str(self.aliasNumber) + '}'
            self.aliasToGate[attribute + '_' + str(self.aliasNumber)] = valuesForAllJobs
            self.aliasNumber += 1
        else:
            for index, value in enumerate(valuesForAllJobs[0]):
                splitLine[index + 1] = '{' + attribute + '_' + str(self.aliasNumber) + '}'
                self.aliasToGate[attribute + '_' + str(self.aliasNumber)] = valuesForAllJobs[:][index]
                self.aliasNumber += 1
        self.parserAllFiles[self.parserAttributes[attribute][0]][self.parserAttributes[attribute][1]] = " ".join(splitLine) + '\n'

    # Return the value of the attribute, not the command
    # Check if containing alias, in such a case, replace it by the alias value if it exist, else raise an error
    def getAttributes(self, attribute):
        line = self.parserAllFiles[self.parserAttributes[attribute][0]][self.parserAttributes[attribute][1]]
        splitLine = self.decriptAlias(line, attribute)
        return splitLine[1:]

    def getAlias(self, alias):
        if not alias in self.parserAlias:
            print(colorama.Fore.RED + "ERROR: alias " + alias + " is not found in macro files" + colorama.Style.RESET_ALL)
            exit(1)
        return self.parserAlias[alias] #Do not return the command and the name of the alias

    def decriptAlias(self, line, attribute=""):
        line = line.strip()
        line = line.split(" ")
        splitLine = []
        for x in line:
            startAliasIndex = x.find('{')
            endAliasIndex = x.find('}')
            if startAliasIndex != -1 and endAliasIndex != 1:
                if startAliasIndex < endAliasIndex:
                    if x[startAliasIndex+1:endAliasIndex] in self.parserAlias:
                        xAlias = x[:startAliasIndex] + self.getAlias(x[startAliasIndex+1:endAliasIndex]) + x[endAliasIndex+1:]
                        splitLine += [xAlias]
                    else:
                        print(colorama.Fore.RED + "ERROR: attribute \"" + x + "\" is an alias " + x[startAliasIndex+1:endAliasIndex] + colorama.Style.RESET_ALL)
                        print(colorama.Fore.RED + "And the alias was not found in macro files" + colorama.Style.RESET_ALL)
                        exit(1)
            elif x:
                splitLine += [x]
        return splitLine

    def writeMacFiles(self, outputDir):
        for file in self.parserAllFiles:
            writtingFile = file[len(self.fullMacroDir):]
            folder = os.path.dirname(os.path.join(outputDir, writtingFile))
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(outputDir, writtingFile), 'w') as f:
                for element in self.parserAllFiles[file]:
                    f.write(element)


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
    parserMacro.parseMacFiles(fullMacroDir, mainMacroFile)

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
