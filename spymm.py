#!/usr/bin/env python3
#
#   SPYMM
#   Copyright (C) 2018  Tim Vaughan
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import json, argparse, sys, csv

import smtplib, email
from email.message import EmailMessage

def constructMessage(record, mailout_config):
    msg = EmailMessage()
    msg['Subject'] = mailout_config['subject'].format(**record)
    msg['From'] = mailout_config['from'].format(**record)
    msg['To'] = mailout_config['to'].format(**record)

    with open(mailout_config['template'].format(**record), "r") as template_file:
        msg.set_content(template_file.read().format(**record))

    return(msg)
    

def testRecord(record, mailout_config):
    if 'rules' in mailout_config:
        for rule in mailout_config['rules']:
            if not eval(rule.format(**record)):
                return False

    return True


def getConfig():

    parser = argparse.ArgumentParser(description="Command-line mail merge.",
                                     epilog="""
Refer to documentation for format of configuration file.
""")

    parser.add_argument("config_file", metavar="configuration_file", type=argparse.FileType("r"),
                        help="Configuration file for mailout.")

    parser.add_argument("-d","--dry_run", action="store_true",
                        help="Perform dry run: connect to server, but don't actually send any mail.")
    parser.add_argument("-v","--verbose", action="store_true",
                        help="Print detailed output, including full contents of each message.")

    args = parser.parse_args()

    config = json.load(args.config_file)
    config['dry_run'] = args.dry_run
    config['verbose'] = args.verbose

    return config


def doMailout(server, mailout_config, verbose):

    with open(mailout_config['recipients'], "r") as recipients_file:
        reader = csv.DictReader(recipients_file)
    
        msg_count = 0
        
        for record in reader:
            if testRecord(record, mailout_config):
                msg = constructMessage(record, mailout_config)
                msg_count += 1

                if verbose:
                    print("*** Message {}:".format(msg_count))
                    print(msg)
                
                if server != None:
                    server.send_message(msg)

                    if verbose:
                        print("*** Message {} successfully sent to {}".format(
                            msg_count, msg['To']))
                              
        print("*** {} messages{}in total".format(msg_count, " " if dry_run else " sent "))
            

if __name__ == '__main__':

    config = getConfig()
    dry_run = config['dry_run']
    verbose = config['verbose']

    try:
        if dry_run:
            server = None
        else:
            server = smtplib.SMTP(host=config['server']['host'],
                                  port=config['server']['port'])

            if 'use_tls' in config['server'] and config['server']['use_tls']:
                server.starttls()

            if 'login' in config['server']:
                username = config['server']['login']['username']
                password = config['server']['login']['password']
                server.login(username, password)

        for mailout_config in config['mailouts']:
            doMailout(server, mailout_config, verbose)

    finally:
        if server != None:
            server.quit()
