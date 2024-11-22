
import os
import colorama
import shutil

class ParserMacro:
    def __init__(self):
        self.parserAllFiles = {}
        self.aliasToGate = {}
        self.aliasNumber = 0
        self.parserAlias = {}
        self.parserAttributes = {}
        self.fullMacroDir = ""
        self.copyAppendixMac = []
        self.mainMacroFile = ""

    def parseMainMacFiles(self, fullMacroDir, mainMacroFile):
        self.fullMacroDir = fullMacroDir
        self.mainMacroFile = mainMacroFile
        self.parseMacFiles(os.path.join(self.fullMacroDir, self.mainMacroFile))

    def parseMacFiles(self, currentMacFiles):
        # Structure containing all lines of the macro file
        self.parserAllFiles[currentMacFiles] = []
        with open(os.path.join(self.fullMacroDir, currentMacFiles)) as f:  # open file
            for line in f:
                self.parserAllFiles[currentMacFiles] += [line]
                self.parseControlCommand(line.strip(), len(self.parserAllFiles[currentMacFiles]) - 1, currentMacFiles)
                self.checkIfAppendixMacFile(line.strip())
                self.parseAttributes(line.strip(), len(self.parserAllFiles[currentMacFiles]) - 1, currentMacFiles)

    def parseControlCommand(self, line, index, file):
        # Parse macro file to get /control/ commands
        if not line.startswith('#') and not line == '\n':
            splitLine = line.split(" ")
            splitLine = [x for x in splitLine if x]
            if len(splitLine) > 0 and splitLine[0][:9] == '/control/':
                self.checkControlCommand(splitLine, file, index)

    def checkControlCommand(self, splitLine, file, index):
        if len(splitLine) > 0 and splitLine[0] == '/control/alias':
            self.parseAlias(splitLine)
        elif len(splitLine) > 0 and (splitLine[0] == '/control/strdoif' or
                                     splitLine[0] == '/control/doif' or
                                     splitLine[0] == '/control/loop') :
            condition, newSplitLine = self.parseCondition(splitLine)
            if len(newSplitLine) > 0:
                newLine = " ".join(newSplitLine)
                newLine += '\n'
                if newSplitLine[0][:9] == '/control/':
                    self.checkControlCommand(newSplitLine, file, index)
            self.parserAllFiles[file][index] = self.parserAllFiles[file][index][:-1] + " # " + str(condition) + '\n'
        elif len(splitLine) > 0 and splitLine[0] == '/control/execute':
            self.getMacroFiles(splitLine)
        elif len(splitLine) > 0 and (splitLine[0] == '/control/add' or
                                     splitLine[0] == '/control/subtract' or
                                     splitLine[0] == '/control/multiply' or
                                     splitLine[0] == '/control/divide'):
            value = self.parseOperation(splitLine)
            self.parserAllFiles[file][index] = self.parserAllFiles[file][index][:-1] + " # " + value + '\n'
        elif len(splitLine) > 0 and splitLine[0] != '/control/verbose' and splitLine[0] != '/control/listAlias':
            print(colorama.Fore.YELLOW + "WARNING: "
                  "Ignored /control command: " + splitLine[0] + colorama.Style.RESET_ALL)

    def parseAlias(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/alias':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            self.parserAlias[splitLine[1]] = splitLine[2]

    def parseCondition(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/strdoif':
            #left condition
            splitLine[1] = self.decriptAlias(splitLine[1])
            splitLine[1] = " ".join(splitLine[1])
            #right condition
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            if splitLine[2] == "==":
                if splitLine[1] == splitLine[3]:
                    return True, splitLine[4:]
            elif splitLine[2] == "!=":
                if splitLine[1] != splitLine[3]:
                    return True, splitLine[4:]
            else:
                print(colorama.Fore.YELLOW + "WARNING: Not possible to decrypt: " + " ".join(splitLine) + colorama.Style.RESET_ALL)
            return False, []
        elif len(splitLine) > 0 and splitLine[0] == '/control/doif':
            #left condition
            splitLine[1] = self.decriptAlias(splitLine[1])
            splitLine[1] = float(" ".join(splitLine[1]))
            #right condition
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = float(" ".join(splitLine[3]))
            if splitLine[2] == "==":
                if splitLine[1] == splitLine[3]:
                    return True, splitLine[4:]
            elif splitLine[2] == "!=":
                if splitLine[1] != splitLine[3]:
                    return True, splitLine[4:]
            elif splitLine[2] == ">":
                if splitLine[1] > splitLine[3]:
                    return True, splitLine[4:]
            elif splitLine[2] == ">=":
                if splitLine[1] >= splitLine[3]:
                    return True, splitLine[4:]
            elif splitLine[2] == "<":
                if splitLine[1] < splitLine[3]:
                    return True, splitLine[4:]
            elif splitLine[2] == "<=":
                if splitLine[1] <= splitLine[3]:
                    return True, splitLine[4:]
            else:
                print(colorama.Fore.YELLOW + "WARNING: Not possible to decrypt: " + " ".join(splitLine) + colorama.Style.RESET_ALL)
            return False, []
        elif len(splitLine) > 0 and splitLine[0] == '/control/loop':
            return True, splitLine[1:]


    def getMacroFiles(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/execute':
            splitLine[1] = self.decriptAlias(splitLine[1])
            splitLine[1] = " ".join(splitLine[1])
            self.parseMacFiles(os.path.join(self.fullMacroDir, splitLine[1]))

    def parseOperation(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/add':
            return self.parseAdd(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/subtract':
            return self.parseSubtract(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/multiply':
            return self.parseMultiply(splitLine)
        elif len(splitLine) > 0 and splitLine[0] == '/control/divide':
            return self.parseDivide(splitLine)
        return None

    def parseAdd(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/add':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) + float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseSubtract(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/subtract':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) - float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseMultiply(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/multiply':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) * float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def parseDivide(self, splitLine):
        if len(splitLine) > 0 and splitLine[0] == '/control/divide':
            splitLine[2] = self.decriptAlias(splitLine[2])
            splitLine[2] = " ".join(splitLine[2])
            splitLine[3] = self.decriptAlias(splitLine[3])
            splitLine[3] = " ".join(splitLine[3])
            value = str(float(splitLine[2]) / float(splitLine[3]))
            self.parserAlias[splitLine[1]] = value
            return value

    def checkIfAppendixMacFile(self, line):
        # Check if the line contains a file in mac that is not a /control/execute
        if not line.startswith('#') and not line == '\n':
            splitLine = line.split(" ")
            splitLine = [x for x in splitLine if x]
            if len(splitLine) >= 2 and not splitLine[0].startswith('/control/execute'):
                splitLine = self.decriptAlias(line)
                if splitLine[1].startswith('mac'):
                    splitLine[1] = self.decriptAlias(splitLine[1])
                    splitLine[1] = " ".join(splitLine[1])
                    self.copyAppendixMac.append(os.path.join(self.fullMacroDir, splitLine[1]))

    def parseAttributes(self, line, index, file):
        if not line.startswith('#') and not line == '\n':
            if line.startswith('/gate/application/setTimeStart'):
                self.parserAttributes["setTimeStart"] = [file, index]
            elif line.startswith('/gate/application/setTimeSlice'):
                self.parserAttributes["setTimeSlice"] = [file, index]
            elif line.startswith('/gate/application/setTimeStop'):
                self.parserAttributes["setTimeStop"] = [file, index]
            elif line.startswith('/gate/application/setTotalNumberOfPrimaries'):
                self.parserAttributes["setTotalNumberOfPrimaries"] = [file, index]

    def setAlias(self, alias, jobs):
        if type(alias[1]) == list:
            if len(alias[1]) == jobs:
              self.parserAlias[alias[0]] = str(alias[1][0])
              tempList = list(map(lambda x: str(x), alias[1]))
              self.aliasToGate[alias[0]] = tempList
        else:
            self.parserAlias[alias[0]] = str(alias[1])
            self.aliasToGate[alias[0]] = jobs*[str(alias[1])]
        self.aliasNumber += 1

    def setAttributes(self, attribute, valuesForAllJobs):
        line = self.parserAllFiles[self.parserAttributes[attribute][0]][self.parserAttributes[attribute][1]]
        line = line.strip()
        splitLine = line.split(" ")
        splitLine = [x for x in splitLine if x]
        if not isinstance(valuesForAllJobs[0], list):
            splitLine[1] = '{' + attribute + '_' + str(self.aliasNumber) + '}'
            self.aliasToGate[attribute + '_' + str(self.aliasNumber)] = valuesForAllJobs
            self.aliasNumber += 1
        else:
            for index, value in enumerate(valuesForAllJobs[0]):
                splitLine[index + 1] = '{' + attribute + '_' + str(self.aliasNumber) + '}'
                self.aliasToGate[attribute + '_' + str(self.aliasNumber)] = valuesForAllJobs[:][index]
                self.aliasNumber += 1
        self.parserAllFiles[self.parserAttributes[attribute][0]][self.parserAttributes[attribute][1]] = " ".join(splitLine) + '\n'

    # Return the value of the attribute, not the command
    # Check if containing alias, in such a case, replace it by the alias value if it exist, else raise an error
    def getAttributes(self, attribute):
        line = self.parserAllFiles[self.parserAttributes[attribute][0]][self.parserAttributes[attribute][1]]
        line = line.strip()
        splitLine = self.decriptAlias(line, attribute)
        return splitLine[1:]

    def getAlias(self, alias):
        if not alias in self.parserAlias:
            print(colorama.Fore.RED + "ERROR: alias " + alias + " is not found in macro files" + colorama.Style.RESET_ALL)
            exit(1)
        return self.parserAlias[alias] #Do not return the command and the name of the alias

    def decriptAlias(self, line, attribute=""):
        line = line.split(" ")
        splitLine = []
        for x in line:
            startAliasIndex = x.find('{')
            endAliasIndex = x.find('}')
            if startAliasIndex != -1 and endAliasIndex != 1:
                if startAliasIndex < endAliasIndex:
                    if x[startAliasIndex+1:endAliasIndex] in self.parserAlias:
                        xAlias = x[:startAliasIndex] + self.getAlias(x[startAliasIndex+1:endAliasIndex]) + x[endAliasIndex+1:]
                        splitLine += [xAlias]
                    else:
                        print(colorama.Fore.RED + "ERROR: attribute \"" + x + "\" is an alias " + x[startAliasIndex+1:endAliasIndex] + colorama.Style.RESET_ALL)
                        print(colorama.Fore.RED + "And the alias was not found in macro files" + colorama.Style.RESET_ALL)
                        exit(1)
            elif x:
                splitLine += [x]
        return splitLine

    def setVisualisation(self):
        self.parserAllFiles[os.path.join(self.fullMacroDir, self.mainMacroFile)] = ["/control/execute mac/visu.mac \n"] + self.parserAllFiles[os.path.join(self.fullMacroDir, self.mainMacroFile)]
        shutil.copyfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "visu.mac"), os.path.join(self.fullMacroDir, "mac/visu.mac"))
        self.copyAppendixMac.append(os.path.join(self.fullMacroDir, "mac/visu.mac"))

    def writeMacFiles(self, outputDir):
        for file in self.parserAllFiles:
            writtingFile = file[len(self.fullMacroDir):]
            folder = os.path.dirname(os.path.join(outputDir, writtingFile))
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(outputDir, writtingFile), 'w') as f:
                for element in self.parserAllFiles[file]:
                    f.write(element)

        for file in self.copyAppendixMac:
            writtingFile = file[len(self.fullMacroDir):]
            shutil.copyfile(file, os.path.join(outputDir, writtingFile))
