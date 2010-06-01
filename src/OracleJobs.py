import datetime
import time
import os
import re
import sys
import smtplib

class OracleJobs():
        
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

    def oracleDataPumpExport(self, dpdumpdir, localbackupdir, remotebackupdir, fileprefix):
        # Inputs
        #     1. dpdumpdir
        #     2. localbackupdir
        #     3. remotebackupdir
        #     4. fileprefix
        #
        # Process
        #     1. Run a full Data Pump Export
        #     2. Move the dump and log files to the local backup directory.
        #     3. Compress the dump and log files.
        #     4. Remove the dump and log files if they successfully compressed.
        #     5. Copy the compress file to the remotebackupdir.
        
        self.logger(self.whoami(), "Started")
        
        # Add the status keys to the dictionary.
        self.status[self.whoami() + '_expdpcmd'] = -1
        self.status[self.whoami() + '_movecmd'] = -1
        self.status[self.whoami() + '_compresscmd'] = -1
        self.status[self.whoami() + '_removecmd'] = -1
        self.status[self.whoami() + '_cpcmd'] = -1
        self.status[self.whoami() + '_removeOldBackups'] = []
        
        #dpdumpdir = "/opt/oracle/admin/orcl/dpdump/"
        #backupsdir = "/home/oracle/Backups/"
        fileprefix = fileprefix + self.timestr
        
        # Build Data Pump Full Export command. Need to initially set environment variables.
        expdpcmd =  "source /home/oracle/.bash_profile; "
        expdpcmd += "expdp \\'/ as sysdba\\' directory=data_pump_dir dumpfile="
        expdpcmd += fileprefix
        expdpcmd += ".dmp logfile="
        expdpcmd += fileprefix
        expdpcmd += "_expdp.log full=y"

        # Build Move Command
        movecmd =  "mv " + dpdumpdir + fileprefix + "* " + localbackupdir
        
        # Build Compress Command
        compresscmd =  "tar cvfj " + localbackupdir + fileprefix
        compresscmd += ".tbz2 " + localbackupdir + fileprefix
        compresscmd += ".dmp " + localbackupdir + fileprefix + "_expdp.log"
        
        # Remove the dmp and log files as they have been compress into the tgz file.
        removecmd =  "rm " + localbackupdir + fileprefix
        removecmd += ".dmp " + localbackupdir + fileprefix + "_expdp.log"
                
        # Run the commands only if the previous commands were successful.
        self.logger(self.whoami() + "_expdpcmd", "Started", str(expdpcmd))
        self.status[self.whoami() + '_expdpcmd'] = os.system(expdpcmd)
        self.logger(self.whoami() + "_expdpcmd", "Finished", str(self.status[self.whoami() + '_expdpcmd']))
        if self.status[self.whoami() + '_expdpcmd'] == 0:
            self.logger(self.whoami() + "_movecmd", "Started", str(movecmd))
            self.status[self.whoami() + '_movecmd'] = os.system(movecmd)
            self.logger(self.whoami() + "_movecmd", "Finished", str(self.status[self.whoami() + '_movecmd']))
            if self.status[self.whoami() + '_movecmd'] == 0:
                self.logger(self.whoami() + "_compresscmd", "Started", str(compresscmd))
                self.status[self.whoami() + '_compresscmd'] = os.system(compresscmd)
                self.logger(self.whoami() + "_compresscmd", "Finished", str(self.status[self.whoami() + '_compresscmd']))
                if self.status[self.whoami() + '_compresscmd'] == 0:
                    self.logger(self.whoami() + "_removecmd", "Started", str(removecmd))
                    self.status[self.whoami() + '_removecmd'] = os.system(removecmd)
                    self.logger(self.whoami() + "_removecmd", "Finished", str(self.status[self.whoami() + '_removecmd']))
                    
        # Synchronize the backup remotely.
        # mount -t cifs //panzer.opentext.net/Backups /mnt/panzer -o username=backups,password=Pa\$\$w0rd
        # rsync -avz --no-o --no-g --no-p --no-t /home/oracle/Backups/ /mnt/panzer/`date +%Y-%m`

        # Rsync command.
        #rsyncexpdp = "rsync -avz --no-o --no-g --no-p --no-t " + backupsdir + " /mnt/panzer/Oracle/ovmm.support.opentext.net/orcl/DataPumpBackups/`date +%Y-%m`"
        cpcmd = "cp " + localbackupdir + fileprefix + "* " + remotebackupdir + "`date +%Y-%m`"                
        
        self.logger(self.whoami() + "_cpcmd", "Started", str(cpcmd))
        self.status[self.whoami() + '_cpcmd'] = os.system(cpcmd)
        self.logger(self.whoami() + "_cpcmd", "Finished", str(self.status[self.whoami() + '_cpcmd']))

        # Remove local backup files which are over 7 days old only if the synchronization job ran.
        self.logger(self.whoami() + "_removeOldBackups", "Started")
        if self.status[self.whoami() + '_cpcmd'] == 0:
            for file in os.listdir(localbackupdir):
                filetime = os.path.getmtime(localbackupdir + file) 
                currenttime = time.time()
                fileage = currenttime - filetime
                if fileage > 604800:
                    try:
                        os.unlink(localbackupdir + file)
                    except:
                        self.logger(self.whoami() + "_removeOldBackups", "Failed Removing", str(localbackupdir + file))
                        self.status[self.whoami() + '_removeOldBackups'].append([str(localbackupdir + file),"Failed"])
                    else:
                        self.logger(self.whoami() + "_removeOldBackups", "Success Removing", str(localbackupdir + file))
                        self.status[self.whoami() + '_removeOldBackups'].append([str(localbackupdir + file),"Success"])
            self.logger(self.whoami() + "_removeOldBackups", "Finished", str(self.status[self.whoami() + '_removeOldBackups']))
        else:
            self.logger(self.whoami() + "_removeOldBackups", "Finished", "No backups removed due to synchronization failure!")

        self.logger(self.whoami(), "Finished", str(self.status))                    
        
    def oracleHotBackup(self, flashrecoverydir, remotebackupdir):
        # Inputs
        #     1. flashrecoverydir
        #     2. remotebackupdir
        #
        # Process
        #     Run the commands in the local WholeDatabaseBackup.rman file.
        #     Afterwards the flash_recovery_area directory will rsync'ed with a remote backup directory. 
                
        self.logger(self.whoami(), "Started")
        
        self.status[self.whoami() + '_rmancmd'] = -1
        self.status[self.whoami() + '_rsyncrman'] = -1        
                
        rmancmd =  "source /home/oracle/.bash_profile; "
        rmancmd += "rman target=/ cmdfile="
        rmancmd += self.scriptdir + "WholeDatabaseBackup.rman log="
        rmancmd += self.scriptdir + "WholeDatabaseBackup.log append"
        
        # Hot Oracle Backup
        self.logger(self.whoami() + "_rmancmd", "Started", str(rmancmd))
        self.status[self.whoami() + '_rmancmd'] = os.system(rmancmd)
        self.logger(self.whoami() + "_rmancmd", "Finished", str(self.status[self.whoami() + '_rmancmd']))        
        
        # Rsync flash_recovery_area.
        #rsync -av --delete /opt/oracle/flash_recovery_area/ORCL/ mnt/panzer/Oracle/ovmm.support.opentext.net/orcl/HotBackups
        rsyncrman = "rsync -avz --no-o --no-g --no-p --no-t --delete " + flashrecoverydir + " " + remotebackupdir 
        
        self.logger(self.whoami() + "_rsyncrman", "Started", str(rsyncrman))
        self.status[self.whoami() + '_rsyncrman'] = os.system(rsyncrman)
        self.logger(self.whoami() + "_rsyncrman", "Finished", str(self.status[self.whoami() + '_rsyncrman']))                
        
        self.logger("oracleHotBackup", "Finished", str(self.status))         
            
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
        
        pattern = re.compile('.+removeOldBackups')
        
        for s in sorted(self.status):
            if not pattern.match(s):
                message += "\t" + s + ": "
                if self.status[s] == 0:
                    message += "Success\n"
                elif self.status[s] == -1:
                    message += "NOP\n"
                else:
                    message += "Failed\n"
        
        message += "\nOld Backup Removal:\n"
        for s in self.status:
            if pattern.match(s):
                for f in self.status[s]:
                    message += "\t" + f[1] + " removing backup file: " + f[0] + "\n"
        
        try:
            smtpObj = smtplib.SMTP(smtpserver)
            smtpObj.sendmail(sender, receivers, message)
        except SMTPException:
            self.logger(self.whoami(), "Finished", "Failed to send email!")
        else:
            self.logger(self.whoami(), "Finished", str(self.status))
