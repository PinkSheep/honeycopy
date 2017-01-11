import sys
import time
import shutil
import os
import errno
import subprocess
import schedule
from datetime import datetime

class HoneyCopy(object):
    def __init__(self):
        self.vboxpath = os.environ["HOME"]+"/VirtualBox VMs/"
        self.honeypath = os.getcwd() + "/"
        self.comparepath = os.getcwd() + "compare/"
        self.archivepath = os.getcwd() + "archive/"
        print "Env Variables are: %s , %s" % (self.vboxpath, self.honeypath)
        return


    def createHoneypot(self):
        if not os.path.exists("vm"):
            os.makedirs("vm")

        if not os.path.exists("compare"):
            os.makedirs("compare")

        if not os.path.exists("archive"):
            os.makedirs("archive")

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







    def start(self):
        os.chdir("vm")
        subprocess.check_output(["vagrant", "up"])
        os.chdir("clone1")
        subprocess.check_output(["vagrant", "up"])
        os.chdir("../clone2")
        subprocess.check_output(["vagrant", "up"])
        os.chdir("..")
        print "VMs up, start recording"
        print "abort by pressing CTRL+C"
        schedule.every(5).minutes.do(self.compare)
        while 1:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                print "Manually aborted recording, VMs still running"
                sys.exit()
        
        return

    def compare(self):
        print "start comparing"
        #self.createSnapshot()
        self.suspend()
        if not os.path.exists(self.honeypath + "fs"):
            os.makedirs(self.honeypath + "fs")

        if not os.path.exists(self.honeypath + "fs/honeypot"):
            os.makedirs(self.honeypath + "fs/honeypot")

        if not os.path.exists(self.honeypath + "fs/copy1"):
            os.makedirs(self.honeypath + "fs/copy1")

        if not os.path.exists(self.honeypath + "fs/copy2"):
            os.makedirs(self.honeypath + "fs/copy2")

        if not os.path.exists(self.honeypath + "fs/diff"):
            os.makedirs(self.honeypath + "fs/diff")

        for subdir, dirs, files in os.walk(self.vboxpath):
            for dir in dirs:
                if dir.startswith("vm_"):
                    path1 = self.vboxpath + dir + "/"
                    snapid = self.getSaveId(path1 + "Snapshots/")
                    if os.path.exists(self.honeypath + "fs/honeypot.vmdk"):
                        os.remove(self.honeypath + "fs/honeypot.vmdk")

                    time.sleep(5)
                    print snapid, path1

                    if snapid == "empty":
                        shutil.copyfile(path1 +"box-disk1.vmdk", self.honeypath + "fs/honeypot.vmdk")
                    else:
                        os.chdir(path1 + "Snapshots/")
                        subprocess.check_output(["VBoxManage", "clonehd", snapid, self.honeypath+"fs/honeypot.vmdk"])
                        os.chdir(self.honeypath)


                if dir.startswith("clone1_"):
                    path2 = self.vboxpath + dir + "/"
                    snapid = self.getSaveId(path2 + "Snapshots/")
                    if os.path.exists(self.honeypath + "fs/copy1.vmdk"):
                        os.remove(self.honeypath + "fs/copy1.vmdk")

                    time.sleep(5)

                    print snapid, path2

                    if snapid == "empty":
                        shutil.copyfile(path2 +"box-disk1.vmdk", self.honeypath + "fs/copy1.vmdk")
                    else:
                        os.chdir(path2 + "Snapshots/")
                        subprocess.check_output(["VBoxManage", "clonehd", snapid, self.honeypath+"fs/copy1.vmdk"])
                        os.chdir(self.honeypath)

                if dir.startswith("clone2_"):
                    path3 = self.vboxpath + dir + "/"
                    snapid = self.getSaveId(path3 + "Snapshots/")
                    if os.path.exists(self.honeypath + "fs/copy2.vmdk"):
                        os.remove(self.honeypath + "fs/copy2.vmdk")

                    time.sleep(5)

                    print snapid, path3


                    if snapid == "empty":
                        shutil.copyfile(path3 +"box-disk1.vmdk", self.honeypath + "fs/copy2.vmdk")
                    else:
                        os.chdir(path3 + "Snapshots/")
                        subprocess.check_output(["VBoxManage", "clonehd", snapid, self.honeypath+"fs/copy2.vmdk"])
                        os.chdir(self.honeypath)

        self.resume()
        self.diffFs()
        self.diffNw()
        print "compare complete"
        return

    def getSaveId(self, path):
        f = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            f.extend(filenames)
            break

        f.sort(key=lambda x: os.stat(os.path.join(path, x)).st_mtime)
        f.reverse()
        for file in f:
            filename, file_extension = os.path.splitext(file)
            if file_extension == ".vmdk":
                return file[1:-6]

        return "empty"
                

    def suspend(self):
        os.chdir(self.honeypath + "vm")
        subprocess.check_output(["vagrant", "suspend"])
        os.chdir(self.honeypath + "vm/clone1")
        subprocess.check_output(["vagrant", "suspend"])
        os.chdir(self.honeypath + "vm/clone2")
        subprocess.check_output(["vagrant", "suspend"])
        os.chdir(self.honeypath)
        return

    def resume(self):
        os.chdir(self.honeypath + "vm")
        subprocess.check_output(["vagrant", "resume"])
        os.chdir(self.honeypath + "vm/clone1")
        subprocess.check_output(["vagrant", "resume"])
        os.chdir(self.honeypath + "vm/clone2")
        subprocess.check_output(["vagrant", "resume"])
        os.chdir(self.honeypath)
        return


    def createSnapshot(self):
        snaptime = datetime.now()
        os.chdir(self.honeypath + "vm")
        subprocess.check_output(["vagrant", "snapshot", "save", str(snaptime.year) + str(snaptime.month) + str(snaptime.day) + "_" + str(snaptime.hour) + str(snaptime.minute) ])
        os.chdir("clone1")
        subprocess.check_output(["vagrant", "snapshot", "save", str(snaptime.year) + str(snaptime.month) + str(snaptime.day) + "_" + str(snaptime.hour) + str(snaptime.minute) ])
        os.chdir("../clone2")
        subprocess.check_output(["vagrant", "snapshot", "save", str(snaptime.year) + str(snaptime.month) + str(snaptime.day) + "_" + str(snaptime.hour) + str(snaptime.minute) ])
        os.chdir(self.honeypath)
        print "snapshots created"
        return

    def diffFs(self):
        os.chdir(self.honeypath + "fs")
        subprocess.check_output(["vmware-mount", "honeypot.vmdk", "honeypot"])
        subprocess.check_output(["vmware-mount", "copy1.vmdk", "copy1"])
        subprocess.check_output(["vmware-mount", "copy2.vmdk", "copy2"])
        print "filesystems mounted"

        try:
            shutil.move("diff/diff1.2","diff/diff1.1")
            shutil.move("diff/diff2.2","diff/diff2.1")
        except IOError as e:
            print "moving files aborted, not enough files present"

        try:
            shutil.move("diff/diff1.3","diff/diff1.2")
            shutil.move("diff/diff2.3","diff/diff2.2")
        except IOError as e:
            print "moving files aborted, not enough files present"

        try:
            subprocess.check_output("rsync -rvl --size-only --dry-run honeypot/ copy1 > diff/diff1.3 2>/dev/null", shell=True)
        except subprocess.CalledProcessError as e:
            print "ignoring exitcode from rsync"

        try:
            subprocess.check_output("rsync -rvl --size-only --dry-run honeypot/ copy2 > diff/diff2.3 2>/dev/null", shell=True)
        except subprocess.CalledProcessError as e:
            print "ignoring exitcode from rsync"


        try:
            list1 = self.fileToList("diff/diff1.1")
            list2 = self.fileToList("diff/diff1.2")
            list3 = self.fileToList("diff/diff1.3")
            list4 = self.fileToList("diff/diff2.1")
            list5 = self.fileToList("diff/diff2.2")
            list6 = self.fileToList("diff/diff2.3")
            for line in list2:
                if line in list1:
                    continue
                else:
                    if line in list3:
                        if line in list5:
                            with open('notify.log', 'a+') as notify:
                                notify.write(line)
            print "comparison done"
        except IOError as e:
            print "not enough files present for comparison"
        
    
        time.sleep(5)
        subprocess.check_output(["vmware-mount", "-x"])
        return

    def diffNw(self):
        return

    def fileToList(self,filename):
        with open(filename) as f:
            content = f.readlines()

        return content

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


