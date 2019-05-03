#/bin/bash
#
# install or update SQL schema
#
# Eric Belhomme <ebelhomme@fr.scc.com>

PATH="/sbin:/usr/sbin:/bin:/usr/bin"

LOGFILE='/var/log/rgm_manage_sql.log'
MYSQL_SOCKET=$(mktemp -u --suffix -mysql-sock)
MYSQL="/usr/bin/mysql -u root --socket=${MYSQL_SOCKET} --batch --silent --skip-column-names"
SQL_PRIVILEGES="ALL PRIVILEGES"
LOGLEVEL=3
DBNAME=
FILE_SQL_SCHEMA=
APPEND_SCRIPTS=
SQL_USER=
SQL_PASSWORD=
MYSQL_PID=

# allows to override some variables
if [ -e /etc/sysconfig/rgm/manage_sql ]; then
	source /etc/sysconfig/rgm/manage_sql
fi

function print_help () {
	cat <<EOF

$0 - install or update MariaDB SQL schema

usage:
$0 -d <database name> -s <SQL schema file> -u <SQL user> -p <SQL passwd> -r <user privileges>

	-l - log level : 0->debug, 1->fatal, 2->warning, 3->info, 4-> no log
	-d - database name to create if it not already exists
	-s - SQL schema file to init DB (leave blank to to init the DB)
	-a - Optional additional SQL scripts to append to SQL schema
	-u - SQL user to grant on specified DB (it host part not specified, defaults to 'localhost')
	-p - SQL password to set for DB connection
	-r - specific user privileges to apply (GRANT) on DB (defaults to 'ALL PRIVILEGES')
EOF
}

function logfile() {
	if [ $1 -ge $LOGLEVEL ]; then
		case $1 in
			0) echo -n "Debug: " >> $LOGFILE; ;;
			1) echo -n "Fatal: " >> $LOGFILE; ;;
			2) echo -n "Warning: " >> $LOGFILE; ;;
			3) echo -n "Info: " >> $LOGFILE; ;;
		esac
		if [ ! -z "$2" ]; then echo -e "$2" >> $LOGFILE; fi
	fi
}
if [ -e $LOGFILE ]; then touch $LOGFILE; fi

while getopts "d:s:a:u:p:r:l:" arg; do
	case "$arg" in
		d) DBNAME="$OPTARG";;
		s) FILE_SQL_SCHEMA="$OPTARG";;
		a) APPEND_SCRIPTS+=("$OPTARG");;
		u) SQL_USER="$OPTARG";;
		p) SQL_PASSWORD="$OPTARG";;
		r) SQL_PRIVILEGES="$OPTARG";;
		l) LOGLEVEL="$OPTARG";;
		*)  print_help ;;
	esac
done


logfile 0 "$0 -d $DBNAME -s $FILE_SQL_SCHEMA -u $SQL_USER -r $SQL_PRIVILEGES -l $LOGLEVEL"

if [[ ! $LOGLEVEL =~ [0-4] ]]; then
	LOGLEVEL=3
fi


# database name is mandatory
if [ -z $DBNAME ]; then
	logfile 1 "no database name provided"
	exit 1
fi

if [ ! -z $FILE_SQL_SCHEMA ]; then
	if [ ! -e $FILE_SQL_SCHEMA ]; then
		# SQL schema file not found
		logfile 1 "the specidied schema file is not found or not readable\n" \
			"  specified file was: $FILE_SQL_SCHEMA"
		exit 1
	fi
fi


### toolbox functions


function mysql_pid() {
	SQLPID=$(ps aux | grep '^mysql .*[m]ysqld' | awk '{print $2}')
	if [ ! -z "$1" ]; then
		logfile 3 "Killing SQL PID $SQLPID"
		kill -$1 $SQLPID
	fi
	echo $SQLPID
}

function mysql_service() {
	COUNT=0
	RET=1
	while : ; do
		/usr/bin/systemctl $1 mariadb
		if [ $? -eq 0 ]; then
			RET=0
			break;
		fi
		sleep 1
		COUNT=$(( $COUNT =1 ))
		if [ $COUNT -gt 10 ]; then
			logfile 1 "Failed: failed to $1 mariadb service"
			break;
		fi
	done
	return $RET
}


function start_sql_safe() {
	RET=1
	mysql_service stop
	if [ $? -ne 0 ]; then exit 1; fi
	/usr/bin/systemctl status mariadb &>> $LOGFILE
	if [ $? -ne 3 ]; then
		logfile 1 "mariadb service still running. aborting"
		return $RET
	fi
	/usr/bin/mysqld_safe --skip-grant-tables --no-auto-restart --skip-networking --socket=${MYSQL_SOCKET} &>> $LOGFILE
	if [ $? -ne 0 ]; then
		logfile 1 "Failed: mysqld_safe did not start successfully"
		mysql_pid "9" &> /dev/null
	else
		RET=0
		MYSQL_PID=$(mysql_pid)
	fi
	return $RET
}

function connect_sql_safe() {
	# wait for the mysqld socket ready to handle SQL cnx
	RET=1
	COUNT=0
	while : ; do
		$MYSQL -e '\q' &> /dev/null
		if [ $? -eq 0 ]; then
			logfile 3 "SQL connection in safe mode successfull"
			RET=0
			break;
		fi
		sleep 1
		COUNT=$(( $COUNT +1 ))
		if [ $COUNT -gt 10 ]; then
			logfile 1 "Failed to connect mysqld_safe"
			break;
		fi
	done
	return $RET
}


### main section starts here

# stop mariadb daemon then restarts it with no network and a random socket
# so we ensure nothing can connect while it runs in safe mode with no authentication
start_sql_safe
if [ $? -eq 0 ]; then
	connect_sql_safe
	if [ $? -eq 0 ]; then

		# create and init database if it not already exists
		if [ "$($MYSQL -e 'show databases' | grep -c ^${DBNAME}\$)" == "0" ]; then
			logfile 3 "create database $DBNAME"
			$MYSQL -e "CREATE DATABASE ${DBNAME};"
			if [ ! -z $FILE_SQL_SCHEMA ]; then
				$MYSQL ${DBNAME} < ${FILE_SQL_SCHEMA}
				if [ $? -eq 0 ]; then
					logfile 3 "successfully ran $FILE_SQL_SCHEMA on database $DBNAME"
				else
					logfile 2 "failed to run $FILE_SQL_SCHEMA on database $DBNAME"
				fi
			fi
		else
			logfile 3 "database $DBNAME already exists. skipping DB creation"
		fi

		# execute optional scripts if -a defined
		for ITEM in ${APPEND_SCRIPTS[@]}; do
			if [ -e $ITEM ]; then
				logfile 3 "applying extra SQL script: $ITEM"
				$MYSQL ${DBNAME} < $ITEM
				if [ $? -eq 0 ]; then
					logfile 3 "successfully ran $ITEM on database $DBNAME"
				else
					logfile 2 "failed to run $ITEM on database $DBNAME"
				fi
			else
				logfile 2 "Failed to stat $ITEM file - ignored.." 
			fi
		done

		# is a user is supplied, grant privileges on DB to that user
		if [ ! -z $SQL_USER ]; then
			# as mariadb is running in safe mode with --skip-grant-tables
			# flush privileges is required to restart granting prior creating user
			# or granting privileges./srv/eyesofnetwork/nagios/var/log/rw/live
			# as a consequence, we'll loose the password-less auth afterward...
			# so we create a temporary SQL script to apply all modifications
			# in one shoot
			SQLFILE=$(mktemp --suffix -sql)
			echo "USE mysql;" >> $SQLFILE
			USERNAME=$(echo $SQL_USER | cut -d '@' -f 1)
			if [[ $SQL_USER =~ .+@.+ ]]; then
				USERHOST=$(echo $SQL_USER | cut -d '@' -f 2)
			else
				USERHOST='localhost'
			fi
			UEXISTS=$($MYSQL mysql -e "SELECT COUNT(*) FROM user WHERE user = '$USERNAME' AND host = '$USERHOST';")
			if [ "$UEXISTS" == "0" ]; then
				logfile 3 "create user '${USERNAME}'@'${USERHOST}'"
				echo "FLUSH PRIVILEGES;" >> $SQLFILE
				echo "CREATE USER '${USERNAME}'@'${USERHOST}';" >> $SQLFILE
				echo "SET PASSWORD FOR '${USERNAME}'@'${USERHOST}' = PASSWORD('$SQL_PASSWORD');" >> $SQLFILE
			else
				logfile 3 "user '${USERNAME}'@'${USERHOST}' already exists. skipping..."
			fi
			echo "FLUSH PRIVILEGES;" >> $SQLFILE
			echo "GRANT ${SQL_PRIVILEGES} ON \`${DBNAME}\`.* TO '${USERNAME}'@'${USERHOST}';" >> $SQLFILE
			$MYSQL mysql < $SQLFILE
			rm -f $SQLFILE
		fi

	else
		# failed to properly start a mysqld_safe instance
		# kill anything that might remain then restart mariadb service
		mysql_pid "9" &> /dev/null
	fi
fi

# terminate safe instance and resume normal mariadb instance
mysql_pid "15" &> /dev/null
COUNT=0
while : ; do
  sleep 1
  MYSQL_PID=$(mysql_pid)
  if [ -z $MYSQL_PID ]; then
	logfile 3 "mysqld_safe process terminated."
	break;
  fi
  COUNT=$(( $COUNT +1 ))
  if [ $COUNT -gt 10 ]; then
	logfile 2 "mysqld still running... killing PID $MYSQL_PID"
	mysql_pid "9" &> /dev/null
	sleep 2
	break
  fi
done
logfile 3 "restart mariadb"
mysql_service restart
exit 0
