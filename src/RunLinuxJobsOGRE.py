import LinuxJobs

lj = LinuxJobs.LinuxJobs()

# Manager Snapshots and Backup Linux.
remotebackupdir = "/mnt/extdrive/backups/linux/ogre.support.opentext.net"
backupstokeep = 5
lj.linuxBackup(remotebackupdir, backupstokeep)

# Send status email.
smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "LinuxBackup: ogre.support.opentext.net"
title = "Linux Jobs"
lj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
