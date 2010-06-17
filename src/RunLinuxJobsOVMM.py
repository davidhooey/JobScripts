import LinuxJobs

lj = LinuxJobs.LinuxJobs()

# Manager Snapshots and Backup Linux.
remotebackupdir = "/mnt/extdrive/backups/linux/ovmm.support.opentext.net"
backupstokeep = 5
lj.linuxBackup(remotebackupdir, backupstokeep)

# Manager Snapshots for Windows Backup.
remotebackupdir = "/mnt/extdrive/backups/windows/davidh-e6500.opentext.net"
backupstokeep = 5
lj.snapshotManager(remotebackupdir, backupstokeep)

# Send status email.
smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "LinuxBackup: ovmm.support.opentext.net"
title = "Linux Jobs"
lj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
