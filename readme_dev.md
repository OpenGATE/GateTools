


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
    
    
    # For debug, increase manually the verbose level with: 
    
    logger.setLevel(logging.DEBUG)
    
```


