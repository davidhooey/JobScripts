import LinuxJobs

lj = LinuxJobs.LinuxJobs()

remotebackupdir = "/mnt/panzer/Linux/ovmm.support.opentext.net"

lj.linuxBackup(remotebackupdir)

smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "LinuxBackup: ovmm.support.opentext.net"
title = "Linux Backup"

lj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
