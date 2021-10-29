#!/bin/bash -e
#
# RGM platform backup script using restic solution
#
# forked from https://github.com/vfricou/script-rgm-restic-backup
#
# Vincent FRICOU <vincent@fricouv.eu> 2020
# SCC France 2020 - Eric Belhomme <ebelhomme@fr.scc.com>

RESTICEXTRAVARS=''
RESTICPWDLEN='110'
NOW="$(date +"%Y-%m-%d_%H%M")"
LOGFILE="${BACKUP_ROOT}/logs/${NOW}.log"
if [ ! -d "$(dirname "$LOGFILE")" ]; then
    mkdir -p "$(dirname "$LOGFILE")"
fi
touch "$LOGFILE" && chmod 0640 "$LOGFILE" || exit 1

# User definitions
if [ -e "/srv/rgm/backup/environment" ]; then
    # shellcheck source=/dev/null
    . "/srv/rgm/backup/environment"
else
    echo "Fatal: /srv/rgm/backup/environment not found" | tee "${LOGFILE}"
    exit 1
fi

if [[ -z "$RESTICINCLUDEPATHS" || ! -e "$RESTICINCLUDEPATHS" || -z "$RESTICEXCLUDEPATHS" || ! -e "$RESTICEXCLUDEPATHS" ]]; then
    cat <<EOF | tee "${LOGFILE}"
Fatal : variables RESTICINCLUDEPATHS of RESTICEXCLUDEPATHS not specified or file missing"
Please check file:
  - /srv/rgm/backup/environment 

EOF
    exit 1
fi

if [ -z "$BACKUP_ROOT" ]; then BACKUP_ROOT='/srv/rgm/backup'; fi
if [ -z "$RESTICBIN" ]; then RESTICBIN='/usr/bin/restic'; fi
if [ -z "$RESTICPWDFILE" ]; then RESTICPWDFILE='/root/.resticpwd'; fi
if [ -z "$MARIADBCLIENTCNF" ]; then MARIADBCLIENTCNF='/root/.my.cnf'; fi
if [ -z "$BACKUP_PATH" ]; then BACKUP_PATH="${BACKUP_ROOT}/restic"; fi
if [ -z "$RESTICRETENTION" ]; then RESTICRETENTION='--keep-daily 7 --keep-weekly 4 --keep-monthly 3'; fi
if [ -z "$RESERVATION_FILE_SIZE" ]; then RESERVATION_FILE_SIZE='5G'; fi
RESTIC_REBUILD_LOCK="${BACKUP_ROOT}/.restic-rebuild.lock"

function log_tee() {
    echo "-----------------------------------------------------------" | tee -a "${LOGFILE}"
    echo -e "# $1\n" | tee -a "${LOGFILE}"
}

function create_clean_target() {
    if [ -d "${1}" ]; then
        rm -rf "${1:?}/"*
    else
        mkdir -p "${1}"
    fi
}

cat <<EOF | tee "${LOGFILE}"
# $(basename "$0") started at $(date +"%d %b %Y - %H:%M:%S")
-----------------------------------------------------------

EOF

# generate and secure a random password if none exists yet
if [ ! -d ${BACKUP_PATH}/index ]; then
    echo "Generating restic repository password in ${RESTICPWDFILE} file"
    < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c"${1:-${RESTICPWDLEN}}" > ${RESTICPWDFILE}
    chmod 0400 "${RESTICPWDFILE}"
    ${RESTICBIN} --repo ${BACKUP_PATH} -p ${RESTICPWDFILE} init
fi

# prune old restic snapshots
log_tee "Start backup retention cleaning (with retention ${RESTICRETENTION})"
if [ -f "$RESTIC_REBUILD_LOCK" ]; then rm "$RESTIC_REBUILD_LOCK"; fi
${RESTICBIN} --repo ${BACKUP_PATH} -p ${RESTICPWDFILE} forget ${RESTICRETENTION} --prune | tee -a "${LOGFILE}"
fallocate -l ${RESERVATION_FILE_SIZE} "$RESTIC_REBUILD_LOCK"
log_tee "End backup retention cleaning"

# dump & backup mariadb databases
log_tee "Starting mysql dumps"
BACKUPTARGET="${BACKUP_ROOT}/dumps/mariadb"
create_clean_target "$BACKUPTARGET"
for db in $(mysql --defaults-extra-file=${MARIADBCLIENTCNF} -Bse 'show databases' | grep -Pv 'information_schema|performance_schema|mysql'); do
    File="${BACKUPTARGET}/${db}.sql"
    echo "Dumping database ${db}" | tee -a "${LOGFILE}"
    mysqldump --defaults-extra-file=${MARIADBCLIENTCNF} --compact --order-by-primary --add-drop-table "${db}" -R 2>> "${LOGFILE}" > "$File"
done

# dump & backup influxdb databases
log_tee "Starting influxdb dumps"
BACKUPTARGET="${BACKUP_ROOT}/dumps/influxdb"
create_clean_target "$BACKUPTARGET"
for db in $(influx -precision rfc3339 -execute 'show databases' | grep -ve '^name$' -ve 'name: databases' -ve '----'); do
    Folder="${BACKUPTARGET}/${db}"
    echo "Dumping database ${db}" | tee -a "${LOGFILE}"
    influxd backup -database "${db}" "${Folder}" 1>> "${LOGFILE}" 2>/dev/null
done

# backup flat filesystem
log_tee "Start flat filesystem backup"
echo -e "\nBackup folders ${BACKUPPATHLIST[*]}" | tee -a "${LOGFILE}"

${RESTICBIN} --repo "${BACKUP_PATH}" \
    -p "${RESTICPWDFILE}" \
    backup "$RESTICEXTRAVARS" \
    --exclude-file $RESTICEXCLUDEPATHS \
    --files-from $RESTICINCLUDEPATHS \
    "$RESTICPWDFILE" "$MARIADBCLIENTCNF" "${BACKUP_ROOT}/dumps" | tee -a "${LOGFILE}"

cat <<EOF | tee "${LOGFILE}"

-----------------------------------------------------------
# $(basename "$0") finished at $(date +"%d %b %Y - %H:%M:%S")
EOF
# vim: expandtab sw=4 ts=4: