#!/usr/bin/env python
# coding: utf-8

import sys
import re
import datetime
import click

linere = re.compile(r'''^#\s+([a-zA-Z]+)\s+=\s(.*)$''')
mergedlines = ['NumberOfRun', 'NumberOfEvents', 'NumberOfTracks', 'NumberOfSteps', 'NumberOfGeometricalSteps',
               'NumberOfPhysicalSteps', 'ElapsedTimeWoInit', 'ElapsedTime', 'StartDate', 'EndDate',
               'NumberOfMergedJobs', 'MeanPPS', 'MeanElapsedTime', 'MinElapsedTime', 'MaxElapsedTime']


def total_seconds(deltat):
    try:
        return float(deltat.total_seconds())
    except AttributeError: # total_seconds defined in 2.7
        total = 0.
        total += deltat.seconds
        total += deltat.microseconds*1e-6
        total += deltat.days*3600.*24.
        return total

def parse_stat_file(filenames):
    keys = {}
    for filename in filenames:
        keys[filename] = {}
        for line in open(filename,"r").readlines():
            match = linere.match(line)
            #assert(match is not None)
            if match is None:
                continue
            groups = match.groups()
            if groups[0] not in mergedlines:
                continue
            keys[filename] [groups[0]]=groups[1]
    return keys

def merge_keys(ikeys):
    mindate = None
    maxdate = None
    keys = {}
    for line in mergedlines:
        value = None

        if line == 'NumberOfMergedJobs':
            try:
                value = str(len(ikeys.keys()))
            except KeyError:
                value = str(2)

        if line == 'MeanPPS':
            meanPPS = 0
            for filename in ikeys.keys():
                try:
                    meanPPS += int(ikeys[filename]['NumberOfEvents']) / float(ikeys[filename]['ElapsedTime'])
                except ValueError:
                    meanPPS = -1
                    break
            if not meanPPS == -1:
                value = str(meanPPS/len(ikeys.keys()))

        if line == 'MeanElapsedTime':
            MeanElapsedTime = 0
            for filename in ikeys.keys():
                try:
                    MeanElapsedTime += float(ikeys[filename]['ElapsedTime'])
                except ValueError:
                    MeanElapsedTime = -1
                    break
            if not MeanElapsedTime == -1:
                value = str(MeanElapsedTime/len(ikeys.keys()))

        if line == 'MinElapsedTime':
            MinElapsedTime = 1e20
            for filename in ikeys.keys():
                try:
                    MinElapsedTime = min(float(ikeys[filename]['ElapsedTime']), MinElapsedTime)
                except ValueError:
                    MinElapsedTime = -1
                    break
            if not MinElapsedTime == -1:
                value = str(MinElapsedTime)

        if line == 'MaxElapsedTime':
            MaxElapsedTime = 0
            for filename in ikeys.keys():
                try:
                    MaxElapsedTime = max(float(ikeys[filename]['ElapsedTime']), MaxElapsedTime)
                except ValueError:
                    MaxElapsedTime = -1
                    break
            if not MaxElapsedTime == -1:
                value = str(MaxElapsedTime)

        if line == 'StartDate' or line == 'EndDate':
            tmp_mindate = datetime.datetime.strptime("Tue Nov 16 1:0:0 3000", "%a %b %d %H:%M:%S %Y")
            tmp_maxdate = datetime.datetime.strptime("Tue Nov 16 1:0:0 1000","%a %b %d %H:%M:%S %Y")
            for filename in ikeys.keys():
                tmp_date = datetime.datetime.strptime(ikeys[filename][line],"%a %b %d %H:%M:%S %Y")
                if line=="StartDate":
                    value = min(tmp_date, tmp_mindate)
                    tmp_mindate = value
                    mindate = tmp_mindate
                if line=="EndDate":
                    value = max(tmp_date, tmp_maxdate)
                    tmp_maxdate = value
                    maxdate = tmp_maxdate
            value = value.strftime("%a %b %d %H:%M:%S %Y")

        if value is None:
            value = 0
            for filename in ikeys.keys():
                try:
                    value += int(ikeys[filename][line])
                except ValueError:
                    value = None
                    break
            if value is not None:
                value = str(value)

        if value is None:
            value = 0
            for filename in ikeys.keys():
                try:
                    value += float(ikeys[filename][line])
                except ValueError:
                    value = None
                    break
            if value is not None:
                value = str(value)

        assert(value is not None)
        keys[line] = value
    if mindate is not None and maxdate is not None:
        speedup = float(keys["ElapsedTime"])/total_seconds(maxdate-mindate)
        keys["Speedup"] = str(speedup)
    return keys

def format_keys(keys):
    output = "\n".join("# %s = %s" % (line,keys[line]) for line in mergedlines)
    if "Speedup" in keys:
        output += "\n# Speedup = %s" % keys["Speedup"]
    return output

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-o', '--output', default='', help='Output merged file')
@click.argument('inputs', type=click.Path(dir_okay=False), required=True, nargs=-1)
def mergeStatFile(inputs, output):
    """
    \b
    Merge Stats file from Gate

    """
    mergeStatFileMain(inputs, output)


def mergeStatFileMain(inputs, output):
    ikeys = parse_stat_file(inputs)
    keys  = merge_keys(ikeys)
    outputFile = format_keys(keys)
    open(output,"w").write(outputFile)

if __name__ == "__main__":
    colorama.init()
    mergeStatFile()
