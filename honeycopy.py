#!/usr/bin/python

import sys
import CustomFunctions

honeycopy = CustomFunctions.HoneyCopy()


def create():
    try:
        honeycopy.createHoneypot(sys.argv[2])
    except IndexError:
        print "missing second argument, please provide the os (ubuntu | windows)"

def clone():
    honeycopy.clone()

def start():
    honeycopy.start()

def listSnapshots():
    try:
        vm.setVm(sys.argv[2])
        vm.listAllSnapshots(cloudstack)
    except IndexError:
        print "missing second argument, please provide the VM ID"

def revert():
    try:
        vm.setVm(sys.argv[2])
        vm.stopVm(cloudstack)
        vm.revertSnapshot(cloudstack, sys.argv[3])
        vm.startVm(cloudstack)
    except IndexError:
        print "missing argument, please provide the snapshot ID and the VM ID"

def createinitialsnapshot():
    try:
        if sys.argv[2] != "all":
            vm.setVm(sys.argv[2])
        else:
            vm.setForAll(True)

        vm.createInitialSnapshot(cloudstack)
    except IndexError:
        print "missing argument, please provide the snapshot ID and the VM ID"

def printHelp():
    print "Command Line Utility for predefined Cloudstack Functions"
    print ""
    print "Options:"
    print "create                       - Creates the Honeypot"
    print "clone                        - creates two copys of the honeypot"
    print "start                        - starts the VMs and starts recording"
    return 

options = {"create": create,
           "clone": clone,
           "start": start
           # "listsnapshots":listSnapshots,
           # "createinitialsnapshot":createinitialsnapshot,
           # "help": printHelp,
           # "-h": printHelp,
           # "-help": printHelp,
           # "revert":revert
           }

if len(sys.argv) < 2:
    printHelp()
else:
    try:
        options[sys.argv[1]]()
    except KeyError:
        print "%s is not a valid option, try again (-h for Help)" % sys.argv[1]


