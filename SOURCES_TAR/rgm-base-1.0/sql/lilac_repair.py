#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RGM Lilac database maintenance tool.

This script tries to repair corrupted Lilac database when 'core' and 'instance' records are melted
both together.

Usage:

During the first execution, the script will display low records (with `id` < 10000) for some
key tables and ask you for the last 'core' record for that table.

User answers are saved in a config file (see --config argument) in YAML format so the script will
*not* request anymore for user input !
If you need to modify a value, you can either edit the config file *or* remove the entry from the
config file (or reset the entry to 0)

The script will then try to re-index all SQL tables in a consitent way, by moving all records that
are not considered as 'core' to an `id` > 10000

Once this is done, you should:

  1. reset SQL AUTO_INCREMENT values:
     -> use /usr/share/rgm/lilac_manage_auto_increments.sh -s

  2. try a Nagios export (using WEB GUI or RGMAPI). The export should complete successfully. If it
     fail, then something went wrong. In that case you need to restore your Lilac dump...

Caution : This script can break your Lilac database in an unrecoverable way, you should *always*
          dump your database securely before any attempt !
          For easy DB dump, you can invoke "/usr/share/rgm/lilac_dumper.sh -f -d lilac_dump.sql"
"""

__author__ = 'Eric Belhomme'
__copyright__ = '2020, SCC'
__credits__ = ['Eric Belhomme']
__license__ = 'GPLv2'
__version__ = '0.1'

import sys
import os.path
import MySQLdb
import yaml
import logging
import argparse
import pprint
pp = pprint.PrettyPrinter()

logger = logging


lilac_tables_id = {
    'nagios_command': {
        'indexes': None,
        'reference_tables': {
            'nagios_contact_notification_command': {
                'columns': ['command'],
                'ids_updated': set(),
            },
            'nagios_host': {
                'columns': ['check_command'],
                'ids_updated': set(),
            },
            'nagios_host_template': {
                'columns': ['check_command'],
                'ids_updated': set(),
            },
            'nagios_service_template': {
                'columns': ['check_command'],
                'ids_updated': set(),
            },
            'nagios_service': {
                'columns': ['check_command'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_hostgroup': {
        'indexes': None,
        'reference_tables': {
            'nagios_hostgroup_membership': {
                'columns': ['hostgroup'],
                'ids_updated': set(),
            },
            'nagios_service': {
                'columns': ['hostgroup'],
                'ids_updated': set(),
            },
            'nagios_dependency': {
                'columns': ['hostgroup'],
                'ids_updated': set(),
            },
            'nagios_dependency_target': {
                'columns': ['target_hostgroup'],
                'ids_updated': set(),
            },
            'nagios_escalation': {
                'columns': ['hostgroup'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_service_group': {
        'indexes': None,
        'reference_tables': {
            'nagios_service_group_member': {
                'columns': ['service_group'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_timeperiod': {
        'indexes': None,
        'reference_tables': {
            'nagios_timeperiod_entry': {
                'columns': ['timeperiod_id'],
                'ids_updated': set(),
            },
            'nagios_timeperiod_exclude': {
                'columns': ['timeperiod_id'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_contact': {
        'indexes': None,
        'reference_tables': {
            'nagios_contact_address': {
                'columns': ['contact'],
                'ids_updated': set(),
            },
            'nagios_contact_custom_object_var': {
                'columns': ['contact'],
                'ids_updated': set(),
            },
            'nagios_contact_group_member': {
                'columns': ['contact'],
                'ids_updated': set(),
            },
            'nagios_contact_notification_command': {
                'columns': ['contact_id'],
                'ids_updated': set(),
            },
            'nagios_escalation_contact': {
                'columns': ['contact'],
                'ids_updated': set(),
            },
            'nagios_host_contact_member': {
                'columns': ['contact'],
                'ids_updated': set(),
            },
            'nagios_service_contact_member': {
                'columns': ['contact'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_contact_group': {
        'indexes': None,
        'reference_tables': {
            'nagios_contact_group_member': {
                'columns': ['contactgroup'],
                'ids_updated': set(),
            },
            'nagios_escalation_contactgroup': {
                'columns': ['contactgroup'],
                'ids_updated': set(),
            },
            'nagios_host_contactgroup': {
                'columns': ['contactgroup'],
                'ids_updated': set(),
            },
            'nagios_service_contact_group_member': {
                'columns': ['contact_group'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_service_template': {
        'indexes': None,
        'reference_tables': {
            'nagios_dependency': {
                'columns': ['service_template'],
                'ids_updated': set(),
            },
            'nagios_escalation': {
                'columns': ['service_template'],
                'ids_updated': set(),
            },
            'nagios_service_custom_object_var': {
                'columns': ['service_template'],
                'ids_updated': set(),
            },
            'nagios_service_check_command_parameter': {
                'columns': ['template'],
                'ids_updated': set(),
            },
            'nagios_service_template_inheritance': {
                'columns': ['source_template', 'target_template'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_host_template': {
        'indexes': None,
        'reference_tables': {
            'nagios_dependency': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_escalation': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_host_check_command_parameter': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_host_contactgroup': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_host_custom_object_var': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_host_parent': {
                'columns': ['child_host_template'],
                'ids_updated': set(),
            },
            'nagios_host_template_autodiscovery_service': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_host_template_inheritance': {
                'columns': ['source_template', 'target_template'],
                'ids_updated': set(),
            },
            'nagios_hostgroup_membership': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'nagios_service': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'autodiscovery_device': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
            'autodiscovery_device_template_match': {
                'columns': ['host_template'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_host': {
        'indexes': None,
        'reference_tables': {
            'nagios_dependency': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_dependency_target': {
                'columns': ['target_host'],
                'ids_updated': set(),
            },
            'nagios_escalation': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_host_check_command_parameter': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_host_contact_member': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_host_contactgroup': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_host_custom_object_var': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_host_template_inheritance': {
                'columns': ['source_host'],
                'ids_updated': set(),
            },
            'nagios_hostgroup_membership': {
                'columns': ['host'],
                'ids_updated': set(),
            },
            'nagios_host_parent': {
                'columns': ['child_host', 'parent_host'],
                'ids_updated': set(),
            },
            'nagios_service': {
                'columns': ['host'],
                'ids_updated': set(),
            },
        },
    },
    'nagios_service': {
        'indexes': None,
        'reference_tables': {
            'nagios_dependency': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_dependency_target': {
                'columns': ['target_service'],
                'ids_updated': set(),
            },
            'nagios_escalation': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_service_check_command_parameter': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_service_contact_group_member': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_service_contact_member': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_service_custom_object_var': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_service_group_member': {
                'columns': ['service'],
                'ids_updated': set(),
            },
            'nagios_service_template_inheritance': {
                'columns': ['source_service'],
                'ids_updated': set(),
            },
        },
    },
}

lilac_service_table = {
    'table': 'nagios_service',
    'reference_tables': {
        'nagios_service_template_inheritance': {
            'column': 'source_service',
            'ids_updated': set(),
        },
        'nagios_dependency': {
            'column': 'service',
            'ids_updated': set(),
        },
        'nagios_dependency_target': {
            'column': 'target_service',
            'ids_updated': set(),
        },
        'nagios_escalation': {
            'column': 'service',
            'ids_updated': set(),
        },
        'nagios_service_check_command_parameter': {
            'column': 'service',
            'ids_updated': set(),
        },
        'nagios_service_contact_group_member': {
            'column': 'service',
            'ids_updated': set(),
        },
        'nagios_service_contact_member': {
            'column': 'service',
            'ids_updated': set(),
        },
        'nagios_service_custom_object_var': {
            'column': 'service',
            'ids_updated': set(),
        },
        'nagios_service_group_member': {
            'column': 'service',
            'ids_updated': set(),
        },
    },
}

side_tables = (
    'nagios_service_check_command_parameter',
    'nagios_contact_group_member',
    'nagios_contact_notification_command',
    'nagios_host_parent',
    'nagios_host_template_inheritance',
    'nagios_hostgroup_membership',
    'nagios_service_template_inheritance',
)

core_max_ids = {
    'nagios_command': 0,
    'nagios_contact': 0,
    'nagios_contact_group': 0,
    'nagios_host': 0,
    'nagios_host_template': 0,
    'nagios_hostgroup': 0,
    'nagios_service': 0,
    'nagios_service_group': 0,
    'nagios_service_template': 0,
    'nagios_timeperiod': 0
}


class sqlinfo:
    def __init__(self, host: str, user: str, pwd: str, db: str, port: int = 3306):
        self.info = {
            'host':   host,
            'user':   user,
            'passwd': pwd,
            'db':     db,
            'port':   port
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


def get_max_index(tablename: str, set_newid: bool = False) -> int:
    cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
    cur.execute("SELECT MAX(`id`) FROM {}".format(tablename))
    maxid = cur.fetchone()[0]
    cur.close()
    if set_newid:
        if maxid is None or maxid < min_instance_id:
            maxid = min_instance_id
        else:
            maxid = maxid + 1
    return maxid


def fix_table_index(tablename: str, core_max_id: int, tabledict: dict) -> list:
    """
    1. enumate record ids that are *not* core ids
    2. for each record found in 1.:
        a. update record id to next higher ID > min_instance_id
        b. maintain a list of tuples : (old_id, new_id)
        c. for each reference table, fix for each impacted column the old id by the new one
    """
    list_ids = []
    cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
    stat = "SELECT id from `{}` WHERE `id` > {} AND `id` < {}".format(tablename, core_max_id, min_instance_id)
    logger.info(stat)
    cur.execute(stat)
    ids = tuple(i[0] for i in cur.fetchall())
    cur.close()

    for tid in ids:
        mid = get_max_index(tablename, True)
        cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
        stat = "UPDATE {} SET `id`={} WHERE `id`={}".format(tablename, mid, tid)
        logger.info(stat)
        cur.execute(stat)
        cur.close()
        list_ids.append((tid, mid))

        for table in tabledict['reference_tables'].keys():
            for col in tabledict['reference_tables'][table]['columns']:
                cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
                stat = "SELECT `id` FROM {table} WHERE `{col}`={oid}".format(
                    table=table,
                    col=col,
                    oid=tid)
                cur.execute(stat)
                res = cur.fetchall()
                cur.close()
                if isinstance(res, int) and res == 0:
                    continue
                updateids = set(i[0] for i in res)
                tabledict['reference_tables'][table]['ids_updated'].update(updateids)

                for t2id in updateids:
                    cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
                    stat = "UPDATE {table} SET `{col}`={nid} WHERE `id`={otid}".format(
                        table=table,
                        otid=t2id,
                        col=col,
                        nid=mid
                    )
                    logger.info(stat)
                    cur.execute(stat)
                cur.close()
    return list_ids


def fix_service_table(tablename: str, tabledict: dict, ids: set):
    touchedid = []
    for tid in ids:
        newid = get_max_index(tablename, True)
        cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
        stat = "UPDATE {table} SET `id`={nid} WHERE `id`={oid}".format(
            table=tablename,
            nid=newid,
            oid=tid
        )
        logger.info(stat)
        cur.execute(stat)
        cur.close()
        touchedid.append((tid, newid))

        for table in tabledict.keys():
            cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
            stat = "SELECT `id` FROM {table} WHERE `{col}`={value}".format(
                table=table,
                col=tabledict[table]['column'],
                value=tid)
            logger.info(stat)
            cur.execute(stat)
            res = cur.fetchall()
            cur.close()
            if isinstance(res, int) and res == 0:
                continue
            updateids = set(i[0] for i in res)
            tabledict[table]['ids_updated'].update(updateids)
            for updateid in updateids:
                if updateid < min_instance_id:
                    t2nid = get_max_index(table, True)
                else:
                    t2nid = updateid
                cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
                stat = "UPDATE {table} SET `id`={nid}, `{col}`={value} WHERE `id`={oid}".format(
                    table=table,
                    nid=t2nid,
                    oid=updateid,
                    col=tabledict[table]['column'],
                    value=newid
                )
                logger.info(stat)
                cur.execute(stat)
                cur.close()


def fix_side_table(tablename: str, ids: set):
    for oldid in ids:
        if oldid < min_instance_id:
            newid = get_max_index(tablename, True)
            cur = sql.connect().cursor(MySQLdb.cursors.Cursor)
            stat = "UPDATE {table} SET `id`={nid} WHERE `id`={oid}".format(
                table=tablename,
                nid=newid,
                oid=oldid
            )
            logger.info('fix_side_table: ' + stat)
            cur.execute(stat)
            cur.close()
        else:
            logger.info("discard update table {}, id {}".format(tablename, oldid))


def index_ids(ids_translation: list, from_old_id: bool = True) -> dict:
    retdict = {}
    for old, new in ids_translation:
        if from_old_id:
            retdict[old] = new
        else:
            retdict[new] = old
    return retdict


def fix_main_commands(ids_translation: dict):
    cur = sql.connect().cursor(MySQLdb.cursors.DictCursor)
    stat = """
        SELECT
            global_host_event_handler,
            global_service_event_handler,
            ocsp_command,
            ochp_command,
            host_perfdata_command,
            service_perfdata_command,
            host_perfdata_file_processing_command,
            service_perfdata_file_processing_command
        FROM nagios_main_configuration WHERE `id` = 1
    """
    logger.info(stat)
    cur.execute(stat)
    cmds = cur.fetchone()

    update = {}
    for col in cmds.keys():
        if cmds[col] is not None and isinstance(cmds[col], int):
            if cmds[col] in ids_translation.keys():
                update[col] = ids_translation[cmds[col]]

    if len(update) > 0:
        stat = "UPDATE nagios_main_configuration SET {} WHERE `id` = 1".format(
            ",".join(["`{}`={}".format(k, update[k]) for k in update.keys()])
        )
        logger.info(stat)
        cur.execute(stat)
    cur.close()


def show_table_ids(tablename: str):
    desc = None
    cur = sql.connect().cursor(MySQLdb.cursors.DictCursor)
    cur.execute("DESCRIBE {}".format(tablename))
    fields = [a['Field'].lower() for a in cur.fetchall()]
    if 'name' in fields:
        desc = 'name'
    elif 'description' in fields:
        desc = 'description'

    print("\n\n-=- Index content for table {} -=-\n".format(tablename))
    stat = "SELECT `id`, `{}` FROM {} WHERE id < {} ORDER BY id".format(desc, tablename, min_instance_id)
    cur.execute(stat)
    rows = cur.fetchall()
    for row in rows:
        print(" {0:5} - {1}".format(row['id'], row[desc]))


def user_input_max_id() -> int:
    while True:
        try:
            usrin = int(input("\nPlease enter max core record ID :"))
            if usrin < 1 or usrin >= min_instance_id:
                print("ID out of range (min: 1, max: {})".format(min_instance_id))
                continue
            else:
                return usrin
        except ValueError:
            print('ID value must be an integer')
            continue


def main(yamlfile):
    with open(yamlfile) as file:
        yml = yaml.load(file)
        if yml is not None and 'core_max_id' in yml.keys() and isinstance(yml['core_max_id'], dict):
            for table in yml['core_max_id'].keys():
                if (
                    table in core_max_ids.keys()
                    and isinstance(yml['core_max_id'][table], int)
                    and yml['core_max_id'][table] > 0
                ):
                    logger.info("load core max id value '{}' for table {} from {}".format(
                        core_max_ids[table],
                        table,
                        yamlfile
                    ))
                    core_max_ids[table] = yml['core_max_id'][table]
    logger.info("core max IDs: {}".format(core_max_ids))

    # reindex target tables
    for table in lilac_tables_id.keys():
        core_max_ids[table]
        if core_max_ids[table] == 0:
            show_table_ids(table)
            core_max_ids[table] = user_input_max_id()
        lilac_tables_id[table]['indexes'] = fix_table_index(
            table,
            core_max_ids[table],
            lilac_tables_id[table]
        )
        if table == 'nagios_command':
            fix_main_commands(index_ids(lilac_tables_id[table]['indexes']))

    with open(yamlfile, 'w') as file:
        yml = yaml.dump({'core_max_id': core_max_ids}, file, default_flow_style=False)

    # now compute updated tables
    stables = {}
    for mtable in lilac_tables_id.keys():
        for stable in lilac_tables_id[mtable]['reference_tables'].keys():
            if len(lilac_tables_id[mtable]['reference_tables'][stable]['ids_updated']) == 0:
                continue
            if stable in stables.keys():
                stables[stable].update(lilac_tables_id[mtable]['reference_tables'][stable]['ids_updated'])
            else:
                stables[stable] = lilac_tables_id[mtable]['reference_tables'][stable]['ids_updated']

    if lilac_service_table['table'] in stables.keys():
        fix_service_table(
            lilac_service_table['table'],
            lilac_service_table['reference_tables'],
            stables[lilac_service_table['table']]
        )
    for table in side_tables:
        if table in stables.keys():
            fix_side_table(table, sorted(stables[table]))


sql = None
min_instance_id = 10000

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=" version {} - copyright {}".format(__version__, __copyright__),
    )
    parser.add_argument('-H', '--host', type=str, help='SQL hostname', default='localhost')
    parser.add_argument('-P', '--port', type=int, help='SQL listening port', default=3306)
    parser.add_argument('-u', '--user', type=str, help='SQL user', default='root')
    parser.add_argument('-p', '--password', type=str, help='SQL password', default=None)
    parser.add_argument('-s', '--db', type=str, help='lilac database', default='lilac')
    parser.add_argument(
        '-c', '--config', type=str, help='lilac_repair instance configuration (yaml)',
        default='lilac_repair.yaml'
    )
    parser.add_argument('-l', '--log', type=str, help='logfile location', default='lilac_repair.log')
    args = parser.parse_args()

    logger.basicConfig(filename=args.log, level='INFO')

    sql = sqlinfo(host=args.host, port=args.port, user=args.user, pwd=args.password, db=args.db)
    if not os.path.exists(args.config) or not os.path.isfile(args.config):
        with open(args.config, 'w'):
            pass
    main(args.config)
