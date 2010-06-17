import datetime
import time
import os
import re
import sys
import smtplib
import subprocess

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
        self.status = []
              
        self.logger("Initializing", "Finished")
        
    def logger(self,section,action,msg=""):
        self.f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,") + section + "," + action + "," + msg + "\n")
        # Add self.whoami to the log string to avoid repetition.
        
    def whoami(self):
        return sys._getframe(1).f_code.co_name    

    def runcmd(self, cmd):
        try:
            retcode = subprocess.call(cmd, shell=True)
            return retcode
            #if retcode < 0:
            #    return "Terminated by signal " + str(retcode)
            #elif retcode > 0:
            #    return "Failed with return code " + str(retcode)
            #else:
            #    return retcode
        except OSError as e:
            return "Failed: " + str(e)                    

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
        self.status.append(self.whoami() + ": Started")
                
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
        status = self.runcmd(expdpcmd)
        self.logger(self.whoami() + "_expdpcmd", "Finished", str(status))
        self.status.append([self.whoami() + "_expdpcmd", status])
        if status == 0:
            self.logger(self.whoami() + "_movecmd", "Started", str(movecmd))
            status = self.runcmd(movecmd)
            self.logger(self.whoami() + "_movecmd", "Finished", str(status))
            self.status.append([self.whoami() + "_movecmd", status])
            if status == 0:
                self.logger(self.whoami() + "_compresscmd", "Started", str(compresscmd))
                status = self.runcmd(compresscmd)
                self.logger(self.whoami() + "_compresscmd", "Finished", str(status))
                self.status.append([self.whoami() + "_compresscmd", status])
                if status == 0:
                    self.logger(self.whoami() + "_removecmd", "Started", str(removecmd))
                    status = self.runcmd(removecmd)
                    self.logger(self.whoami() + "_removecmd", "Finished", str(status))
                    self.status.append([self.whoami() + "_removecmd", status])
                    
        # Synchronize the backup remotely.
        # mount -t cifs //panzer.opentext.net/Backups /mnt/panzer -o username=backups,password=Pa\$\$w0rd
        # rsync -avz --no-o --no-g --no-p --no-t /home/oracle/Backups/ /mnt/panzer/`date +%Y-%m`

        # Rsync command.
        #rsyncexpdp = "rsync -avz --no-o --no-g --no-p --no-t " + backupsdir + " /mnt/panzer/Oracle/ovmm.support.opentext.net/orcl/DataPumpBackups/`date +%Y-%m`"
        cpcmd = "cp " + localbackupdir + fileprefix + "* " + remotebackupdir + "`date +%Y-%m`"                
        
        self.logger(self.whoami() + "_cpcmd", "Started", str(cpcmd))
        status = self.runcmd(cpcmd)
        self.logger(self.whoami() + "_cpcmd", "Finished", str(status))
        self.status.append([self.whoami() + "_cpcmd", status])

        # Remove local backup files which are over 7 days old only if the synchronization job ran.
        self.logger(self.whoami() + "_removeOldBackups", "Started")
        removeList = []
        if status == 0:
            for file in os.listdir(localbackupdir):
                filetime = os.path.getmtime(localbackupdir + file) 
                currenttime = time.time()
                fileage = currenttime - filetime
                if fileage > 604800:
                    try:
                        os.unlink(localbackupdir + file)
                    except:
                        self.logger(self.whoami() + "_removeOldBackups", "Failed Removing", str(localbackupdir + file))
                        removeList.append([str(localbackupdir + file),"Failed"])
                    else:
                        self.logger(self.whoami() + "_removeOldBackups", "Success Removing", str(localbackupdir + file))
                        removeList.append([str(localbackupdir + file),"Success"])
            self.logger(self.whoami() + "_removeOldBackups", "Finished")
            self.status.append([self.whoami() + "_removeOldBackups", removeList])
        else:
            self.logger(self.whoami() + "_removeOldBackups", "Finished", "No backups removed due to synchronization failure!")

        self.logger(self.whoami(), "Finished")
        self.status.append(self.whoami() + ": Finished")               
        
    def oracleHotBackup(self, flashrecoverydir, remotebackupdir):
        # Inputs
        #     1. flashrecoverydir
        #     2. remotebackupdir
        #
        # Process
        #     Run the commands in the local WholeDatabaseBackup.rman file.
        #     Afterwards the flash_recovery_area directory will rsync'ed with a remote backup directory. 
                
        self.logger(self.whoami(), "Started")
        self.status.append(self.whoami() + ": Started")
                        
        rmancmd =  "source /home/oracle/.bash_profile; "
        rmancmd += "rman target=/ cmdfile="
        rmancmd += self.scriptdir + "WholeDatabaseBackup.rman log="
        rmancmd += self.scriptdir + "WholeDatabaseBackup.log append"
        
        # Hot Oracle Backup
        self.logger(self.whoami() + "_rmancmd", "Started", str(rmancmd))
        status = self.runcmd(rmancmd)
        self.logger(self.whoami() + "_rmancmd", "Finished", str(status))
        self.status.append([self.whoami() + "_rmancmd", status])        
        
        # Rsync flash_recovery_area.
        #rsyncrman = "rsync -avz --delete /opt/oracle/flash_recovery_area/ORCL/ mnt/panzer/Oracle/ovmm.support.opentext.net/orcl/HotBackups"
        logfile = self.scriptdir + "rsync_" + self.timestr + ".log"
        rsyncrman = "rsync -av --delete " + flashrecoverydir + " " + remotebackupdir + "  >> " + logfile 
        
        self.logger(self.whoami() + "_rsyncrman", "Started", str(rsyncrman))
        status = self.runcmd(rsyncrman)
        self.logger(self.whoami() + "_rsyncrman", "Finished", str(status))
        self.status.append([self.whoami() + "_rsyncrman", status])                
        
        self.logger("oracleHotBackup", "Finished")
        self.status.append(self.whoami() + ": Finished")    
            
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
        
        message = emailheader + title + ": " + self.timestr + "\n\n"
        
        pattern = re.compile('.+removeOldBackups')
                
        for s in self.status:
            if s.__class__ == [].__class__:
                if pattern.match(s[0]):
                    if len(s[1]) == 0:
                        message += s[0] + ": No files removed.\n"
                    else:
                        for f in s[1]:
                            message += s[0] + ": " + f[1] + " removing " + f[0] + "\n"
                else:
                    if s[1] == 0:
                        message += s[0] + ": Success\n"
                    elif s[1] == -1:
                        message += s[0] + ": NOP\n"
                    else:
                        message += s[0] + ": Failed\n"
            else:
                message += s + "\n"
        
        try:
            smtpObj = smtplib.SMTP(smtpserver)
            smtpObj.sendmail(sender, receivers, message)
        except SMTPException:
            self.logger(self.whoami(), "Finished", "Failed to send email!")
        else:
            self.logger(self.whoami(), "Finished")
