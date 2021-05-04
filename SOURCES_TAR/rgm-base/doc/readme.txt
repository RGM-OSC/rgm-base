Base package for common RGM utility scripts

* manage_sql.sh - a shell script to handle SQL database RGM creation/updates

usage:
manage_sql.sh -d <database name> -s <SQL schema file> -u <SQL user> -p <SQL passwd> -r <user privileges>

    -d - database name to create if it not already exists
    -s - SQL schema file to init DB (leave blank to to init the DB)
    -u - SQL user to grant on specified DB (it host part not specified, defaults to 'localhost')
    -p - SQL password to set for DB connection
    -r - specific user privileges to apply (GRANT) on DB (defaults to 'ALL PRIVILEGES')