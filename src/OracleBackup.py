import datetime
import time
import os
import sys
import smtplib

class RunCommand():
        
    def __init__(self):
        self.f = open("/home/oracle/Scripts/OracleBackup.log",'a')
        
        self.logger("Initializing", "Started")
        
        # Get the current time and set the fileprefix.
        now = datetime.datetime.now() 
        self.timestr = now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        self.fileprefix = "ogre_full_expdp_" + self.timestr
        
        self.dpdumpdir = "/opt/oracle/admin/ogre/dpdump/"
        self.backupsdir = "/home/oracle/Backups/"
        
        # Build Data Pump Full Export command
        self.expdpcmd =  "expdp \\'/ as sysdba\\' directory=data_pump_dir dumpfile="
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
        self.rsynccmd = "rsync -avz --no-o --no-g --no-p --no-t /home/oracle/Backups/ /mnt/panzer/`date +%Y-%m`"
        
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
        
    def logger(self,section,msg):
        self.f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,") + section + "," + msg)
        
    def run(self):
        self.logger("Running", "Started")
        self.status['expdpcmd'] = os.system(self.expdpcmd)
        self.status['movecmd'] = os.system(self.movecmd)
        self.status['compresscmd'] = os.system(self.compresscmd)
        self.status['removecmd'] = os.system(self.removecmd)
        self.logger("Running", "Finished")
            
    def rsyncFiles(self):
        # mount -t cifs //panzer.opentext.net/ogre -o username=ogre,password=Oracle12$
        # rsync -avz --no-o --no-g --no-p --no-t /home/oracle/Backups/ /mnt/panzer/`date +%Y-%m`
        self.logger("Synchronizing", "Started")        
        self.status['rsynccmd'] = os.system(self.rsynccmd)
        self.logger("Synchronizing", "Finished")

    def removeOldBackups(self):
        self.logger("BackupCleanup", "Started")
        # Remove local backup files which are 7 days old or older.
        for file in os.listdir(self.backupsdir):
            filetime = os.path.getmtime(self.backupsdir + file) 
            currenttime = time.time()
            fileage = currenttime - filetime
            if fileage > 604800:
                os.unlink(self.backupsdir + file)
                self.status['removeOldBackups'].append(str(self.backupsdir + file))
        self.logger("BackupCleanup", "Finished")  

    def sendStatusEmail(self):
        self.logger("SendingEmail", "Started")
        self.message = self.emailheader + "Oracle Data Pump Backup: " + self.timestr + "\n"
        
        self.message += "\nCommand Status:\n"
        for s in self.status:
            if s != 'removeOldBackups':
                self.message += "\t" + s + ": "
                if self.status[s] == 0:
                    self.message += "Success\n"
                else:
                    self.message += "Failed\n"
        
        self.message += "\nOld Backup Removal:\n"
        for f in self.status['removeOldBackups']:
            self.message += "\tRemoved backup file: " + f + "\n"
        
        try:
            smtpObj = smtplib.SMTP(self.smtpserver)
            smtpObj.sendmail(self.sender, self.receivers, self.message)
        except SMTPException:
            print("Error: unable to send email")
            
        self.logger("SendingEmail", "Finished" + str(self.status))

rc = RunCommand()
rc.run()
rc.rsyncFiles()
rc.removeOldBackups()
rc.sendStatusEmail()
