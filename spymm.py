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

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
from os.path import basename

def createAttachment(filename):
    with open(filename, "rb") as fh:
        part = MIMEApplication(fh.read(), Name=basename(filename))
    part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(filename))

    return(part)

def constructMessage(record, mailout_config):
    msg = MIMEMultipart()
    msg['Subject'] = mailout_config['subject'].format(**record)
    msg['From'] = mailout_config['from'].format(**record)

    if isinstance(mailout_config['to'], list):
        msg['To'] = ", ".join(map(lambda s: s.format(**record),
                                  filter(lambda s: len(s)>0, mailout_config['to'])))
    else:
        msg['To'] = mailout_config['to'].format(**record)

    if 'cc' in mailout_config:
        if isinstance(mailout_config['cc'], list):
            msg['Cc'] = ", ".join(map(lambda s: s.format(**record),
                                      filter(lambda s: len(s)>0, mailout_config['cc'])))
        else:
            msg['Cc'] = mailout_config['cc'].format(**record)

    msg['Date'] = formatdate(localtime=True)
                
    with open(mailout_config['template'].format(**record), "r") as template_file:
        msg.attach(MIMEText(template_file.read().format(**record)))

    if 'attach' in mailout_config:
        if isinstance(mailout_config['attach'], list):
            for attach_name in mailout_config['attach']:
                msg.attach(createAttachment(attach_name.format(**record)))
        else:
            msg.attach(createAttachment(mailout_config['attach'].format(**record)))

    return(msg)
    

def testRecord(record, mailout_config):
    try:
        if 'rules' in mailout_config:
            for rule in mailout_config['rules']:
                if not eval(rule.format(**record)):
                    return False

        return True

    except Exception as err:
        print("Error evaluating rules: {}".format(err))
        sys.exit(1)


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

    try:
        config = json.load(args.config_file)
        config['dry_run'] = args.dry_run
        config['verbose'] = args.verbose

    except Exception as err:
        print("Error reading config file: {}".format(err))
        sys.exit(1)

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

    exit_status = 0

    server = None

    try:
        if not dry_run:
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

    except KeyError as err:
        print("Undefined configuration item: {}".format(err))
        exit_status = 1

    except Exception as err:
        print("Error during mailout: {}".format(err))
        exit_status = 1

    finally:
        if server != None:
            server.quit()

    sys.exit(exit_status)
