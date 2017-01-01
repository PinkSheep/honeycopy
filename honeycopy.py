#!/usr/bin/python

import sys
import CustomFunctions

honeycopy = CustomFunctions.HoneyCopy()


def create():
    honeycopy.createHoneypot()

def clone():
    honeycopy.clone()

def start():
    try:
        if sys.argv[2] != "all":
            vm.setVm(sys.argv[2])
            vm.stopVm(cloudstack)
            vm.createSnapshot(cloudstack, sys.argv[3])
            vm.startVm(cloudstack)
    except IndexError:
        print "missing argument, please provide the VM ID and the name of the snapshot"

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
    print "restart {vmid}               - restartcommand for VMs"
    print "createsnapshot {vmid} {name} - creates a snapshot"
    print "revert {vmid} {snapshotid}   - reverts the VM to a snapshot"
    print "createinitialsnapshot {vmid|all} - creates an initial Snapshot"    

options = {"create": create,
           "clone": clone
           # "createsnapshot": createSnapshot,
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


