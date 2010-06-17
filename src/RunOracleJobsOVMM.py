import OracleJobs

oj = OracleJobs.OracleJobs()

# Data Pump Export.
dpdumpdir = "/opt/oracle/admin/orcl/dpdump/"
localbackupdir = "/home/oracle/Backups/"
remotebackupdir = "/mnt/extdrive/backups/oracle/ovmm.support.opentext.net/orcl/datapumpbackups/"
fileprefix = "ovmm_orcl_full_expdp_"
oj.oracleDataPumpExport(dpdumpdir, localbackupdir, remotebackupdir, fileprefix)

# Hot Backup.
flashrecoverydir = "/opt/oracle/flash_recovery_area/ORCL/"
remotebackupdir = "/mnt/extdrive/backups/oracle/ovmm.support.opentext.net/orcl/hotbackups"
oj.oracleHotBackup(flashrecoverydir, remotebackupdir)

# Send status email.
smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "OracleBackup: ovmm.support.opentext.net/orcl"
title = "Oracle Jobs"
oj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
