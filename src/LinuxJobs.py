import datetime
import time
import os
import re
import sys
import smtplib

class LinuxJobs():
        
    def __init__(self):
        # Write the log in the same directory as the script. Logname will be ScriptName.log
        self.scriptdir = sys.path[0] + "/"
        self.f = open(str(self.scriptdir + re.sub('\.py(c)?','.log',os.path.basename(sys.argv[0]))),'a')
        
        self.logger("Initializing", "Started")        
        
        # Get the current time and set the fileprefix.
        self.now = datetime.datetime.now() 
        self.timestr = self.now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
                                        
        # Create a status dictionary.
        self.status = {}
              
        self.logger("Initializing", "Finished")
        
    def logger(self,section,action,msg=""):
        self.f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,") + section + "," + action + "," + msg + "\n")
        # Add self.whoami to the log string to avoid repetition.
        
    def whoami(self):
        return sys._getframe(1).f_code.co_name    

    def linuxBackup(self, remotebackupdir):
        self.logger(self.whoami(), "Started")

        # How to perform snapshots using hard links. Hard links are not support through CIFS mounts to Windows.
        # 1. rm -rf /mnt/panzer/Linux/ovmm.support.opentext.net/backup.3
        # 2. mv /mnt/panzer/Linux/ovmm.support.opentext.net/backup.2 /mnt/panzer/Linux/ovmm.support.opentext.net/backup.3
        # 3. mv /mnt/panzer/Linux/ovmm.support.opentext.net/backup.1 /mnt/panzer/Linux/ovmm.support.opentext.net/backup.2
        # 4. Then:
        #    cp -al /mnt/panzer/Linux/ovmm.support.opentext.net/backup.0 /mnt/panzer/Linux/ovmm.support.opentext.net/backup.1
        #    rsync -av --delete --exclude=/mnt /  /mnt/panzer/Linux/ovmm.support.opentext.net/backup.0
        #    Or This:
        #    rsync -av --no-o --no-g --no-p --no-t --delete --exclude=/mnt --link-dest=/mnt/panzer/Linux/ovmm.support.opentext.net/backup.1 /  /mnt/panzer/Linux/ovmm.support.opentext.net/backup.0/
        
        logfile = self.scriptdir + "rsync_" + self.timestr + ".log"
        
        rsynccmd = "rsync -av --delete --exclude=/mnt /  " + remotebackupdir + " >> " + logfile 
        
        self.logger(self.whoami() + "_rsync", "Started")
        self.status[self.whoami() + '_rsync'] = os.system(rsynccmd)
        self.logger(self.whoami() + "_rsync", "Finished", str(self.status))
        
        self.logger(self.whoami(), "Finished", str(self.status))
            
    def sendStatusEmail(self, smtpserver, sender, receivers, subject, title):
        # Inputs
        #     1. smtpserver
        #     2. sender
        #     3. receivers
        #     4. subject
        #     5. title
        #
        # Process
        #     Send an email with the status of the jobs.
        
        self.logger(self.whoami(), "Started")

        # Setup Email
        emailheader =  "From: " + sender + "<" + sender + ">\n"
        emailheader += "To: " + sender + "<" + sender + ">\n"
        emailheader += "Subject: " + subject + "\n\n"        
        
        message = emailheader + title + ": " + self.timestr + "\n"
        
        message += "\nResults:\n"
        
        for s in self.status:
            message += "\t" + s + ": "
            if self.status[s] == 0:
                message += "Success\n"
            elif self.status[s] == -1:
                message += "NOP\n"
            else:
                message += "Failed\n"
                
        try:
            smtpObj = smtplib.SMTP(smtpserver)
            smtpObj.sendmail(sender, receivers, message)
        except SMTPException:
            self.logger(self.whoami(), "Finished", "Failed to send email!")
        else:
            self.logger(self.whoami(), "Finished", str(self.status))
