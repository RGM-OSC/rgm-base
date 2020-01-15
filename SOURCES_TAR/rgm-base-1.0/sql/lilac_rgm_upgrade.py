#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eric Belhomme'
__copyright__ = '2020, SCC'
__credits__ = ['Eric Belhomme']
__license__ = 'GPLv2'
__version__ = '0.1'

import sys
import os.path
import datetime
import argparse
import subprocess
import MySQLdb


tables_list_id = (
    'export_job',
    'nagios_broker_module',
    'nagios_cgi_configuration',
    'nagios_cgi_configuration',
    'nagios_command',
    'nagios_contact',
    'nagios_contact_address',
    'nagios_contact_custom_object_var',
    'nagios_contact_group',
    'nagios_contact_group_member',
    'nagios_contact_notification_command',
    'nagios_dependency',
    'nagios_dependency_target',
    'nagios_escalation',
    'nagios_escalation_contact',
    'nagios_escalation_contactgroup',
    'nagios_host',
    'nagios_host_check_command_parameter',
    'nagios_host_contact_member',
    'nagios_host_contactgroup',
    'nagios_host_custom_object_var',
    'nagios_host_parent',
    'nagios_host_template',
    'nagios_host_template_autodiscovery_service',
    'nagios_host_template_inheritance',
    'nagios_hostgroup',
    'nagios_hostgroup_membership',
    'export_job',
    'nagios_service',
    'nagios_service_check_command_parameter',
    'nagios_service_contact_group_member',
    'nagios_service_contact_member',
    'nagios_service_custom_object_var',
    'nagios_service_group',
    'nagios_service_group_member',
    'nagios_service_template',
    'nagios_service_template_inheritance',
    'nagios_timeperiod',
    'nagios_timeperiod_entry',
    'nagios_timeperiod_exclude',
)


class sqlinfo:
    def __init__(self, host: str, user: str, pwd: str, db: str):
        self.info = {
            'host':   host,
            'user':   user,
            'passwd': pwd,
            'db':     db
        }
        self.cnx = None

    def connect(self) -> MySQLdb.connect:
        if not self.cnx:
            try:
                self.cnx = MySQLdb.connect(**self.info)
            except Exception as e:
                print("Failed to connect to SQL. Error {}".format(e))
                sys.exit(1)
        return self.cnx


class ids:
    def __init__(self, src: tuple, dst: tuple):
        self.src = set(src)
        self.dst = set(dst)

    def get_update(self):
        return self.dst.intersection(self.src)

    def get_create(self):
        return self.src.difference(self.dst)

    def get_delete(self):
        return self.dst.difference(self.src)


def compare_table_by_id(tablename) -> ids:

    cur = db_src.connect().cursor(MySQLdb.cursors.Cursor)
    cur.execute("SELECT id from {} WHERE id < 10000".format(tablename))
    src_ids = tuple(i[0] for i in cur.fetchall())
    cur.close()

    cur = db_dst.connect().cursor(MySQLdb.cursors.Cursor)
    cur.execute("SELECT id from {} WHERE id < 10000".format(tablename))
    dst_ids = tuple(i[0] for i in cur.fetchall())
    cur.close()

    return ids(src=src_ids, dst=dst_ids)


def get_source_row(tablename: str, tid: int) -> dict:
    cur = db_src.connect().cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * from {} WHERE id = {}".format(tablename, str(tid)))
    row = cur.fetchone()
    cur.close()
    return row


def escape_sql(value) -> str:
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        return "'" + value.replace("'", "\\'") + "'"
    elif isinstance(value, datetime.date):
        return "'{}'".format(value)
    return value


def create_update_rows_in_table(tablename: str, list_ids: tuple, update: bool = False):
    for tid in list_ids:
        row = get_source_row(tablename, tid)
        if len(row) > 0:
            stat = ''
            if update:
                row.pop('id')
                stat = "UPDATE `{table}` SET {cols} WHERE `id`={tid}".format(
                    table=tablename,
                    cols=", ".join(["`{}`={}".format(k, escape_sql(row[k])) for k in row.keys()]),
                    tid=tid
                )
            else:
                keys = row.keys()
                stat = "INSERT INTO `{table}` ({rows}) VALUES ({vals})".format(
                    table=tablename,
                    rows=", ".join(["`{}`".format(k) for k in keys]),
                    vals=", ".join([escape_sql(row[k]) for k in keys])
                )
            cur = db_dst.connect().cursor(MySQLdb.cursors.Cursor)
            print("{}".format(stat))
            cur.execute(stat)
            cur.close()


def upgrade_table(tablename):
    table_ids = compare_table_by_id(tablename)

    if len(table_ids.get_update()) > 0:
        create_update_rows_in_table(tablename, table_ids.get_update(), True)
    if len(table_ids.get_create()) > 0:
        create_update_rows_in_table(tablename, table_ids.get_create())
    for tid in table_ids.get_delete():
        stat = "DELETE FROM `{}` WHERE `id`={}".format(tablename, tid)
        cur = db_dst.connect().cursor(MySQLdb.cursors.Cursor)
        print(stat)
        cur.execute(stat)
        cur.close()


def ask_yes_no(req: str) -> bool:
    reply = input("{} (y/N)".format(req)).lower()
    if len(reply) == 0:
        return False
    if reply[0] == 'y':
        return True
    return False


def compare_table_cols(tablename: str):

    cur = db_src.connect().cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * from {}".format(tablename))
    src_rows = cur.fetchone()
    cur.close()
    cur = db_dst.connect().cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * from {} WHERE `id`='{}'".format(tablename, src_rows['id']))
    dst_rows = cur.fetchone()
    cur.close()

    tid = dst_rows.pop('id')
    update = {}
    for key in dst_rows.keys():
        if src_rows[key] != dst_rows[key]:
            if ask_yes_no(
                "table `{}` - column `{}` differs (old: '{}', new '{}'). Update ?".format(
                    tablename,
                    key,
                    dst_rows[key],
                    src_rows[key]
                )
            ):
                update[key] = src_rows[key]
            else:
                print("discard change for table `{}` - column `{}`".format(tablename, key))

    if len(update):
        cur = db_dst.connect().cursor(MySQLdb.cursors.DictCursor)
        stat = "UPDATE `{table}` SET {cols} WHERE `id`={tid}".format(
            table=tablename,
            cols=", ".join(["`{}`={}".format(k, escape_sql(update[k])) for k in update.keys()]),
            tid=tid
        )
        print("{}".format(stat))
        cur.execute(stat)
        cur.close()


def dump_injection(database: str, dumpfile: str):
    if not os.path.exists(dumpfile) or not os.path.isfile(dumpfile):
        print("Fatal: SQL dump file {} not found".format(dumpfile))
        sys.exit(1)

    with open(dumpfile) as fhdump:
        try:
            subprocess.run(
                ['/usr/bin/mysql', database],
                stdin=fhdump
            )
        except subprocess.CalledProcessError as e:
            print(e)
            sys.exit(1)


def main(maincfg, resources):

    def get_lilac_cfg(dbinfo: sqlinfo) -> dict:
        stat = "SELECT `key`, `value` FROM `lilac_configuration` WHERE `key`=\'db_build\' OR `key`=\'rgm_base_release\'"
        cur = dbinfo.connect().cursor(MySQLdb.cursors.DictCursor)
        cur.execute(stat)
        ret = {}
        for item in cur.fetchall():
            ret[item['key']] = int(item['value'])
        cur.close()
        if 'db_build' not in ret.keys():
            ret['db_build'] = 0
        if 'rgm_base_release' not in ret.keys():
            ret['rgm_base_release'] = 0
        return ret

    src_cfg = get_lilac_cfg(db_src)
    dst_cfg = get_lilac_cfg(db_dst)

    print("lilac source schema version: {} - lilac dest schema version: {}".format(
        src_cfg['db_build'],
        dst_cfg['db_build']
    ))
    if src_cfg['db_build'] != dst_cfg['db_build']:
        print("Fatal: Lilac build verson differs. First fix Lilac schema build version before upgrading RGM Core")
        sys.exit(1)

    print("lilac source RGM core release: {} - lilac dest RGM core release: {}".format(
        src_cfg['rgm_base_release'],
        dst_cfg['rgm_base_release']
    ))
    if src_cfg['rgm_base_release'] < dst_cfg['rgm_base_release']:
        if not ask_yes_no("Warning: lilac target RGM core release seems more recent than source ! Continue anyway ?"):
            print("User abort")
            sys.exit(0)
    elif src_cfg['rgm_base_release'] == dst_cfg['rgm_base_release']:
        if not ask_yes_no("Warning: lilac target RGM core release seems up to date ! Continue anyway ?"):
            print("User abort")
            sys.exit(0)

    if maincfg:
        compare_table_cols('nagios_main_configuration')
    if resources:
        compare_table_cols('nagios_resource')

    for table in tables_list_id:
        upgrade_table(table)

    for key in src_cfg.keys():
        cur = db_dst.connect().cursor(MySQLdb.cursors.Cursor)
        stat = "INSERT INTO lilac_configuration (`key`, `value`) VALUES ('{key}', '{value}') \
             ON DUPLICATE KEY UPDATE `value` = '{value}';".format(
            key=key,
            value=src_cfg[key]
        )
        print(stat)
        cur.execute(stat)
        cur.close()


# main start here

db_src = None
db_dst = None


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="RGM Lilac 'core' records upgrader",
        epilog=" version {} - copyright {}".format(__version__, __copyright__),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-H', '--host', type=str, help='SQL hostname', default='localhost')
    parser.add_argument('-u', '--user', type=str, help='SQL user', default='rgminternal')
    parser.add_argument('-p', '--password', type=str, help='SQL password', required=True)
    parser.add_argument('-s', '--srcdb', type=str, help='source database', default='lilac_tmp')
    parser.add_argument('-d', '--dstdb', type=str, help='target database', default='lilac')
    parser.add_argument('-i', '--inject', type=str, help='inject SQL dump on source database')
    parser.add_argument(
        '-m', '--maincfg', action='store_true', help='process nagios main configuration table', default=False
    )
    parser.add_argument('-r', '--resources', action='store_true', help='process nagios resources table', default=False)

    args = parser.parse_args()

    if args.inject is not None:
        dump_injection(args.srcdb, args.inject)

    db_src = sqlinfo(host=args.host, user=args.user, pwd=args.password, db=args.srcdb)
    db_dst = sqlinfo(host=args.host, user=args.user, pwd=args.password, db=args.dstdb)

    main(args.maincfg, args.resources)
