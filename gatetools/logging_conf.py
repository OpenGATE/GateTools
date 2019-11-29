# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

"""
This module contains the default logging configuration for the Gate tools.
It is used by the command line tools and you *can* use it for your own
python scripts based on the gatetools modules. You can of course also define
your own logging configuration.
"""

# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------


import logging
from datetime import datetime
import os, sys
import click

_logging_is_already_configured = False

def logging_conf(verbose=False,logfile=""):
    """
    This function is supposed to be called only once, inside the main function
    of your application.

    By default, the logging level is high (i.e. low verbosity) and no logging file
    will be produced.

    You can choose to increase the terminal output (verbose=True). This lowers
    the log level to "INFO". This is not the lowest possible logging level.
    With debugging mode off, the logging messages will be displayed without any
    prefix, i.e. as if they were printed with the "print()" function. With
    debugging mode on, then you get a lengthy prefix that shows you details
    like the module name, line number, date and time.  Terminal output and
    logging file get the same prefix, in order to facilitate finding back
    events in the log file.

    The debugging mode is enabled when the `logfile` argument is a non-empty
    string containing the desired file path the log file (in a directory where
    the user should have write permissions). If the file already exists, then
    the logging information will be *appended*. If the `logfile` argument is
    equal to "auto" then a log file name in the current working directory will
    be generated, composed of the basename of the main script and a prefix
    ".PID.YYMMDD.HHMMSS.log", where PID, YYMMDD and HHMMSS are the process ID,
    date and time, respectively.

    Note that the `verbose` flag only controls how much information is streamed
    to terminal; the log file always contains the full debug-level information.
    """
    global _logging_is_already_configured
    if _logging_is_already_configured:
        logger=logging.getLogger(__name__)
        logger.debug("attempt to re-configure logging ignored...")
        return

    stdout_loglevel = logging.INFO if verbose else logging.WARNING
    if not bool(logfile):
        logging.basicConfig(format='%(message)s',level=stdout_loglevel)
        return
    else:
        logger = logging.getLogger() # get root logger
        logger.setLevel(logging.DEBUG)
        # same format for terminal and for log file
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        # terminal output
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(stdout_loglevel)
        logger.addHandler(sh)
        # log file
        if logfile == "auto":
            logfiledir = os.path.realpath(os.getcwd())
            logfilename = os.path.basename(sys.argv[0])
            logfilename += "."+str(os.getpid())+datetime.now().strftime(".%Y%m%d.%H%M%S.log")
            logfilepath = os.path.join(logfiledir,logfilename)
        else:
            logfilepath = os.path.realpath(logfile)
        # check disk space before trying to open log file ("df" = "disk free")
        # TODO: if it turns out that `psutil` is available on practically all systems
        # then we can maybe use that here too, it has a nicer interface.
        vfs=os.statvfs(os.path.dirname(logfilepath))
        MiB=1024*1024
        GiB=1024*MiB
        df = vfs.f_bsize*vfs.f_bavail
        if df < 100*MiB: # totally arbitrary minimum
            raise RuntimeError("Looks like you are very low on disk space, abort...")
        try:
            fh = logging.FileHandler(logfilepath)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            logger.error("failed to open debugging log file {}".format(os.path.realpath(logfilepath)))
            logger.error("got exception: '{}'".format(e))
            logger.exception("stack trace:")
            logger.critical("please make sure that the log file path is correct, that there is space on the device and that you have write permissions on it.")
            raise
        # logging is now configured
        # start with logging some system basics that could possibly be useful for debugging
        logger.debug("start logging")
        logger.debug("OS: {}".format(os.uname()))
        logger.debug("python version: {}".format(sys.version))
        logger.debug("#cpus: {}".format(os.cpu_count()))
        logger.debug("load averages: {}".format(str(os.getloadavg())))
        logger.debug("free disk space in log file directory: {0:.2f} GiB ({1:d} MiB)".format(df/GiB,int(df/MiB)))
        logger.debug("full logfile path: {}".format(logfilepath))
        logger.debug("cwd: {}".format(os.getcwd()))
        logger.debug("script: {}".format(sys.argv[0]))
        try:
            import itk
            logger.debug("ITK: {}".format(itk.Version.GetITKVersion()))
            import pydicom
            logger.debug("pydicom: {}".format(".".join(pydicom.__version_info__)))
            import numpy
            logger.debug("numpy: {}".format(numpy.__version__))
            import psutil
            meminfo=psutil.virtual_memory()
            logger.debug("RAM: total={} MiB, available={} MiB ({} % used)".format(meminfo.total/MiB,meminfo.available/MiB,meminfo.percent))
            # TODO: should we emit a warning if we see that available RAM is very low?
        except ImportError as ie:
            logger.warning("oopsie: {}".format(ie))
            logger.warning("trying to continue, keep fingers crossed...")
    _logging_is_already_configured = True



def add_options(options):
    '''
    Function to add all common options to click.

    Current options are --verbose and --log
    '''
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

common_options= [
    click.option('--verbose/--quiet','-v/-q', default=False,
                 help='Be verbose (-v) or keep quiet (-q, default)'),
    click.option('--logfile', required=False, default="",
                 help='Path of debugging log file. Default: empty (no log file is written). If you specify "auto" then an informative logfile name will be generated automatically.')
]


###############################################################################
import unittest
class LoggedTestCase(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        logfilename=f'unittest.{os.getpid()}.log'
        logging_conf(verbose=False, logfile=logfilename)
        unittest.TestCase.__init__(self,*args,**kwargs)
