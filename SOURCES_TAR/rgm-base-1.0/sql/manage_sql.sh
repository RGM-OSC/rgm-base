#/bin/bash
#
# install or update SQL schema
#
# Eric Belhomme <ebelhomme@fr.scc.com>

PATH="/sbin:/usr/sbin:/bin:/usr/bin"

function help () {
  cat <<EOF

$0 - install or update MariaDB SQL schema

usage:
$0 -d <database name> -s <SQL schema file> -u <SQL user> -p <SQL passwd> -r <user privileges>

    -d - database name to create if it not already exists
    -s - SQL schema file to init DB (leave blank to to init the DB)
    -u - SQL user to grant on specified DB (it host part not specified, defaults to 'localhost')
    -p - SQL password to set for DB connection
    -r - specific user privileges to apply (GRANT) on DB (defaults to 'ALL PRIVILEGES')
EOF
}
DBNAME=
FILE_SQL_SCHEMA=
SQL_USER=
SQL_PASSWORD=
SQL_PRIVILEGES="ALL PRIVILEGES"

while getopts "dsupr" option; do
  case "$1" in
    -d)
      DBNAME=$2; shift; shift; ;;
    -s)
      FILE_SQL_SCHEMA=$2; shift; shift; ;;
    -u)
      SQL_USER=$2; shift; shift; ;;
    -p)
      SQL_PASSWORD=$2; shift; shift; ;;
    -r)
    SQL_PRIVILEGES=$2; shift; shift; ;;
    *)
      help
      shift
      ;;
  esac
done


if [ -z $DBNAME ]; then
  # database name not provided
  exit 1
fi

if [ ! -z $FILE_SQL_SCHEMA ]; then
  if [ ! -e $FILE_SQL_SCHEMA ]; then
    # SQL schema file not found
    exit 3
  fi
fi

MYSQL_SOCKET=$(mktemp -u --suffix -mysql-sock)
MYSQL="/usr/bin/mysql -u root --socket=${MYSQL_SOCKET} --batch --silent --skip-column-names"

# stop mariadb daemon then restarts it with no network and a random socket
# so we ensure nothing can connect while it runs in safe mode with no authentication
systemctl stop mariadb
/usr/bin/mysqld_safe --skip-grant-tables --no-auto-restart --skip-networking --socket=${MYSQL_SOCKET} &> /dev/null
MYSQL_PID=$(ps aux | grep '^mysql .*[m]ysqld' | awk '{print $2}')
if [ -z $MYSQL_PID ]; then
  # failed to start mariadb in safe mode
  systemctl start mariadb
  exit 1
fi

# wait for the mysqld socket ready to handle SQL cnx
COUNT=0
while : ; do
  $MYSQL -e '\q' &> /dev/null
  if [ $? -eq 0 ]; then
    break;
  fi
  COUNT=$(( $COUNT +1 ))
  if [ $COUNT -gt 10 ]; then
    echo "Failed to connect mysqld_safe"
    exit 1
  fi
  sleep 1
done

# create and init database if it not already exists
if [ "$($MYSQL -e 'show databases' | grep -c ^${DBNAME}\$)" == "0" ]; then
  $MYSQL -e "CREATE DATABASE ${DBNAME};"
  if [ ! -z $FILE_SQL_SCHEMA ]; then
    $MYSQL ${DBNAME} < ${FILE_SQL_SCHEMA}
  fi
fi

# is a user is supplied, grant privileges on DB to that user
if [ ! -z $SQL_USER ]; then
  USERNAME=$(echo $SQL_USER | cut -d '@' -f 1)
  USERHOST=$(echo $SQL_USER | cut -d '@' -f 2)
  if [ -z $USERHOST ]; then USERHOST='localhost'; fi
  if [ -z $SQL_PASSWORD ]; then
    $MYSQL -e "CREATE USER IF NOT EXISTS ${USERNAME};"
  else
    $MYSQL -e "CREATE USER IF NOT EXISTS ${USERNAME} IDENTIFIED BY '${SQL_PASSWORD}';"
  fi
  $MYSQL -e "GRANT ${SQL_PRIVILEGES} ON `${DBNAME}`.* TO '${USERNAME}'@'${USERHOST}';"
fi

# terminate safe instance and resume normal mariadb instance
kill -15 $MYSQL_PID
COUNT=0
while : ; do
  sleep 1
  ps aux | grep '^mysql .*[m]ysqld' &> /dev/null
  if [ $? -eq 1 ]; then
    break;
  fi
  COUNT=$(( $COUNT +1 ))
  if [ $COUNT -gt 10 ]; then
    kill -9 $MYSQL_PID
    sleep 2
    break
  fi
done
systemctl start mariadb
exit 0