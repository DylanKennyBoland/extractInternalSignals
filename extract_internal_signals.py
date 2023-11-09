#!/usr/bin/env python3

# Author: Dylan Boland

# Modules that will be useful
import argparse
import os
import sys
import re
import csv

# ==== Some General-info Strings ====
# Tags - define these here so they can be quickly and easily changed
errorTag   = """\t***Error: """
successTag = """\t***Success: """
infoTag    = """\t***Info: """

# Standard help & error messages
helpMsg    = infoTag + """The path to the Verilog or SystemVerilog module should be
given after using the '--filename' switch."""
noArgsMsg  = errorTag + """No input arguments were specified. Please use '--filename' followed
\tby the name of the module to be inspected."""
noSuchFileMsg   = errorTag + """The module file '{}' could not be located - double-check the name or file path."""
fileReadSuccess = successTag + """The module file was read in successfully."""
fileReadError   = errorTag + """The module file could not be read in successfully."""
moduleNameNotIdentified = errorTag + """The module name could not be identified. Please ensure that you have used
a standard or conventional structure. Setting the module name to {} for now
"""

noInternalWiresIdentified = infoTag + """No internal wire declarations were found"""
noInternalRegsIdentified = infoTag + """No internal register declarations were found"""

internalSignalsSummaryMsg = """
\n===========================================================================
\t\t{} Internal Signals Information
\t\tTotal number of wires: {}
\t\tTotal number of registers: {}
\t\tTotal number of internal signals: {}
==========================================================================="""

internalWiresHeader = """
\n===========================================================================
\t\tInternal Wires of {}
==========================================================================="""

internalRegsHeader = """
\n===========================================================================
\t\tInternal Registers of {}
==========================================================================="""

# Instantiated module print-out message
jobDoneMsg = """
\n===========================================================================
\tAdditionally, you can see the internal signals below!
==========================================================================="""

# Goodbye message
goodbyeMsg = """
========================================================================================================
\tSuccess! The list of internal signals is in {}.
\t The list can also be found in CSV format in {}.
========================================================================================================"""

# Function to handle the input arguments
def parseArguments():
    parser = argparse.ArgumentParser(description = "The file containing the Verilog or SystemVerilog module description.")
    parser.add_argument('--filename', type = str, help = helpMsg)
    return parser.parse_args()

if __name__ == "__main__":
    args = parseArguments() # parse the input arguments (if there are any)
    if len(sys.argv) == 1:
        print(noArgsMsg)
        exit()
    moduleFileName = args.filename # get the file name (or path) from the input arguments
    
    # ==== Check if the File (path) Exists ====
    if os.path.isfile(moduleFileName) is False:
        print(noSuchFileMsg.format(moduleFileName))
        exit()
    
    # ==== Try to Read the Module File in ====
    with open(moduleFileName) as p:
        try:
            moduleContents = p.read() # read the file into a string
            print(fileReadSuccess)
        except:
            print(fileReadError)
            exit()
    
    # ==== Define the Patterns that we will use to extract the relevant information ====
    # Note: The patterns for extracting the internal wire and register signals use an idea called
    # "negative lookbehind".
    #
    # Essentially, if we think we have found something that we are looking for, then look behind (backwards) and
    # and make sure some other pattern has not occurred.
    #
    # We want to extract the signal name and dimension associated with each "wire" and "reg" declaration, but we want
    # to ensure that we do not capture any of the inputs or outputs. As a result, if we find the pattern "wire" or "reg" we
    # will make sure it is not preceded by "input " or "output ".
    #
    # Given that there can be more than a single white space between "input" and "wire", we need to account for cases such
    # as those shown below:
    #
    # input   wire <signal_name>
    # input          wire <signal_name>
    # output                         reg <signal_name> // not great practice to have so many spaces, but it could happen
    #
    # Unfortunately, the "re" module in Python does not support variable-length negative-lookbehind expressions. As a result, we will
    # write a long regular expression by formatting a string inside a 'for' loop.
    #
    # Example:
    #    r'(?<!input)(?<!input\s{1})(?<!input\s{2})wire<rest_regular_expression>) <- "inputwire", "input wire" and "input  wire" will NOT be matched
    #
    internalWiresPatternRawStr = r""
    internalRegsPatternRawStr = r""
    maxNumWhiteSpaces = 16 # the maximum number of white spaces that we expect between the port type ("input"/"output") and the signal name
    for i in range(0, maxNumWhiteSpaces + 1):
        internalWiresPatternRawStr += "(?<!input\s{{{}}})(?<!output\s{{{}}})".format(i, i)
    
    # Completing the regular expression by concatenating the final segment below
    internalWiresPatternRawStr += "wire\s*(\[[`a-zA-Z0-9\_\-\+\:\*/ ]+\](?:[ ]*)?){0,2}\s+([a-zA-Z\_0-9\$]+)\s*;?"
    # The regular expression for extracting the internal registers is the same as that used for the internal
    # wires, only we need to look for "reg" instead of "wire"
    internalRegsPatternRawStr = internalWiresPatternRawStr.replace("wire", "reg")
    moduleNamePattern    = re.compile(r'(?<!(?: |/|[a-zA-Z\_]))module\s+(?:\$\[PREFIX\])?([a-zA-Z\_0-9]+)[\n\s]*#?[\n\s]*\(')
    internalWiresPattern = re.compile(internalWiresPatternRawStr)
    internalRegsPattern = re.compile(internalRegsPatternRawStr)    
    
    # ==== Extract the Module Name first ====
    matches = re.findall(moduleNamePattern, moduleContents)
    # ==== Check that only one Match was found for the Module Name ====
    if (len(matches) != 1):
        moduleName = "module"
        print(moduleNameNotIdentified.format(moduleName))
    else:
        moduleName = matches[0] # store the module name
    
    # ==== Extract the Internal Wire Signals ====
    matches = re.findall(internalWiresPattern, moduleContents)
    if (len(matches) == 0): # if there were no matches
        internalWiresFound = False
        print(noInternalWiresIdentified) # print a message saying that no internal wire declarations were found
    else:
        internalWiresFound = True
        internalWires = matches # capture the list of internal wires
        numInternalWires = len(internalWires)
    
    # ==== Extract the Internal Register Signals ====
    matches = re.findall(internalRegsPattern, moduleContents)
    if (len(matches) == 0): # if there were no matches
        internalRegsFound = False
        print(noInternalRegsIdentified) # print a message saying that no internal register declarations were found
    else:
        internalRegsFound = True
        internalRegs = matches # capture the list of internal registers
        numInternalRegs = len(internalRegs)
        
    numInternalSignals = numInternalRegs + numInternalWires

    internalRegNames = []
    for i in range(0, numInternalRegs):
        signalName = internalRegs[i][1]
        internalRegNames.append(signalName)
    
    # Remove duplicate entries by converting the list to a set and then back to a list. In a set, each element
    # only appears once. The duplicate entries occur when the script is called on the pre-processed
    # RTL (the same signal can be declared in multiple locations in 'if' and 'else' blocks)
    internalRegNames = list(set(internalRegNames))
    numUniqueRegNames = len(internalRegNames)

    internalWireNames = []
    for i in range(0, numInternalWires):
        signalName = internalWires[i][1]
        internalWireNames.append(signalName)

    # Remove duplicate entries by converting the list to a set and then back to a list. In a set, each element
    # only appears once. The duplicate entries occur when the script is called on the pre-processed
    # RTL (the same signal can be declared in multiple locations in 'if' and 'else' blocks)
    internalWireNames = list(set(internalWireNames))
    numUniqueWireNames = len(internalWireNames)

    internalSignalNames = internalWireNames + internalRegNames
    numUniqueSignalNames = len(internalSignalNames)

    # ==== Write the list of Internal Signals to a CSV file ====
    # <signal_name>, <signal_dimension>
    internalSignals = internalWires + internalRegs # list concatenation (combining two lists)
    internalSignalsDict = {}
    for i in range(0, numInternalSignals):
        signalDimension = internalSignals[i][0]
        signalName = internalSignals[i][1]
        internalSignalsDict[signalName] = signalDimension
    outputCsvFileName = moduleName + "_internal_signals.csv"
    with open(outputCsvFileName, 'w') as p:
        writer = csv.writer(p)
        writer.writerow(["Field Name", "Field Dimension"])
        for key, value in internalSignalsDict.items():
            writer.writerow([key, value])

    # ==== Form the part of the string with all the Internal Wires ====
    # Give the signal name followed by its dimension
    internalWiresStr = ""
    if (internalWiresFound):
        numInternalWires = len(internalWires)
        internalWiresStr = internalWiresHeader.format(moduleFileName) + "\n\n"
        for wireName in internalWires:
            internalWiresStr += f"{wireName[1]}   {wireName[0]}" + "\n"

    # ==== Form the part of the string with all the Internal Registers ====
    # Again, give the signal name followed by its dimension
    internalRegsStr = ""
    if (internalRegsFound):
        numInternalRegs = len(internalRegs)
        internalRegsStr = internalRegsHeader.format(moduleFileName) + "\n\n"
        for regName in internalRegs:
            internalRegsStr += f"{regName[1]}   {regName[0]}" + "\n"

    # ==== Form the Output String ====
    outputStr = internalWiresStr + internalRegsStr
    outputFileName = moduleName + "_internal_signals.txt" # name of the file to which we will write
    with open(outputFileName, "w") as p: # create (or open) the file in "write" mode
        p.write(outputStr)
        print(goodbyeMsg.format(outputFileName, outputCsvFileName))
        print(internalSignalsSummaryMsg.format(moduleName, numUniqueWireNames, numUniqueRegNames, numUniqueSignalNames))
