#!/bin/bash

function print_help() {
	cat <<EOF

$0 - set or reset Lilac tables AUTO_INCREMENT values

Option:
  -s  : set AUTO_INCREMENT >= 10000
  -r  : reset AUTO_INCREMENT to highest value currently in use on table +1

EOF
	exit 1
}
MODE=
while getopts hsr arg; do
	case "$arg" in
		h) print_help;;
		s) MODE="set";;
		r) MODE="reset";;
		*) print_help;;
	esac
done

if [ -e $MODE ]; then
	print_help
fi

CGR='\033[0;32m'
CYE='\033[0;33m'
CNC='\033[0m'
CBOLD='\033[1m'

LILACCFG=/srv/rgm/lilac/includes/lilac-conf.php
LILACUSR=$(grep "'user'\s*=>" $LILACCFG | sed "s/[',>]//g" | awk '{print$3}')
LILACPWD=$(grep "'password'\s*=>" $LILACCFG | sed "s/[',>]//g" | awk '{print$3}')
LILACDB=$(grep 'dbname=' $LILACCFG | sed "s/[',]//g" | cut -d '=' -f 4)
MYSQL="mysql --user=$LILACUSR --password=$LILACPWD --batch -N $LILACDB"

function process_table() {
	TABLE="$1"

	MAX_ID=$($MYSQL -e "SELECT MAX(id) FROM $TABLE;")
	if [ "$MAX_ID" == "NULL" ]; then
		MAX_ID=0
	fi
	if [ $MODE == "set" ]; then
		if [ $MAX_ID -lt 10000 ]; then
			COL=$CGR
			MAX_ID=10000
		else
			COL=$CYE
			MAX_ID=$(( $MAX_ID + 1 ))
		fi
		printf "set AUTO_INCREMENT on table ${CBOLD}%-45s${CNC} - value: ${COL}%s${CNC}\n" $TABLE $MAX_ID
		$MYSQL -e "ALTER TABLE $TABLE AUTO_INCREMENT = $MAX_ID;"
	elif [ $MODE == "reset" ]; then
		CUR_INCR=$($MYSQL -e "SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '${LILACDB}' AND TABLE_NAME = '${TABLE}';")
		if [ $MAX_ID -lt $CUR_INCR ]; then
			MAX_ID=$(( $MAX_ID + 1 ))
			if [ $MAX_ID -gt 10000 ]; then
				COL=$CYE
			else
				COL=$CGR
			fi
			printf "reset AUTO_INCREMENT on table ${CBOLD}%-45s${CNC} - value: ${COL}%s${CNC}\n" $TABLE $MAX_ID
			$MYSQL -e "ALTER TABLE $TABLE AUTO_INCREMENT = $MAX_ID;"
		else
			printf "Dont't alter AUTO_INCREMENT on table %-45s as value is %s\n" $TABLE $MAX_ID
		fi
	fi
	
}

for TABLE in $($MYSQL --execute "SHOW TABLES;"); do
	if [[ $TABLE =~ ^(nagios_.*|.+port_job|label)$ ]]; then
		process_table "$TABLE"
	fi
done
