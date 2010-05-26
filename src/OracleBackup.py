import datetime
import time
import os
import re
import sys
import smtplib

class RunCommand():
        
    def __init__(self):
        # Write the log in the same directory as the script. Logname will be ScriptName.log
        self.f = open(str(sys.path[0] + "/" + re.sub('\.py(c)?','.log',os.path.basename(sys.argv[0]))),'a')
        
        self.logger("Initializing", "Started")
        
        # Get the current time and set the fileprefix.
        now = datetime.datetime.now() 
        self.timestr = now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        self.fileprefix = "ogre_full_expdp_" + self.timestr
        
        self.dpdumpdir = "/opt/oracle/admin/ogre/dpdump/"
        self.backupsdir = "/home/oracle/Backups/"
        
        # Build Data Pump Full Export command. Need to initially set environment variables.
        self.expdpcmd =  "source /home/oracle/.bash_profile; "
        self.expdpcmd += "expdp \\'/ as sysdba\\' directory=data_pump_dir dumpfile="
        self.expdpcmd += self.fileprefix
        self.expdpcmd += ".dmp logfile="
        self.expdpcmd += self.fileprefix
        self.expdpcmd += "_expdp.log full=y"
        
        # Build Move Command
        self.movecmd =  "mv " + self.dpdumpdir + self.fileprefix + "* " + self.backupsdir
        
        # Build Compress Command
        self.compresscmd =  "tar cvfj " + self.backupsdir + self.fileprefix
        self.compresscmd += ".tbz2 " + self.backupsdir + self.fileprefix
        self.compresscmd += ".dmp " + self.backupsdir + self.fileprefix + "_expdp.log"
        
        # Remove the dmp and log files as they have been compress into the tgz file.
        self.removecmd =  "rm " + self.backupsdir + self.fileprefix
        self.removecmd += ".dmp " + self.backupsdir + self.fileprefix + "_expdp.log"
        
        # Rsync command.
        self.rsynccmd = "rsync -avz --no-o --no-g --no-p --no-t " + self.backupsdir + " /mnt/panzer/`date +%Y-%m`"
        
        self.status = {}
        self.status['expdpcmd'] = -1
        self.status['movecmd'] = -1
        self.status['compresscmd'] = -1
        self.status['removecmd'] = -1
        self.status['rsynccmd'] = -1
        self.status['removeOldBackups'] = []      
        
        # Setup Email
        self.smtpserver = 'mail.opentext.com'
        self.sender = 'davidh@opentext.com'
        self.receivers = ['davidh@opentext.com']
        self.emailheader =  "From: David Hooey <davidh@opentext.com>\n"
        self.emailheader += "To: David Hooey <davidh@opentext.com>\n"
        self.emailheader += "Subject: OracleBackup: ogre\n\n"
        
        self.logger("Initializing", "Finished")
        
    def logger(self,section,action,msg=""):
        self.f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,") + section + "," + action + "," + msg + "\n")
        
    def run(self):
        # Run the commands only if the previous commands were successful.
        self.logger("Running", "Started")
        self.logger("expdpcmd", "Started", str(self.expdpcmd))
        self.status['expdpcmd'] = os.system(self.expdpcmd)
        self.logger("expdpcmd", "Finished", str(self.status['expdpcmd']))
        if self.status['expdpcmd'] == 0:
            self.logger("movecmd", "Started", str(self.movecmd))
            self.status['movecmd'] = os.system(self.movecmd)
            self.logger("movecmd", "Finished", str(self.status['movecmd']))
            if self.status['movecmd'] == 0:
                self.logger("compresscmd", "Started", str(self.compresscmd))
                self.status['compresscmd'] = os.system(self.compresscmd)
                self.logger("compresscmd", "Finished", str(self.status['compresscmd']))
                if self.status['compresscmd'] == 0:
                    self.logger("removecmd", "Started", str(self.removecmd))
                    self.status['removecmd'] = os.system(self.removecmd)
                    self.logger("removecmd", "Finished", str(self.status['removecmd']))
        self.logger("Running", "Finished", str(self.status))
            
    def rsyncFiles(self):
        # mount -t cifs //panzer.opentext.net/ogre -o username=ogre,password=Oracle12$
        # rsync -avz --no-o --no-g --no-p --no-t /home/oracle/Backups/ /mnt/panzer/`date +%Y-%m`
        self.logger("Synchronizing", "Started")
        self.logger("rsynccmd", "Started", str(self.rsynccmd))
        self.status['rsynccmd'] = os.system(self.rsynccmd)
        self.logger("rsynccmd", "Finished", str(self.status['rsynccmd']))
        self.logger("Synchronizing", "Finished", str(self.status))

    def removeOldBackups(self):
        self.logger("BackupCleanup", "Started")
        # Remove local backup files which are over 7 days old only if the synchronization job ran.
        if self.status['rsynccmd'] == 0:
            for file in os.listdir(self.backupsdir):
                filetime = os.path.getmtime(self.backupsdir + file) 
                currenttime = time.time()
                fileage = currenttime - filetime
                if fileage > 604800:
                    try:
                        os.unlink(self.backupsdir + file)
                    except:
                        self.logger("BackupCleanup", "Failed Removing", str(self.backupsdir + file))
                        self.status['removeOldBackups'].append([str(self.backupsdir + file),"Failed"])
                    else:
                        self.logger("BackupCleanup", "Success Removing", str(self.backupsdir + file))
                        self.status['removeOldBackups'].append([str(self.backupsdir + file),"Success"])
            self.logger("BackupCleanup", "Finished", str(self.status['removeOldBackups']))
        else:
            self.logger("BackupCleanup", "Finished", "No backups removed due to synchronization failure!")
            
    def sendStatusEmail(self):
        self.logger("SendingEmail", "Started")
        self.message = self.emailheader + "Oracle Data Pump Backup: " + self.timestr + "\n"
        
        self.message += "\nCommand Status:\n"
        for s in self.status:
            if s != 'removeOldBackups':
                self.message += "\t" + s + ": "
                if self.status[s] == 0:
                    self.message += "Success\n"
                elif self.status[s] == -1:
                    self.message += "NOP\n"
                else:
                    self.message += "Failed\n"
        
        self.message += "\nOld Backup Removal:\n"
        for f in self.status['removeOldBackups']:
            self.message += "\t" + f[1] + " removing backup file: " + f[0] + "\n"
        
        try:
            smtpObj = smtplib.SMTP(self.smtpserver)
            smtpObj.sendmail(self.sender, self.receivers, self.message)
        except SMTPException:
            self.logger("SendingEmail", "Finished", "Failed to send email!")
        else:
            self.logger("SendingEmail", "Finished", str(self.status))

rc = RunCommand()
rc.run()
rc.rsyncFiles()
rc.removeOldBackups()
rc.sendStatusEmail()
