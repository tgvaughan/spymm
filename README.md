SPYMM: Simple PYthon Mail-Merge
===============================

Ever needed to send a bunch of emails to a bunch of people, each personalized
in some way?  Do you hate standard office tools?  Would you like a basic tool
for doing this from the command line?

If so, SPYMM is for you!

To use SPYMM, simply create a CSV file containing the email addresses and other
recipient-specific data.  For example, the file `submissions.csv` below
contains email addresses and their acceptance status for made-up applicants to a
made-up conference:

```
    First Name, Last Name, Email,                Accepted
    Sue,        Smith,     ssmith@uni.edu,       Yes
    Jane,       Doe,       jdoe@institute.com,   No
    Wally,      Winthrop,  wally@winthrop.id.au, No
    Tony,       Robinson,  trob@company.org,     Yes
```

Note that the header row for the CSV file is mandatory.

Suppose we want to send an acceptance letter to everyone who has had their
submission accepted, and a rejection letter to everyone else.

To do this, create a file `acceptance.template` containing the acceptance
email, along the lines of:

```
    Dear {First Name},

    Your submission to Awesome Conference 2018 has been accepted!  We will
    soon be in touch with registration details.

    Yours,
    The organisers.
```

Note that the `{First Name}` will be replaced by the contents of the `First Name`
field in the record of the CSV file corresponding to the recipient.

Similarly, create a file `rejection.template` containing the rejection email template.

Then, you'll need to create a JSON configuration file. This file will
containing details of the SMTP server you intend to use, as well as information
about how to compose each email in one or more mailouts. For our example
we might use something like the following:

```json
{
    "server": {
        "host": "smtp.myuni.edu",
        "port": 25,
        "use_tls": true,
        "login": {
            "username": "myusername",
            "password": "mypassword"
        }
    },

    "mailouts": [
        {
            "from": "conference@myuni.edu",
            "to": "{Email}",
            "subject": "Awesome Conference 2018",
            "recipients": "submissions.csv",
            "template": "acceptance.template",
            "rules": ["'{Accepted}' == 'Yes'"]
        },
        {
            "from": "conference@myuni.edu",
            "to": "{Email}",
            "subject": "Awesome Conference 2018",
            "recipients": "submissions.csv",
            "template": "rejection.template",
            "rules": ["'{Accepted}' != 'Yes'"]
        }
    ]
}
```

Only include the "login" entry if authentication is required.

The "mailout" section of the file contains one or more distinct sets of emails
to send. The "from", "to" and "subject" elements are processed in the same way
as the template.  Hence in our case, `"to": "{Email}"` causes the destination
address to be defined by the "Email" field in the corresponding CSV file record.
We could also use this to customize the email subject and sender.

The "rules" section of a given mailout, if present, contains one or more
predicates that are processed according to the given CSV record and then evaluated.
Mails are sent only to records for which all of these rules evaluate to true.
In this example configuration, we have used such rules to distinguish between
recipients whose submission has been accepted (mailout 1) vs those whose application
has been rejected (mailout 2).

Note that the template file name defined in the configuration file is processed
according to the same way as the template itself.  This means that the example
task could have been accomplished using a single mailout section,
placing the templates in files named `accepted.Yes.template` and `accepted.No.template`
and using `"template": "accepted.{Accepted}.template"` in the configuration file.

To actually send the emails, all that is required now is to run the `spymm`
python script like so:
```
    $ python3 spymm.py config.json
```
where `config.json` is the name of the file containing the JSON configuration above. Note
that since this configuration does not specify the paths to the CSV and template files,
these also need to be in the current working directory.

WARNING: Given that this script can send mail to a large number of recpients,
it is prudent to test out any configuration first using the `--dry_run` option,
which quotes the number of messages that will be sent. Adding the `--verbose`
option additionally displays the complete messages which will be sent.  (This
option can also be enabled for the final mail-out for additional peace of mind.)

License
-------

This package is distributed under the terms of version 3 of the GNU General
Public License.  See the file COPYING, included in this archive, for more
details.
