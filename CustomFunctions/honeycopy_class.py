import sys
import time
import shutil
import os
import errno
import subprocess

class HoneyCopy(object):
    def __init__(self):
        return


    def createHoneypot(self):
        if not os.path.exists("vm"):
            os.makedirs("vm")

        shutil.copyfile("ubuntu.box", "vm/ubuntu.box")
        os.chdir("vm")
        subprocess.check_output(["vagrant", "box", "add", "ubuntu", "ubuntu.box"], stderr=subprocess.STDOUT)
        subprocess.check_output(["vagrant", "init", "ubuntu.box"], stderr=subprocess.STDOUT)
        subprocess.check_output(["vagrant", "up"])
        subprocess.check_output(["vagrant", "halt"])
        shutil.copyfile("../Vagrantfile_ubuntu", "Vagrantfile")
        return

    def clone(self):
        os.chdir("vm")

        if not os.path.exists("clone1"):
            os.makedirs("clone1")

        if not os.path.exists("clone2"):
            os.makedirs("clone2")

        subprocess.check_output(["vagrant", "package", "--output", "ubuntu_clone.box", "--vagrantfile", "../Vagrantfile_ubuntu_clone"])
        shutil.copyfile("ubuntu_clone.box", "clone1/ubuntu_clone.box")
        shutil.copyfile("ubuntu_clone.box", "clone2/ubuntu_clone.box")
        os.remove("ubuntu_clone.box")
        os.chdir("clone1")
        subprocess.check_output(["vagrant", "init", "ubuntu_clone.box"])
        subprocess.check_output(["vagrant", "up"])
        subprocess.check_output(["vagrant", "halt"])
        os.chdir("..")
        os.chdir("clone2")
        subprocess.check_output(["vagrant", "init", "ubuntu_clone.box"])
        subprocess.check_output(["vagrant", "up"])
        subprocess.check_output(["vagrant", "halt"])
        os.chdir("..")
        return







    def stopVm(self, cloudstack):
        job = cloudstack.stopVirtualMachine({"id":self.vmid})

        status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})
        print "stopping VM ... Jobid: %s" % status['jobid']
        while status['jobstatus'] == 0:
            print ".",
            sys.stdout.flush()
            time.sleep(1)
            status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})

        print "Job %s completed, VM stopped" % status['jobid']
        return

    def startVm(self, cloudstack):
        job = cloudstack.startVirtualMachine({"id":self.vmid})

        status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})
        print "starting VM. Job id = %s" % job['jobid']

        while status['jobstatus'] == 0:
            print ".",
            sys.stdout.flush()
            time.sleep(1)
            status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})

        print "Job %s completed, VM started" % status['jobid']
        return

    def listAllVms(self, cloudstack):
        vms = cloudstack.listVirtualMachines()
        for vm in vms:
            print "id: %s  Name: %s  State: %s" % (vm['id'], vm['name'], vm['state'])

        return

    def createSnapshot(self, cloudstack, name):
        vols = cloudstack.listVolumes({"virtualmachineid":self.vmid})
        for vol in vols:
          volumeid = vol['id']
          break

        job = cloudstack.createSnapshot({"volumeid":volumeid,"name":name})

        status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})

        print "Creating Snapshot ... Jobid: %s" % status['jobid']

        while status['jobstatus'] == 0:
          print ".",
          sys.stdout.flush()
          time.sleep(1)
          status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})

        print "\n Snapshot has been created..."
        return

    def listAllSnapshots(self, cloudstack):
        vols = cloudstack.listVolumes({"virtualmachineid":self.vmid})
        for vol in vols:
          volumeid = vol['id']
          break

        snaps = cloudstack.listSnapshots({"volumeid":volumeid})
        for snap in snaps:
            print "id: %s  Name: %s  State: %s  Created on: %s" % (snap['id'], snap['name'], snap['state'], snap['created'])

        return

    def revertSnapshot(self, cloudstack, snapshotid):

        job = cloudstack.revertSnapshot({"id":snapshotid})

        status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})

        print "Reverting VM to Snapshot"

        while status['jobstatus'] == 0:
          print ".",
          sys.stdout.flush()
          time.sleep(1)
          status = cloudstack.queryAsyncJobResult({"jobid":job['jobid']})

        print "\n VM has been reverted to the snapshot"
        return

    def createInitialSnapshot(self, cloudstack):
        if self.isAll:
            vms = cloudstack.listVirtualMachines()

            for vm in vms:
                self.setVm(vm['id'])
                self.stopVm(cloudstack)
                self.createSnapshot(cloudstack, "initialSnapshot")
                self.startVm(cloudstack)

        else:
            self.stopVm(cloudstack)
            self.createSnapshot(cloudstack, "initialSnapshot")
            self.startVm(cloudstack)


