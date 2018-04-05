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

import argparse, sys

import smtplib, email
from email.message import EmailMessage

import csv, ast

def constructMessage(template, args):
    msg = EmailMessage()
    msg['Subject'] = args.subject
    msg['From'] = args.from_address
    msg['To'] = record[args.address]
    msg.set_content(template.format(**record))

    return(msg)
    
def testRecord(record, args):
    for rule in args.rules:
        if not eval(rule.format(**record)):
            return False

    return True

def parseArgs():

    parser = argparse.ArgumentParser(description="Command-line mail merge.",
                                     epilog="""
Any occurrence of {BLAH} in the message tempalte, where BLAH is the
header of a column in the recipients CSV file is replaced by value in
the corresponding recipient record.
""")

    parser.add_argument("smtp_hostname", type=str,
                        help="SMTP server hostname.")

    parser.add_argument("smtp_port", type=int,
                        help="SMTP server port.")

    parser.add_argument("from_address", type=str,
                        help="Message from address.")

    parser.add_argument("subject", type=str,
                        help="Message subject.")

    parser.add_argument("recipients_file", type=argparse.FileType("r"),
                        help="CSV file containing names and addresses.")

    parser.add_argument("template_file", type=argparse.FileType("r"),
                        help="File containing message template.")

    parser.add_argument("-a", "--address", type=str, default="Email",
                        help="Header of CSV column containing email addresses. (Default is \"Email\".)")
    parser.add_argument("-u","--username", type=str,
                        help="Username for SMTP server.")

    parser.add_argument("-p","--password", type=str,
                        help="Password for SMTP server.")

    parser.add_argument("-r","--rules", type=str, nargs='+', default=[],
                        help="Rules which records must satisfy for email to be sent.")

    parser.add_argument("-d","--dry_run", action='store_true',
                        help="Dry run: don't send anything.")

    return parser.parse_args()


if __name__ == '__main__':

    args = parseArgs()

    # Read in template
    template = args.template_file.read()

    # Initialize CSV reader
    reader = csv.DictReader(args.recipients_file)
    
    if args.address not in reader.fieldnames:
        print("Address header '{}' not found in CSV header.".format(args.address))
        sys.exit(1)


    if not args.dry_run:

        with smtplib.SMTP(host=args.smtp_hostname, port=args.smtp_port) as server:
            server.starttls()

            if args.username != None:
                server.login(args.username, args.password)

            for record in reader:
                if testRecord(record, args):
                    msg = constructMessage(template, args)
                    print("Sending to {} ... ".format(msg['To']), end='')
                    server.send_message(msg)
                    print("done.")
    else:

        for record in reader:
            if testRecord(record, args):
                msg = constructMessage(template, args)
                print("Message will be sent to {}".format(msg['To']))


