#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


###############################################
# to run script 
# python Mac2GND.py -i input.mac -o output.mac -sd crystal_name 
############################################## 
import gatetools as gt
import os
import math
import logging
logger=logging.getLogger(__name__)
import unittest
import click


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', default=0,type=str,
              help='-i input.mac, input digitizer macro')
@click.option('-o', default=0,type=str,
              help='-o ouput.mac, output new digitizer macro')
@click.option('-sd', default=0,type=str,
              help='-sd <SDname>, sensitive detector name (the one you use in line /gate/<SDname>/attachCrystalSD ) ')
@click.option('-multi', default=0,type=str,
              help='-multi <mode>, use this option of you have several Singles Collections or CoincidenceSorters, <mode> = SinglesDigitizer or CoincidenceSorter')

def convert_macro(i, o, sd, multi):
    input_file_name=i
    output_file_name=o

    fin = open(i, "rt")
    fout = open(o, "wt")

    x=[]
    singles_tmp_name='-NULL'
    coin_tmp_name='-NULL'
    flagThres=0
    flagUp=0
    newColl=0
    
    for line in fin:
        if 'digitizer' in line:
            #print (line)
            line =line.replace('/digitizer/','/digitizerMgr/')
            #print ("*"+line)
        if '/Singles/' in line:
            line =line.replace('/Singles/','/'+sd+'/SinglesDigitizer/Singles/')
        if '/Coincidences/' in line:
            line =line.replace('/Coincidences/','/CoincidenceSorter/Coincidences/')
        if 'coincidenceSorter' in line:
            line =line.replace('coincidenceSorter','CoincidenceSorter')   
        if '/allPulseOpenCoincGate' in line:
            line =line.replace('/allPulseOpenCoincGate','/allDigiOpenCoincGate')

        if 'singleChain' in line:
            line =line.replace('singleChain','SinglesDigitizer')
            
        if '/gate/digitizerMgr/name' in line:
            if(multi=='SinglesDigitizer'):
                x_non=line.replace('\n', '')
                x_tmp=x_non.replace('\t', '') 
                x = x_tmp.split(' ')
                name2 = x[len(x)-1]
                singles_tmp_name='/'+name2+'/'
                line =line.replace(line,line+'/gate/digitizerMgr/chooseSD '+sd+'\n')
                flagThres=0
                flagUp=0
                #print(singles_tmp_name)    
                
            elif (multi=='CoincidenceSorter'):
                x_non=line.replace('\n', '')
                x_tmp=x_non.replace('\t', '') 
                x = x_tmp.split(" ")
                name2 = x[len(x)-1]
                coin_tmp_name='/'+name2+'/'
                #print(tmp_name)
                #print(line)
               

        if singles_tmp_name in line:
            line =line.replace(singles_tmp_name,'/'+sd+'/SinglesDigitizer'+singles_tmp_name+'')
        if coin_tmp_name in line:
            line =line.replace(coin_tmp_name,'/CoincidenceSorter'+coin_tmp_name+'')       

            
        if '/setInputName' in line:
            line =line.replace('/setInputName','/setInputCollection')
            
        #####################################
        #Thressholder and Upholder
        #####################################
        if 'thresholder' or 'upholder'  in line: 
            if 'thresholder' in line:
                line =line.replace('thresholder','energyFraming')
                flagThres=1
            if 'upholder' in line:
                line =line.replace('upholder','energyFraming')
                flagUp=1
            if flagUp and flagThres:
                line=line.replace(line, '')
                flagUp=0
                flagThres=0
        if '/setThreshold' in line:
            line =line.replace('/setThreshold','/setMin')
        if '/setUphold' in line:
            line =line.replace('/setUphold','/setMax')
       #####################################
       # Time Resolution
       #####################################
        if '/setTimeResolution' in line:
            line =line.replace('/setTimeResolution','/fwhm')
        #####################################
        # Energy Resolution
        #####################################
        if ' blurring' in line:
            line =line.replace(' blurring',' energyResolution')
        if '/blurring/setResolution' in line:
            line =line.replace('/blurring/setResolution','/energyResolution/fwhm')
        if '/blurring/setEnergyOfReference' in line:
            line =line.replace('/blurring/setEnergyOfReference','/energyResolution/energyOfReference')    
        if '/blurring/setLaw' in line:
            line =line.replace(line,'')

        if '/blurring/linear/setResolution' in line:
            line =line.replace('/blurring/linear/setResolution','/energyResolution/fwhm')
        if '/blurring/inverseSquare/setResolution' in line:
            line =line.replace('/blurring/inverseSquare/setResolution','/energyResolution/fwhm')

        if '/blurring/linear/setEnergyOfReference' in line:
            line =line.replace('/blurring/linear/setEnergyOfReference','/energyResolution/energyOfReference')
        if '/blurring/inverseSquare/setEnergyOfReference' in line:
            line =line.replace('/blurring/inverseSquare/setEnergyOfReference','/energyResolution/energyOfReference')     
 
        if '/blurring/linear/setSlope' in line:
            line =line.replace('/blurring/linear/setSlope','/energyResolution/slope')
        #crystalblurring
        if 'crystalblurring' in line:
            line =line.replace('crystalblurring','energyResolution')
        if '/setCrystalResolutionMin' in line:
            line =line.replace('/setCrystalResolutionMin','/fwhmMin')
        if '/setCrystalResolutionMax' in line:
            line =line.replace('/setCrystalResolutionMax','/fwhmMax')
        if '/setCrystalEnergyOfReference' in line:
            line =line.replace('/setCrystalEnergyOfReference','/energyOfReference') 
        if '/setCrystalQE' in line:
            y = line.split(" ")
            name_tmp = y[1][:-1]
            value=name_tmp
            if (singles_tmp_name== '-1') :
                line =line.replace(line,'/gate/digitizerMgr/'+sd+'/SinglesDigitizer/Singles/insert efficiency\n/gate/digitizerMgr/'+sd+'/SinglesDigitizer/Singles/efficiency/setUniqueEfficiency '+ value+'\n')
            else:
                line =line.replace(line,'/gate/digitizerMgr/'+sd+'/SinglesDigitizer'+singles_tmp_name+'insert efficiency\n/gate/digitizerMgr/'+sd+'/SinglesDigitizer'+singles_tmp_name+'efficiency/setUniqueEfficiency '+ value+'\n')

            
        #####################################
        # Spatial Resolution
        #####################################
        if 'spblurring' in line:
            line =line.replace('spblurring','spatialResolution')    
        if '/setSpresolution' in line:
            line =line.replace('/setSpresolution','/fwhm') #+'\n'+'/gate/digitizerMgr/'+sd+'/SinglesDigitizer/Singles/spatialResolution/confineInsideOfSmallestElement tru)
            if (singles_tmp_name == '-1') :
                line =line.replace(line,line+'\n/gate/digitizerMgr/'+sd+'/SinglesDigitizer/Singles/spatialResolution/confineInsideOfSmallestElement true\n')
            else:
                line =line.replace(line,line+'\n/gate/digitizerMgr/'+sd+'/SinglesDigitizer'+singles_tmp_name+'spatialResolution/confineInsideOfSmallestElement true\n')

        #####################################
        # Efficiency
        #####################################
        if 'localEfficiency' in line:
            line =line.replace('localEfficiency','efficiency')
            if 'insert' in line:
                if (singles_tmp_name == '-1') :
                    line =line.replace(line,line+'/gate/digitizerMgr/'+sd+'/SinglesDigitizer/Singles/efficiency/setMode crystal\n')
                else:
                    line =line.replace(line,line+'/gate/digitizerMgr/'+sd+'/SinglesDigitizer'+singles_tmp_name+'efficiency/setMode crystal\n')          

        #####################################
        # DeadTime
        #####################################
        # nothing to do

        #####################################
        # PileUp
        #####################################
        # nothing to do
        
        #####################################
        #  adderCompton
        #####################################
        # nothing to do

        #####################################
        #  opticaladder
        #####################################
        # nothing to do

        #####################################
        #  noise
        #####################################
        # nothing to do    
              
        if '#' in line:
            line =line
        elif line=='':
            line = '' 
            
        fout.write(line)
      
    fin.close()
    fout.close()
    
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    convert_macro()
