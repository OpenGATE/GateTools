


# Logging

Instead of using print, please use the following logging system. Consider a command line as example. 

```
    # Step 1: near the import section, import the logging system as follows
    
    import logging
    logger=logging.getLogger(__name__)
    
    
    # Step 2: for the click function, add the common options and **kwargs 
    
    @gt.add_options(gt.common_options)
    def gt_my_cool_tool(mypara, **kwargs):
        ...
    
    
    # Step 3: add the following at the beginning of your command line tools
    
    gt.logging_conf(**kwargs)
    
    
    # Step4: instead of print, use the following
    
    logger.info('This is print if --verbose is used')
    logger.debug('This is only print if the log level is set (see after)')
    logger.warning('This is always printed')
    logger.error('This is printed and fail')
    
    
    # For debugging, run your tool with a logfile:
    $ gt_my_cool_tool --logfile=foobar.log

    # In the log file you will find the output from all log messages, including the logger.debug(..) ones.
    #
    # Note that if you provide the name of an already existing log file, the
    # new logging information will be *appended*, it will not overwrite the old logfile.
    #
    # If you do not like the dual logging setup and prefer to get all logging
    # messages to standard output, then you can simply replace the
    # `gt.logging_conf(**kwargs)` line with:
    logging.basicConfig(level=logging.DEBUG)
    
```


# Logging

Unit tests. We need some text here about how to write unit tests.
