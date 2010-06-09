import OracleJobs

oj = OracleJobs.OracleJobs()

dpdumpdir = "/opt/oracle/admin/orcl/dpdump/"
localbackupdir = "/home/oracle/Backups/"
remotebackupdir = "/mnt/extdrive/backups/oracle/ovmm.support.opentext.net/orcl/datapumpbackups/"
fileprefix = "ovmm_orcl_full_expdp_"

oj.oracleDataPumpExport(dpdumpdir, localbackupdir, remotebackupdir, fileprefix)

flashrecoverydir = "/opt/oracle/flash_recovery_area/ORCL/"
remotebackupdir = "/mnt/extdrive/backups/oracle/ovmm.support.opentext.net/orcl/hotbackups"

oj.oracleHotBackup(flashrecoverydir, remotebackupdir)

smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "OracleBackup: ovmm.support.opentext.net/orcl"
title = "Oracle Backup"

oj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
