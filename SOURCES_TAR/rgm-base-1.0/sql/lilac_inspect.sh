#!/bin/bash


CRE='\033[0;31m'
CGR='\033[0;32m'
CYE='\033[0;33m'
CNC='\033[0m'
CBOLD='\033[1m'

function process_table() {
	TABLE="$1"
	CORE=$($MYSQL -e "SELECT COUNT(*) FROM $TABLE WHERE id < 10000;")
	COLC=$CRE
	if [ $CORE -gt 0 ]; then
		COLC=$CGR
	fi
	INST=$($MYSQL -e "SELECT COUNT(*) FROM $TABLE WHERE id >= 10000;")
	COLI=$CRE
	if [ $INST -gt 0 ]; then
		COLI=$CGR
	fi

	printf "Table ${CBOLD}%-45s${CNC} - core records: ${COLC}%5s${CNC} - instance records: ${COLI}%6s${CNC}\n" $TABLE $CORE $INST
}


LILACCFG=/srv/rgm/lilac/includes/lilac-conf.php
LILACUSR=$(grep "'user'\s*=>" $LILACCFG | sed "s/[',>]//g" | awk '{print$3}')
LILACPWD=$(grep "'password'\s*=>" $LILACCFG | sed "s/[',>]//g" | awk '{print$3}')
LILACDB=$(grep 'dbname=' $LILACCFG | sed "s/[',]//g" | cut -d '=' -f 4)
MYSQL="mysql --user=$LILACUSR --password=$LILACPWD --batch -N $LILACDB"
process_table "export_job"
process_table "import_job"
for TABLE in $($MYSQL -e "SHOW TABLES WHERE Tables_in_lilac LIKE 'nagios_%';"); do
	process_table "$TABLE"
done
 
