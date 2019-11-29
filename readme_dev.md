When developing, install with: `pip install -e .`

Dependencies:
- click: https://click.palletsprojects.com
- uproot: https://github.com/scikit-hep/uproot
- pydicom: https://pydicom.github.io/
- tqdm: https://github.com/tqdm/tqdm
- colored: https://gitlab.com/dslackw/colored
- itk: https://itk.org/
- numpy https://numpy.org/
- matplotlib https://matplotlib.org/


# Logging

Instead of using print, please use the following [logging](https://docs.python.org/3/library/logging.html) system. Consider a command line as example. 

```
    # Step 1: near the import section, import the logging system as follows (in each tool and each module)
    
    import logging
    logger=logging.getLogger(__name__)
    
    
    # Step 2: for the click function, add the common options and **kwargs 
    
    @gt.add_options(gt.common_options)
    def gt_my_cool_tool(mypara, **kwargs):
        ...
    
    
    # Step 3: add the following at the beginning of your command line tools:
    
    gt.logging_conf(**kwargs)
    
    
    # Step4: instead of print, use the following (in tools and in modules)
    
    logger.info('This is print if --verbose is used')
    logger.debug('This is only written into the logfile, or to screen if tweak the logger settings.')
    logger.warning('This is always printed')
    logger.error('This is always printed and should be followed by program exit.')
```

For debugging, run your tool with a logfile (or: ask the user who reports a problem to run the tool with a logfile and send that logfile to you):

```
$ gt_my_cool_tool --logfile=foobar.log <other args>
```

In the log file you will find some system information (hardware specs, versions
of installed modules) and the output from all log messages, including the
logger.debug(..) ones.  Note that if you provide the name of an already
existing log file, the new logging information will be *appended*, it will not
overwrite the old logfile. If you use "auto" for the logfile name, then a
sufficiently unique logfilename will be generated containing the name of the
tool, the PID, date and time.

During development it can sometimes be useful to tweak the console stream
handler and the file stream handler separately:
```
    gt.logging_conf(verbose=True,logfile="auto")
    logger=logging.getLogger() # get root logger
    logger.handlers[0].setLevel(logging.DEBUG)
    logger.handlers[1].setLevel(logging.INFO)

```

Alternatively, you can define your own logging configuration (at least during tool development), if you like.
For instance, to just get all logging messages (including logging.debug) to standard output (not to file), then simply replace the
```
gt.logging_conf(**kwargs)
```
line with:
```
logging.basicConfig(level=logging.DEBUG)
```

# Unit tests

The functions and classes defined in the `gatetools` modules are tested using
the [`unittest`](https://docs.python.org/3/library/unittest.html) module from
the Python standard library.  As a minimum, the 'normal use' of the
functionality is tested by defining simple input data and verifying that output
agrees with the expectation.  The 'unit' in 'unit test' refers to the most elementary
operations and structures in your code.  Ideally the writing of unit tests will
inspire you to break up large blocks of code into smaller "units" that can be tested
individually.

We chose to implement unit tests directly in the code of each module in `gatetools`.
Groups of unit tests are created by defining subclasses of [`unittest.TestCase`](https://docs.python.org/3/library/unittest.html#unittest.TestCase).
The tests are defined in methods with names that start with "test_". In these tests you create objects
like you would in code that uses the module, and then `assert*` methods can be used
to verify that the code behaves correctly, and to print loud and informative error messages otherwise.
Since `unittest` disables the normal use of stdout, we defined a LoggedTestCase class
which uses `logging_conf` to define a logfile so that all debug messages can be found in
a logfile called `unittest.{PID}.log`.

You can run all unit tests (may take a few minutes) by running:
```
$ python3 -m unittest gatetools
.........................
----------------------------------------------------------------------
Ran 25 tests in 60.806s

OK
```
In the output above, all is fine. Each dot `.` is printed during the execution of a
`unittest.TestCase`. If some tests fail, then you'll see loud error messages. If you are
eager to see when which test is executed, add a `-v` option. In order to run only the
tests of one particular module, or even a particular test case or test, you add the
names of those, separated by dots:
```
$ python3 -m unittest gatetools.gamma_index.Test_GammaIndex3dIdenticalMesh.test_scaling
.
----------------------------------------------------------------------
Ran 1 test in 0.053s

OK
```

