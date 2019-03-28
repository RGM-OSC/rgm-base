#!/bin/bash
#
# Lilac SQL schema management
#
# Eric Belhomme <ebelhomme@fr.scc.com>

function print_help() {
	cat <<EOF
This scripts will dump Lilac schema with only specified subsets of records

Caution: only nagios_* table records are covered. Other tables includes *ONLY*
the table schema drop/creation

FOR A FULL BACKUP, use mysqldump command instead of this script !

Option:
  -h        : this help
  -d <file> : destination file for SQL dump
  -c        : Dumps *ONLY* RGM core records (eg. ids < 10000) - default
  -s        : Dumps *ONLY* installation specific lilac objects (eg. ids >= 10000)
  -f        : Dumps *BOTH* core & specific lilac object (eg. -c -s)
  -r        : remove AUTO_INCREMENTS values from CREATE statements
	-b <db>   : Lilac database name - default: autoconfig
	-u <user> : SQL user with granted privileges for Lilac DB - default: autoconfig
	-p <pwd>  : SQL user password - default: autoconfig
EOF
	exit 1
}

SQLOUT=
DUMPCLAUSE="--where='id<10000'"
RESETINCR=0
LILACUSR=
LILACPWD=
LILACDB=

while getopts hd:csfrb:u:p: arg; do
	case "$arg" in
		h) print_help;;
		d) SQLOUT="$OPTARG";;
		c) DUMPCLAUSE="--where='id<10000'";;
		s) DUMPCLAUSE="--where='id>=10000'";;
		f) DUMPCLAUSE=;;
		r) RESETINCR=1;;
		b) LILACDB="$OPTARG";;
		u) LILACUSR="$OPTARG";;
		p) LILACPWD="$OPTARG";;
		*) print_help;;
	esac
done

if [ -z $SQLOUT ]; then
	print_help
fi
if [ -e $SQLOUT ]; then
	echo "Warning: file $SQLOUT already exists !"
	echo "Overwrite ? (y/N)"
	read -r YESNO
	if [[ ! $YESNO =~ [yY] ]]; then
		echo "User abort"
		exit 1
	else
		rm -f $SQLOUT
	fi
fi
touch $SQLOUT
if [ $? -ne 0 ]; then
	echo "Error: failed to create file $SQLOUT"
	exit 1
fi

LILACCFG=/srv/rgm/lilac/includes/lilac-conf.php
if [ -z $LILACUSR ]; then
	LILACUSR=$(grep "'user'\s*=>" $LILACCFG | sed "s/[',>]//g" | awk '{print$3}')
fi
if [ -z $LILACPWD ]; then
	LILACPWD=$(grep "'password'\s*=>" $LILACCFG | sed "s/[',>]//g" | awk '{print$3}')
fi
if [ -z $LILACDB ]; then
	LILACDB=$(grep 'dbname=' $LILACCFG | sed "s/[',]//g" | cut -d '=' -f 4)
fi
SQLOPTS="--user=${LILACUSR} --password=${LILACPWD}"

# enumerates tables in Lilac DB then dump them one by one
for TABLE in $(mysql $SQLOPTS -N $LILACDB --execute "SHOW TABLES;"); do
	if [[ $TABLE =~ ^nagios_.* ]]; then
		echo "dump table $TABLE with values"
		mysqldump $SQLOPTS --compact --add-drop-table $LILACDB $TABLE $DUMPCLAUSE >> $SQLOUT
	else
		echo "dump table $TABLE schema only"
		mysqldump $SQLOPTS --compact --add-drop-table --no-data $LILACDB $TABLE >> $SQLOUT
	fi
done

# remove AUTO_INCREMENT counter value from the CREATE statement
if [ $RESETINCR -eq 1 ]; then
	sed -i 's| AUTO_INCREMENT=[0-9]\+ | |' $SQLOUT
fi
