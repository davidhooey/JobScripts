import OracleJobs

oj = OracleJobs.OracleJobs()

dpdumpdir = "/opt/oracle/admin/ogre/dpdump/"
localbackupdir = "/home/oracle/Backups/"
remotebackupdir = "/mnt/extdrive/backups/oracle/ogre.support.opentext.net/ogre/datapumpbackups/"
fileprefix = "ogre_ogre_full_expdp_"

oj.oracleDataPumpExport(dpdumpdir, localbackupdir, remotebackupdir, fileprefix)

smtpserver = 'mail.opentext.com'
sender = 'davidh@opentext.com'
receivers = ['davidh@opentext.com']
subject = "OracleBackup: ogre.support.opentext.net/ogre"
title = "Oracle Backup"

oj.sendStatusEmail(smtpserver, sender, receivers, subject, title)
