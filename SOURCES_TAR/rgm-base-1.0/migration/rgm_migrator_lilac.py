#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eric Belhomme'
__copyright__ = '2019, SCC'
__credits__ = ['Eric Belhomme']
__license__ = 'GPLv2'
__version__ = '0.1'

import sys
# import re
import argparse
import csv
import requests
import json
import pprint
import MySQLdb

pp = pprint.PrettyPrinter()
requests.packages.urllib3.disable_warnings()


def list_available_commands(session, server):
    r = session.post("https://{server}/rgmapi/getCommand".format(server=server))
    if r.status_code == 200:
        return [{i['Name']: i['Line']} for i in r.json()['result']]
    else:
        return None


def list_available_hosts(session, server):
    r = session.post("https://{server}/rgmapi/getHost".format(server=server))
    if r.status_code == 200:
        return [i['Name'] for i in r.json()['result']]
    else:
        return None


def list_available_services(session, server, hostname):
    r = session.post(
        "https://{server}/rgmapi/getServicesByHost".format(server=server),
        data=json.dumps({'hostName': hostname})
    )
    if r.status_code == 200:
        return [i['Description'] for i in r.json()['result']]
    else:
        return None


def list_available_service_templates(session, server):
    r = session.post(
        "https://{server}/rgmapi/getServiceTemplate".format(server=server),
    )
    if r.status_code == 200:
        return [i['Name'] for i in r.json()['result']]
    else:
        return None


def connect(server, user, passwd):
    session = requests.session()
    session.verify = False
    r = session.get(
        "https://{server}/rgmapi/getAuthToken?&username={user}&password={passwd}".format(
            server=server,
            user=user,
            passwd=passwd
        )
    )
    if r.status_code == 200:
        session.headers = {'token': r.json()['RGMAPI_TOKEN']}
        print('RGMAPI connection OK')
        print(session.headers)
        return session
    else:
        return None


def get_csv_from_database(cfglilac, csvfile):
    sql_params = {
        'host':   cfglilac['hostname'],
        'user':   cfglilac['user'],
        'passwd': cfglilac['password'],
        'db':     cfglilac['database'],
    }
    try:
        conn = MySQLdb.connect(**sql_params)
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT
                distinct (hst.`name`) AS `host`,
                srv.description AS service,
                srv.id AS srvid,
                srvtmpl.`name` AS template,
                cmd.name AS command,
                prm.parameter AS param
            FROM nagios_service AS srv
            INNER JOIN nagios_host AS hst ON srv.`host` = hst.`id`
            INNER JOIN nagios_command AS cmd ON srv.check_command = cmd.id
            INNER JOIN nagios_service_template_inheritance AS srvinh ON srv.id = srvinh.source_service
            INNER JOIN nagios_service_template AS srvtmpl ON srvinh.target_template = srvtmpl.id
            INNER JOIN nagios_service_check_command_parameter AS prm ON srv.id = prm.service
            WHERE srv.host_template IS NULL
            ORDER BY
                hst.name,
                srv.description,
                srvinh.order,
                prm.id;
            """)
        with open(csvfile, 'w', newline='') as fcsv:

            fields = [
                'host',
                'service',
                'srvid',
                'template',
                'command',
                'param'
            ]
            csvwriter = csv.DictWriter(fcsv, fieldnames=fields, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            for row in cur.fetchall():
                csvwriter.writerow(row)
    except Exception as e:
        print("Failed to connect to SQL. Error {}".format(e))
        sys.exit(1)


def inject_csv_to_rgmapi(session, server, csvfile, check_source):

    # generating data structure from CSV file
    services = {}
    with open(csvfile, newline='') as fcsv:
        fields = [
            'host',
            'service',
            'srvid',
            'template',
            'command',
            'param'
        ]
        csvreader = csv.DictReader(fcsv, fieldnames=fields, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        for row in csvreader:
            if row['srvid'] in services:
                services[row['srvid']]['service']['parameters'].append(row['param'])
            else:
                services[row['srvid']] = {
                    'hostName': row['host'],
                    'service': {
                        'name': row['service'],
                        'inheritance': row['template'],
                        'command': row['command'],
                        'parameters': [row['param'], ]
                    }
                }
    services = sorted([services[i] for i in services.keys()], key=lambda j: j['hostName'])

    # sending  RGM API calls
    if len(services) > 0:
        avail_cmds = list_available_commands(session, config['rgmapi']['hostname'])
        avail_hosts = list_available_hosts(session, config['rgmapi']['hostname'])
        avail_tmplt = list_available_service_templates(session, config['rgmapi']['hostname'])

        for srv in services:
            if not srv['service']['command'] in [list(i)[0] for i in avail_cmds]:
                print("aïe aïe aïe !!! commande {} pas trouvée :(".format(srv['service']['command']))
            elif not srv['service']['inheritance'] in avail_tmplt:
                print("outch ! le service template {} n'existe pas !".format(srv['service']['inheritance']))
            else:
                if srv['hostName'] in avail_hosts:
                    if srv['service']['name'] in list_available_services(
                        session, config['rgmapi']['hostname'], srv['hostName']
                    ):
                        print("le service {} existe déjà pour le host {}".format(
                            srv['service']['name'], srv['hostName']
                        ))
                    else:
                        #session = requests.session()
                        r = session.post(
                            "https://{server}/rgmapi/createServiceToHost".format(server=server),
                            data=json.dumps(srv)
                        )
                        if r.status_code == 200:
                            print("youpi, service {} inséré avec succes sur le host {}".format(
                                srv['service']['name'], srv['hostName']
                            ))
                        else:
                            print("erreur lors de l'insertion du service {}/{}".format(
                                srv['hostName'], srv['service']['name']
                            ))
                        pp.pprint(r.json())
                else:
                    print("Le host {} n'existe pas dans la conf actuelle de RGM. On l'ignore".format(srv['hostName']))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="""
Simple script to extract direct-attached services to hosts, then re-inject them on a new RGM instance.
It work by :
    1. importing information from EON/RGM Lilac database to a CSV file
    2. exporting the content of the extracted CSV file using RGMAPI.

Important: the script doesn't create neither the hosts, nor the Nagios commands. So they must exist
prior export (or the CSV file have to be adapted to fit on target hosts/commands)

At first, you must create a JSON configuration file. Invoking the script without
any args will create a default JSON for you.

You can then edit and customize it :
- to connect to MariaDB source lilac database
- to access and login on target RGMAPI REST API

Then, invoke the script a first time with '-m get-csv'

This will produce a CSV file "host;service desc;service id;command:arg"
You can adapt the CSV to match hosts and commands on target.

Finally, invode the script a second time with '-m export-services'
            """,
        epilog=" version {} - copyright {}".format(__version__, __copyright__),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-c', '--config', type=str, help='JSON configuration file', default='rgm_migrator_lilac.json')
    parser.add_argument('-f', '--csvfile', type=str, help='CSV out file', default='rgm_migrator_lilac.csv')
    parser.add_argument('-v', '--verify', type=bool, help='check Nagios command existence', default=True)
    parser.add_argument('-m', '--mode', help='mode', type=lambda s: s.lower(), choices=['import-services', 'export-services'])

    args = parser.parse_args()

    config = {}
    outlist = []

    try:
        with open(args.config) as cfg:
            config = json.load(cfg)
    except IOError:
        try:
            with open(args.config, 'w') as cfg:
                cfg.writelines(json.dumps({
                    'rgmapi': {
                        'hostname': 'localhost',
                        'user': 'admin',
                        'password': 'admin'
                    },
                    'lilac': {
                        'hostname': 'localhost',
                        'database': 'lilac',
                        'user': 'root',
                        'password': 'password'
                    },
                    'check_source': 'True'
                }, sort_keys=True, indent=4))
        except IOError as e:
            print("Failed to read or write cfg file {}. Msg: {}".format(args.config, e.errno))
            sys.exit(1)

    if args.mode == 'import-services':
        get_csv_from_database(config['lilac'], args.csvfile)
    elif args.mode == 'export-services':
        session = connect(config['rgmapi']['hostname'], config['rgmapi']['user'], config['rgmapi']['password'])
        if session:
            inject_csv_to_rgmapi(session, config['rgmapi']['hostname'], args.csvfile, config['check_source'])
