#!/usr/bin/env python

import os
import shutil
import click
import colorama
import sys
import re
import itk

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "gatetools"))
from gatetools import image_arithm
import mergeStatFile

def isPresentInFile(file, searched):
    isInFile = False
    openedFile = open(file, "r")
    for line in openedFile:
        if re.search(searched, line):
            isInFile = True
        if isInFile:
            break
    return isInFile

def checkInterfile(file):
    openedFile = open(file, "r")
    xSize = 0
    ySize = 0
    zSize = 0
    byte_per_pixel = 0
    rawData = ""
    for line in openedFile:
        if line.startswith("!matrix size [1] := "):
            xSize = int(line.split(" ")[-1])
        elif line.startswith("!matrix size [2] := "):
            ySize = int(line.split(" ")[-1])
        elif line.startswith("!number of projections := "): #sould be ("!total number of images := ")
            zSize = int(line.split(" ")[-1])
        elif line.startswith("!number of bytes per pixel := "):
            byte_per_pixel = int(line.split(" ")[-1])
        elif line.startswith("!name of data file := output/"):
            rawData = line.split("/")[-1]

    rawData = os.path.join(os.path.dirname(file), rawData)[:-1]
    if os.path.isfile(rawData):
        if xSize*ySize*zSize*byte_per_pixel == os.path.getsize(rawData):
            return True
        else:
            return False
    else:
        return False

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('outputs', nargs=1)
@click.option('-f', '--force', is_flag=True, help='Merge files even if the file is missing in some output')
def mergeJobs(outputs, force):
    """
    \b
    Merge Gate jobs

    OUTPUTS: Folders where output are present and ready to be merged (eg: run.xxxx)

    """

    # Check the folder outputs
    rundir = outputs
    if not rundir == '' and not os.path.isabs(rundir):
        rundir = os.path.join(os.getcwd(), rundir)
    if rundir.endswith('/'):
        rundir = rundir[:-1]
    if not os.path.isdir(rundir):
        print(colorama.Fore.RED + 'ERROR: The outputs folder does not exist: ' + outputs + colorama.Style.RESET_ALL)
        exit(1)

    #Look for the number of output dir in outputs
    outputsDirs = []
    for root, dirs, files in os.walk(rundir):
        for dir in dirs:
            if dir.startswith("output"):
                outputsDirs += [os.path.join(root, dir)]
    if len(outputsDirs) == 0:
        print(colorama.Fore.RED + 'ERROR: No output folder in outputs: ' + outputs + colorama.Style.RESET_ALL)
        exit(1)

    #Create results folder
    resultDir = "results"
    splitRunDir = os.path.basename(rundir).split('.')
    if len(splitRunDir) > 1:
        numberRun = ".".join(splitRunDir[1:])
        if not numberRun == '':
            resultDir += "." + numberRun
    resultDir = os.path.join(os.getcwd(), resultDir)
    if os.path.isdir(resultDir):
        print(colorama.Fore.YELLOW + 'WARNING: The result folder already exist: ' + resultDir + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + 'Evereything will be overwritten' + colorama.Style.RESET_ALL)
        shutil.rmtree(resultDir)
    os.makedirs(resultDir)

    #Look for correct files in outputsDir
    rootFiles = {}
    hdrFiles = {}
    hdrInterfileFiles = {}
    mhdFiles = {}
    statFiles = {}
    doseFiles = {}
    resolFiles = {}
    doseByRegionsFiles = {}
    txtFiles = {}
    for outputsDir in outputsDirs:
        for root, dirs, files in os.walk(outputsDir):
            for file in files:
                fullPathFile = os.path.join(root, file)
                if file.endswith(".root"):
                    if file in rootFiles.keys():
                        rootFiles[file] += [fullPathFile]
                    else:
                        rootFiles[file] = [fullPathFile]
                elif file.endswith(".mha") or file.endswith(".mhd"):
                    if file in mhdFiles.keys():
                        mhdFiles[file] += [fullPathFile]
                    else:
                        mhdFiles[file] = [fullPathFile]
                elif file.endswith(".txt"):
                    if isPresentInFile(fullPathFile, 'NumberOfEvent'):
                        if file in statFiles.keys():
                            statFiles[file] += [fullPathFile]
                        else:
                            statFiles[file] = [fullPathFile]
                    elif isPresentInFile(fullPathFile, 'energydose'):
                        if file in doseFiles.keys():
                            doseFiles[file] += [fullPathFile]
                        else:
                            doseFiles[file] = [fullPathFile]
                    elif isPresentInFile(fullPathFile, 'Resol'):
                        if file in resolFiles.keys():
                            resolFiles[file] += [fullPathFile]
                        else:
                            resolFiles[file] = [fullPathFile]
                        print("not for the moment")
                        exit(1)
                    elif isPresentInFile(fullPathFile, 'vol(mm3)'):
                        if file in doseByRegionsFiles.keys():
                            doseByRegionsFiles[file] += [fullPathFile]
                        else:
                            doseByRegionsFiles[file] = [fullPathFile]
                    else:
                        if file in txtFiles.keys():
                            txtFiles[file] += [fullPathFile]
                        else:
                            txtFiles[file] = [fullPathFile]
                elif file.endswith(".hdr"):
                    if isPresentInFile(fullPathFile, 'INTERFILE'):
                        if checkInterfile(fullPathFile):
                            if file in hdrInterfileFiles.keys():
                                hdrInterfileFiles[file] += [fullPathFile]
                            else:
                                hdrInterfileFiles[file] = [fullPathFile]
                    else:
                        if file in hdrFiles.keys():
                            hdrFiles[file] += [fullPathFile]
                        else:
                            hdrFiles[file] = [fullPathFile]

    if not len(rootFiles.keys()) == 0:
        for key in rootFiles:
            outputFile = os.path.join(resultDir, os.path.basename(rootFiles[key][0]))
            for file in rootFiles[key][1:]:
                #./mergeStatFile.sh -i outputFile -j file -o outputFile
                print("merge root file " + file)

    if not len(statFiles.keys()) == 0:
        for key in statFiles:
            outputFile = os.path.join(resultDir, os.path.basename(statFiles[key][0]))
            mergeStatFile.mergeStatFileMain(statFiles[key], outputFile)

    if not len(doseFiles.keys()) == 0:
        for key in doseFiles:
            outputFile = os.path.join(resultDir, os.path.basename(doseFiles[key][0]))
            for file in doseFiles[key][1:]:
                #./mergeDosePerEnergyFile.sh -i outputFile -j file -o outputFile
                print("merge dose file " + file)

    if not len(doseByRegionsFiles.keys()) == 0:
        for key in doseByRegionsFiles:
            outputFile = os.path.join(resultDir, os.path.basename(doseByRegionsFiles[key][0]))
            for file in doseByRegionsFiles[key][1:]:
                #./mergeDoseByRegions.sh -i outputFile -j file -o outputFile
                print("merge doseByRegionsFiles file " + file)

    if not len(resolFiles.keys()) == 0:
        for key in resolFiles:
            outputFile = os.path.join(resultDir, os.path.basename(resolFiles[key][0]))
            for file in resolFiles[key][1:]:
                #./clitkMergeAsciiDoseActor.sh -i outputFile -j file -o outputFile
                print("merge resol file " + file)

    if not len(hdrFiles.keys()) == 0:
        for key in hdrFiles:
            outputFile = os.path.join(resultDir, os.path.basename(hdrFiles[key][0]))
            temp = image_arithm.image_sum(input_list=mhdFiles[key])
            itk.imwrite(temp, outputFile)

    if not len(hdrInterfileFiles.keys()) == 0:
        for key in hdrInterfileFiles:
            outputFile = os.path.join(resultDir, os.path.basename(hdrInterfileFiles[key][0]))
            temp = image_arithm.image_sum(input_list=hdrInterfileFiles[key])
            itk.imwrite(temp, outputFile)

    if not len(mhdFiles.keys()) == 0:
        for key in mhdFiles:
            outputFile = os.path.join(resultDir, os.path.basename(mhdFiles[key][0]))
            temp = image_arithm.image_sum(input_list=mhdFiles[key])
            itk.imwrite(temp, outputFile)

if __name__ == "__main__":
    colorama.init()
    mergeJobs()
