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
try:
  import uproot3 as uproot
except:
  print("uproot3 is mandatory to merge root file. Please, do:")
  print("pip install uproot3")
import numpy as np
import tqdm
import logging
logger=logging.getLogger(__name__)

def merge_root(rootfiles, outputfile):
    """
    Merge root files in output files
    """
    out = uproot.recreate(outputfile)

    #create the dict reading all input root files
    trees = {}
    pbar = tqdm.tqdm(total = len(rootfiles))
    for file in rootfiles:
        root = uproot.open(file)
        for tree in root.keys():
            if hasattr(root[tree], 'keys'):
                if not tree in trees:
                    trees[tree] = {}
                    trees[tree]["rootDictType"] = {}
                    trees[tree]["rootDictValue"] = {}
                for branch in root[tree].keys():
                    array = root[tree].array(branch)
                    if len(array) > 0:
                        if type(array[0]) is type(b'c'):
                            array = np.array([0 for xi in array])
                        if not branch in trees[tree]["rootDictType"]:
                            trees[tree]["rootDictType"][branch] = type(array[0])
                            trees[tree]["rootDictValue"][branch] = np.array([])
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
try:
  import uproot3 as uproot
except:
  print("uproot3 is mandatory to merge root file. Please, do:")
  print("pip install uproot3")
from .logging_conf import LoggedTestCase

class Test_MergeRoot(LoggedTestCase):
    def test_merge_root(self):
        logger.info('Test_MergeRoot test_merge_root')
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
