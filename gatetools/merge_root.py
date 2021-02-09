# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""

This module provides a function to crop image

"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import gatetools as gt
import numpy as np
import tqdm
import logging
logger=logging.getLogger(__name__)

def unicity(root_keys):
    """
    Return an array containing the keys of the root file only one (without the version number)
    """
    root_array = []
    for key in root_keys:
        name = key.decode("utf-8").split(";")[0]
        if not name in root_array:
            root_array.append(name)
    return(root_array)

def merge_root(rootfiles, outputfile, incrementRunId=False):
    """
    Merge root files in output files
    """
    try:
        import uproot3 as uproot
    except:
        print("uproot3 is mandatory to merge root file. Please, do:")
        print("pip install uproot3")

    out = uproot.recreate(outputfile)

    #Previous ID values to be able to increment runIn or EventId
    previousId = {}

    #create the dict reading all input root files
    trees = {}
    pbar = tqdm.tqdm(total = len(rootfiles))
    for file in rootfiles:
        root = uproot.open(file)
        root_keys = unicity(root.keys())
        for tree in root_keys:
            if hasattr(root[tree], 'keys'):
                if not tree in trees:
                    trees[tree] = {}
                    trees[tree]["rootDictType"] = {}
                    trees[tree]["rootDictValue"] = {}
                    previousId[tree] = {}
                for branch in root[tree].keys():
                    array = root[tree].array(branch)
                    if len(array) > 0:
                        if type(array[0]) is type(b'c'):
                            array = np.array([0 for xi in array])
                        if not branch in trees[tree]["rootDictType"]:
                            trees[tree]["rootDictType"][branch] = type(array[0])
                            trees[tree]["rootDictValue"][branch] = np.array([])
                        if (not incrementRunId and branch.decode('utf-8').startswith('eventID')) or (incrementRunId and branch.decode('utf-8').startswith('runID')):
                            if not branch in previousId[tree]:
                                previousId[tree][branch] = 0
                            array += previousId[tree][branch]
                            previousId[tree][branch] = max(array) +1
                        trees[tree]["rootDictValue"][branch] = np.append(trees[tree]["rootDictValue"][branch], array)
        pbar.update(1)
    pbar.close()

    #Set the dict in the output root file
    for tree in trees:
        if not trees[tree]["rootDictValue"] == {} or not trees[tree]["rootDictType"] == {}:
            out[tree] = uproot.newtree(trees[tree]["rootDictType"])
            out[tree].extend(trees[tree]["rootDictValue"])




#####################################################################################
import unittest
import tempfile
import wget
import os
import shutil
from .logging_conf import LoggedTestCase

class Test_MergeRoot(LoggedTestCase):
    def test_merge_root_phsp(self):
        try:
            import uproot3 as uproot
        except:
            print("uproot3 is mandatory to merge root file. Please, do:")
            print("pip install uproot3")

        logger.info('Test_MergeRoot test_merge_root_phsp')
        tmpdirpath = tempfile.mkdtemp()
        filenameRoot = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/phsp.root?inline=false", out=tmpdirpath, bar=None)
        gt.merge_root([filenameRoot, filenameRoot],  os.path.join(tmpdirpath, "output.root"))
        input = uproot.open(filenameRoot)
        output = uproot.open(os.path.join(tmpdirpath, "output.root"))
        self.assertTrue(output.keys() == input.keys())
        inputTree = input[input.keys()[0]]
        outputTree = output[output.keys()[0]]
        self.assertTrue(outputTree.keys() == inputTree.keys())
        inputBranch = inputTree.array(inputTree.keys()[1])
        outputBranch = outputTree.array(outputTree.keys()[1])
        self.assertTrue(2*len(inputBranch) == len(outputBranch))
        shutil.rmtree(tmpdirpath)

    def test_merge_root_pet_incrementEvent(self):
        try:
            import uproot3 as uproot
        except:
            print("uproot3 is mandatory to merge root file. Please, do:")
            print("pip install uproot3")

        logger.info('Test_MergeRoot test_merge_root_pet')
        tmpdirpath = tempfile.mkdtemp()
        filenameRoot = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/pet.root?inline=false", out=tmpdirpath, bar=None)
        gt.merge_root([filenameRoot, filenameRoot],  os.path.join(tmpdirpath, "output.root"))
        input = uproot.open(filenameRoot)
        output = uproot.open(os.path.join(tmpdirpath, "output.root"))
        inputTree = input[input.keys()[0]]
        outputTree = output[output.keys()[0]]
        inputRunBranch = inputTree.array(inputTree.keys()[0])
        outputRunBranch = outputTree.array(outputTree.keys()[0])
        self.assertTrue(max(inputRunBranch) == max(outputRunBranch))
        self.assertTrue(2*len(inputRunBranch) == len(outputRunBranch))
        inputEventBranch = inputTree.array(inputTree.keys()[1])
        outputEventBranch = outputTree.array(outputTree.keys()[1])
        self.assertTrue(2*max(inputEventBranch)+1 == max(outputEventBranch))
        self.assertTrue(2*len(inputEventBranch) == len(outputEventBranch))
        shutil.rmtree(tmpdirpath)

    def test_merge_root_pet_incrementRun(self):
        try:
            import uproot3 as uproot
        except:
            print("uproot3 is mandatory to merge root file. Please, do:")
            print("pip install uproot3")

        logger.info('Test_MergeRoot test_merge_root_pet')
        tmpdirpath = tempfile.mkdtemp()
        print(tmpdirpath)
        filenameRoot = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/pet.root?inline=false", out=tmpdirpath, bar=None)
        gt.merge_root([filenameRoot, filenameRoot],  os.path.join(tmpdirpath, "output.root"), True)
        input = uproot.open(filenameRoot)
        output = uproot.open(os.path.join(tmpdirpath, "output.root"))
        inputTree = input[input.keys()[0]]
        outputTree = output[output.keys()[0]]
        inputRunBranch = inputTree.array(inputTree.keys()[0])
        outputRunBranch = outputTree.array(outputTree.keys()[0])
        self.assertTrue(2*max(inputRunBranch)+1 == max(outputRunBranch))
        self.assertTrue(2*len(inputRunBranch) == len(outputRunBranch))
        inputEventBranch = inputTree.array(inputTree.keys()[1])
        outputEventBranch = outputTree.array(outputTree.keys()[1])
        self.assertTrue(max(inputEventBranch) == max(outputEventBranch))
        self.assertTrue(2*len(inputEventBranch) == len(outputEventBranch))
        #shutil.rmtree(tmpdirpath)

