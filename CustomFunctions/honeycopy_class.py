import sys
import time
import shutil
import os
import errno
import subprocess
import schedule
import pyshark
from datetime import datetime


class HoneyCopy(object):
    def __init__(self):
        self.vboxpath = os.environ["HOME"]+"/VirtualBox VMs/"
        self.honeypath = os.getcwd() + "/"
        self.archivepath = os.getcwd() + "/nw/archive/"
        print "Env Variables are: %s , %s" % (self.vboxpath, self.honeypath)
        return


    def createHoneypot(self, osstr):
        if not os.path.exists("vm"):
            os.makedirs("vm")

        if not os.path.exists("nw/archive"):
            os.makedirs("nw/archive")

        shutil.copyfile(osstr+".box", "vm/"+osstr+".box")
        os.chdir("vm")
        subprocess.check_output(["vagrant", "box", "add", osstr, osstr+".box"], stderr=subprocess.STDOUT)
        subprocess.check_output(["vagrant", "init", osstr], stderr=subprocess.STDOUT)
        subprocess.check_output(["vagrant", "up"])
        subprocess.check_output(["vagrant", "halt"])
        shutil.copyfile("../Vagrantfile_"+osstr, "Vagrantfile")
        return

    def clone(self):
        os.chdir("vm")

        if not os.path.exists("clone1"):
            os.makedirs("clone1")

        if not os.path.exists("clone2"):
            os.makedirs("clone2")

        if os.path.exists("windows.box"):
            osstr = "windows"
            subprocess.check_output(["vagrant", "package", "--output", "clone1/"+osstr +"_clone1.box", "--vagrantfile", self.honeypath+"Vagrantfile_"+osstr+"_clone1"])
            time.sleep(5)
            subprocess.check_output(["vagrant", "package", "--output", "clone2/"+osstr +"_clone2.box", "--vagrantfile", self.honeypath+"Vagrantfile_"+osstr+"_clone2"])
            os.chdir("clone1")
            subprocess.check_output(["vagrant", "init", osstr+"_clone1.box"])
            subprocess.check_output(["vagrant", "up"])
            subprocess.check_output(["vagrant", "halt"])
            os.chdir("..")
            os.chdir("clone2")
            subprocess.check_output(["vagrant", "init", osstr+"_clone2.box"])
            subprocess.check_output(["vagrant", "up"])
            subprocess.check_output(["vagrant", "halt"])
            os.chdir("..")       
        else:
            osstr = "ubuntu"
            subprocess.check_output(["vagrant", "package", "--output", osstr +"_clone.box", "--vagrantfile", self.honeypath+"Vagrantfile_"+osstr+"_clone"])
            shutil.copyfile(osstr+"_clone.box", "clone1/"+osstr+"_clone.box")
            shutil.copyfile(osstr+"_clone.box", "clone2/"+osstr+"_clone.box")
            os.chdir("clone1")
            subprocess.check_output(["vagrant", "init", osstr+"_clone.box"])
            subprocess.check_output(["vagrant", "up"])
            subprocess.check_output(["vagrant", "halt"])
            os.chdir("..")
            os.chdir("clone2")
            subprocess.check_output(["vagrant", "init", osstr+"_clone.box"])
            subprocess.check_output(["vagrant", "up"])
            subprocess.check_output(["vagrant", "halt"])
            os.chdir("..")

        if not os.path.exists(self.honeypath + "nw"):
            os.makedirs(self.honeypath + "nw")

        time.sleep(5)

        for subdir, dirs, files in os.walk(self.vboxpath):
            for dir in dirs:
                if dir.startswith("vm_"):
                    subprocess.check_output(["VBoxManage", "modifyvm", dir ,"--nictrace2", "on" , "--nictracefile2", self.honeypath + "nw/honeypot.pcap"])
                if dir.startswith("clone1_"):
                    subprocess.check_output(["VBoxManage", "modifyvm", dir ,"--nictrace1", "on" , "--nictracefile1", self.honeypath + "nw/clone1.pcap"]) 
                if dir.startswith("clone2_"):
                    subprocess.check_output(["VBoxManage", "modifyvm", dir ,"--nictrace1", "on" , "--nictracefile1", self.honeypath + "nw/clone2.pcap"])  
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
        schedule.every(60).minutes.do(self.compare)
        self.compare()
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
        self.createSnapshot()
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

        shutil.move(self.honeypath + "nw/honeypot.pcap", self.archivepath + "honeypot.pcap")
        shutil.move(self.honeypath + "nw/clone1.pcap", self.archivepath + "clone1.pcap")
        shutil.move(self.honeypath + "nw/clone2.pcap", self.archivepath + "clone2.pcap")

        for subdir, dirs, files in os.walk(self.vboxpath):
            for dir in dirs:
                if dir.startswith("vm_"):

                    subprocess.check_output(["VBoxManage", "modifyvm", dir ,"--nictrace2", "on" , "--nictracefile2", self.honeypath + "nw/honeypot.pcap"])

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
                    subprocess.check_output(["VBoxManage", "modifyvm", dir ,"--nictrace1", "on" , "--nictracefile1", self.honeypath + "nw/clone1.pcap"]) 

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

                    subprocess.check_output(["VBoxManage", "modifyvm", dir ,"--nictrace1", "on" , "--nictracefile1", self.honeypath + "nw/clone2.pcap"])  

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
        if os.path.exists(self.honeypath+"vm/windows.box"):
            subprocess.check_output(["vmware-mount", "honeypot.vmdk", "2", "honeypot"])
            subprocess.check_output(["vmware-mount", "copy1.vmdk", "2", "copy1"])
            subprocess.check_output(["vmware-mount", "copy2.vmdk", "2", "copy2"])
        else:
            subprocess.check_output(["vmware-mount", "honeypot.vmdk", "honeypot"])
            subprocess.check_output(["vmware-mount", "copy1.vmdk", "copy1"])
            subprocess.check_output(["vmware-mount", "copy2.vmdk", "copy2"])            
        print "filesystems mounted"

        snaptime = datetime.now()

        try:
            shutil.move("diff/diff1.1","diff/diff1_" + str(snaptime.year) + str(snaptime.month) + str(snaptime.day) + "_" + str(snaptime.hour) + str(snaptime.minute))
            shutil.move("diff/diff2.1","diff/diff2_" + str(snaptime.year) + str(snaptime.month) + str(snaptime.day) + "_" + str(snaptime.hour) + str(snaptime.minute))
        except IOError as e:
            pass
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
            subprocess.check_output("rsync -rvl --size-only --dry-run --devices honeypot/ copy1 > diff/diff1.3 2>/dev/null", shell=True)
        except subprocess.CalledProcessError as e:
            print "ignoring exitcode from rsync"

        try:
            subprocess.check_output("rsync -rvl --size-only --dry-run --devices honeypot/ copy2 > diff/diff2.3 2>/dev/null", shell=True)
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
                        with open('notify.log', 'a+') as notify:
                            notify.write(line)

            for line in list5:
                if line in list4:
                    continue
                else:
                    if line in list6:
                        with open('notify.log', 'a+') as notify:
                            notify.write(line)
            print "FS-Compare done"
        except IOError as e:
            print "not enough files present for comparison"
        
    
        time.sleep(5)
        try:
            subprocess.check_output(["vmware-mount", "-x"])
        except subprocess.CalledProcessError as e:
            subprocess.check_output(["vmware-   mount", "-x"])
            print "ignoring vmware-mount error"
            
        return

    def diffNw(self):

        cap1 = self.pcapToList(self.archivepath + "honeypot.pcap")
        cap2 = self.pcapToList(self.archivepath + "clone1.pcap")
        cap3 = self.pcapToList(self.archivepath + "clone2.pcap")
        print "pcap-files read"
        duplicated = []
        for pkg1 in cap1:
            time1 = float(pkg1.sniff_timestamp)
            param = float(cap1[-1].sniff_timestamp) - 60 * 60 * 2 
            less = float(time1) - 60 * 60
            more = float(time1) + 60 * 60
            if pkg1.ip.dst in duplicated:
                continue
            else:
                duplicated.append(pkg1.ip.dst)
                if time1 > param:
                    counter = 0
                    for pkg2 in cap2:
                        time2 = float(pkg2.sniff_timestamp)
                        if pkg1.ip.dst == pkg2.ip.dst and  less > time2 and more <= time2:
                            counter += 1
                            break

                    for pkg3 in cap3:
                        time3 = float(pkg3.sniff_timestamp)
                        if pkg1.ip.dst == pkg3.ip.dst and less > time3 and more <= time3:
                            counter += 1
                            break

                    if counter < 1:
                        with open(self.honeypath + 'fs/notify.log', 'a+') as notify:
                            notify.write(pkg1.ip.dst + "\n")

        time.sleep(2)

        nowtime = datetime.now()
        shutil.move(self.archivepath + "honeypot.pcap", self.archivepath + "honeypot.pcap_" + str(nowtime.year) + str(nowtime.month) + str(nowtime.day) + str(nowtime.hour) + str(nowtime.minute))
        shutil.move(self.archivepath + "clone1.pcap", self.archivepath + "clone1.pcap_" + str(nowtime.year) + str(nowtime.month) + str(nowtime.day) + str(nowtime.hour) + str(nowtime.minute))
        shutil.move(self.archivepath + "clone2.pcap", self.archivepath + "clone2.pcap_" + str(nowtime.year) + str(nowtime.month) + str(nowtime.day) + str(nowtime.hour) + str(nowtime.minute))

        print "Network-Compare done"
        return

    def fileToList(self,filename):
        with open(filename) as f:
            content = f.readlines()

        return content

    def pcapToList(self,filepath):
        cap = pyshark.FileCapture(filepath, display_filter="tcp and tcp.seq < 2")
        li = []
        for pkg in cap:
            li.append(pkg)

        return li