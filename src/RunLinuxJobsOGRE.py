import LinuxJobs

lj = LinuxJobs.LinuxJobs()

remotebackupdir = "/mnt/extdrive/backups/linux/ogre.support.opentext.net"
backupstokeep = 5

lj.linuxBackup(remotebackupdir, backupstokeep)

smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "LinuxBackup: ogre.support.opentext.net"
title = "Linux Backup"

lj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
