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

def cleanup():
    honeycopy.cleanup()

def printHelp():
    print "Command Line Utility for predefined Cloudstack Functions"
    print ""
    print "Options:"
    print "create                       - Creates the Honeypot"
    print "clone                        - creates two copys of the honeypot"
    print "start                        - starts the VMs and starts recording"
    print "cleanup                      - removes the VMs (without removing the collected data)"
    return 

options = {"create": create,
           "clone": clone,
           "start": start,
           "cleanup": cleanup
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


