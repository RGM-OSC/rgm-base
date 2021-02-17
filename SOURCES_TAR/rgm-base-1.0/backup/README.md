# RGM Backup script

This script use [restic](https://restic.net/) as backup solution.  
Is fully designed to perform backup on RGM platform, with standard deployment without any changes in configuration.

## Usage

the backup script `/srv/rgm/backup/bin/rgm-backup.sh` is triggered by a daily **cron** job located at `/etc/cron.d/rgm_backup`

To browse over backup, use `restic` command:

```shell
restic -r /srv/rgm/backup/restic -p /root/.resticpwd snapshots
```

## Licence

BSD

## Author Information

Initial write by Vincent Fricou <vincent@fricouv.eu> (2020) release under the terms of BSD licence.
https://github.com/vfricou/script-rgm-restic-backup

Fork by SCC France, Eric Belhomme <ebelhomme@fr.scc.com>
- restic and rgm-backup.sh RPM packaging
- refactoring and option removal