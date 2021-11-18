#!/usr/bin/env python
# coding: utf-8

import itk
import numpy as np
import click


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--imageFile', default='', help='image')
@click.option('-s', '--squaredFile', default='', help='squared image')
@click.option('-n', '--numberOfEvent', default=1, help='number of events')
@click.option('-d', '--default', default=1.0, help='default value')
def mergeUncertaintyImage(imageFile, squaredFile, numberOfEvent, default):
    """
    \b
    Merge Uncertainty image from Gate

    """
    image = itk.imread(imageFile)
    squared = itk.imread(squaredFile)
    mergeUncertaintyImageMain(image, squared, numberOfEvent, default=1.0)


def mergeUncertaintyImageMain(image, squared, numberOfEvent, default):
    imageArray = itk.array_from_image(image)
    squaredArray = itk.array_from_image(squared)
    result = numberOfEvent * squaredArray - imageArray*imageArray
    result = result / (numberOfEvent - 1)
    result = np.sqrt(result)
    result = result / np.abs(imageArray)
    result[result != result] = default
    resultImage = itk.image_from_array(result)
    resultImage.CopyInformation(image)
    return(resultImage)


if __name__ == "__main__":
    colorama.init()
    mergeUncertaintyImage()

