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
        name = key.split(";")
        if len(name) > 2:
            name = ";".join(name)
        else:
            name = name[0]
        if not name in root_array:
            root_array.append(name)
    return(root_array)

def merge_root(rootfiles, outputfile, incrementRunId=False):
    """
    Merge root files in output files
    """
    try:
        import uproot
    except:
        print("uproot4 is mandatory to merge root file. Please, do:")
        print("pip install uproot")

    uproot.default_library = "np"

    out = uproot.recreate(outputfile)

    #Previous ID values to be able to increment runIn or EventId
    previousId = {}

    #create the dict reading all input root files
    trees = {} #TTree with TBranch
    hists = {} #Directory with THist
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
                    hists[tree] = {}
                    hists[tree]["rootDictType"] = {}
                    hists[tree]["rootDictValue"] = {}
                    previousId[tree] = {}
                for branch in root[tree].keys():
                    if isinstance(root[tree],uproot.reading.ReadOnlyDirectory):
                        array = root[tree][branch].values()
                        if len(array) > 0:
                            branchName = tree + "/" + branch
                            if type(array[0]) is type('c'):
                                array = np.array([0 for xi in array])
                            if not branchName in hists[tree]["rootDictType"]:
                                hists[tree]["rootDictType"][branchName] = root[tree][branch].to_numpy()
                                hists[tree]["rootDictValue"][branchName] = np.zeros(array.shape)
                            hists[tree]["rootDictValue"][branchName] += array
                    else:
                        array = root[tree][branch].array(library="np")
                        if len(array) > 0 and not (type(array[0]) is type(np.ndarray(2,))):
                            if type(array[0]) is type('c'):
                                array = np.array([0 for xi in array])
                            if not branch in trees[tree]["rootDictType"]:
                                trees[tree]["rootDictType"][branch] = type(array[0])
                                trees[tree]["rootDictValue"][branch] = np.array([])
                            if (not incrementRunId and branch.startswith('eventID')) or (incrementRunId and branch.startswith('runID')):
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
            #out.mktree(tree, trees[tree]["rootDictType"])
            out[tree] = trees[tree]["rootDictValue"]
    for hist in hists:
        if not hists[hist]["rootDictValue"] == {} or not hists[hist]["rootDictType"] == {}:
            for branch in hists[hist]["rootDictValue"]:
                for i in range(len(hists[hist]["rootDictValue"][branch])):
                    hists[hist]["rootDictType"][branch][0][i] = hists[hist]["rootDictValue"][branch][i]
                out[branch[:-2]] = hists[hist]["rootDictType"][branch]


#####################################################################################
import unittest
import tempfile
import wget
import os
import shutil
import numpy as np
from .logging_conf import LoggedTestCase

class Test_MergeRoot(LoggedTestCase):
    def test_merge_root_phsp(self):
        try:
            import uproot
        except:
            print("uproot4 is mandatory to merge root file. Please, do:")
            print("pip install uproot")

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
        inputBranch = inputTree[inputTree.keys()[1]].array(library="np")
        outputBranch = outputTree[outputTree.keys()[1]].array(library="np")
        self.assertTrue(2*len(inputBranch) == len(outputBranch))
        shutil.rmtree(tmpdirpath)

    def test_merge_root_pet_incrementEvent(self):
        try:
            import uproot
        except:
            print("uproot4 is mandatory to merge root file. Please, do:")
            print("pip install uproot")

        logger.info('Test_MergeRoot test_merge_root_pet')
        tmpdirpath = tempfile.mkdtemp()
        filenameRoot = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/pet.root?inline=false", out=tmpdirpath, bar=None)
        gt.merge_root([filenameRoot, filenameRoot],  os.path.join(tmpdirpath, "output.root"))
        input = uproot.open(filenameRoot)
        output = uproot.open(os.path.join(tmpdirpath, "output.root"))
        inputTree = input[input.keys()[0]]
        outputTree = output[output.keys()[0]]
        inputRunBranch = inputTree[inputTree.keys()[0]].array(library="np")
        outputRunBranch = outputTree[outputTree.keys()[0]].array(library="np")
        self.assertTrue(max(inputRunBranch) == max(outputRunBranch))
        self.assertTrue(2*len(inputRunBranch) == len(outputRunBranch))
        inputEventBranch = inputTree[inputTree.keys()[1]].array(library="np")
        outputEventBranch = outputTree[outputTree.keys()[1]].array(library="np")
        self.assertTrue(2*max(inputEventBranch)+1 == max(outputEventBranch))
        self.assertTrue(2*len(inputEventBranch) == len(outputEventBranch))
        shutil.rmtree(tmpdirpath)

    def test_merge_root_pet_incrementRun(self):
        try:
            import uproot
        except:
            print("uproot4 is mandatory to merge root file. Please, do:")
            print("pip install uproot")

        logger.info('Test_MergeRoot test_merge_root_pet')
        tmpdirpath = tempfile.mkdtemp()
        print(tmpdirpath)
        filenameRoot = wget.download("https://gitlab.in2p3.fr/opengate/gatetools_data/-/raw/master/pet.root?inline=false", out=tmpdirpath, bar=None)
        gt.merge_root([filenameRoot, filenameRoot],  os.path.join(tmpdirpath, "output.root"), True)
        input = uproot.open(filenameRoot)
        output = uproot.open(os.path.join(tmpdirpath, "output.root"))
        inputTree = input[input.keys()[0]]
        outputTree = output[output.keys()[0]]
        inputRunBranch = inputTree[inputTree.keys()[0]].array(library="np")
        outputRunBranch = outputTree[outputTree.keys()[0]].array(library="np")
        self.assertTrue(2*max(inputRunBranch)+1 == max(outputRunBranch))
        self.assertTrue(2*len(inputRunBranch) == len(outputRunBranch))
        inputEventBranch = inputTree[inputTree.keys()[1]].array(library="np")
        outputEventBranch = outputTree[outputTree.keys()[1]].array(library="np")
        self.assertTrue(max(inputEventBranch) == max(outputEventBranch))
        self.assertTrue(2*len(inputEventBranch) == len(outputEventBranch))
        #shutil.rmtree(tmpdirpath)

