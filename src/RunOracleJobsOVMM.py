import OracleJobs

oj = OracleJobs.OracleJobs()

dpdumpdir = "/opt/oracle/admin/orcl/dpdump/"
localbackupdir = "/home/oracle/Backups/"
remotebackupdir = "/mnt/panzer/Oracle/ovmm.support.opentext.net/orcl/DataPumpBackups/"
fileprefix = "ovmm_orcl_full_expdp_"

oj.oracleDataPumpExport(dpdumpdir, localbackupdir, remotebackupdir, fileprefix)

flashrecoverydir = "/opt/oracle/flash_recovery_area/ORCL/"
remotebackupdir = "/mnt/panzer/Oracle/ovmm.support.opentext.net/orcl/HotBackups"

oj.oracleHotBackup(flashrecoverydir, remotebackupdir)

smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "OracleBackup: ovmm.support.opentext.net/orcl"
title = "Oracle Backup"

oj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
