#/bin/bash
#
# install or update SQL schema
#
# Eric Belhomme <ebelhomme@fr.scc.com>

PATH="/sbin:/usr/sbin:/bin:/usr/bin"

DBNAME="$1"
FILE_SQL_SCHEMA="$2"
SQL_USER="$3"
SQL_PASSWORD="$4"
SQL_PRIVILEGES="$5"


if [ -z $DBNAME ]; then
    # database name not provided
    exit 1
fi

if [ -z $FILE_SQL_SCHEMA ]; then
    # SQL schema file not provided
    exit 2
fi

if [ ! -e $FILE_SQL_SCHEMA ]; then
    # SQL schema file not found
    exit 3
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

# create and init database if it not already exists
if [ "$($MYSQL -e 'show databases' | grep -c ^${DBNAME}\$)" == "0" ]; then
    $MYSQL -e "CREATE DATABASE ${DBNAME};"
    cat ${FILE_SQL_SCHEMA} | $MYSQL ${DBNAME}
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
    if [ -z $SQL_PRIVILEGES ]; then SQL_PRIVILEGES='ALL privileges'; fi
    $MYSQL -e "GRANT ${SQL_PRIVILEGES} ON `${DBNAME}`.* TO '${USERNAME}'@'${USERHOST}';"
fi

# terminate safe instance and resume normal mariadb instance
kill -15 $MYSQL_PID
systemctl start mariadb
exit 0