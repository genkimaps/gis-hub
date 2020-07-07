"""
Functions for parsing csv file and emailing users.
"""

# Import modules.
from csv import DictReader
from string import Template
import os
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def parse_csv(csv_file):
    """
    Parse csv of datasets with their associated data maintainers.
    Return a list of python dictionaries with information about dataset.
    """
    try:
        with open(csv_file, "r") as csv:
            dict_reader = DictReader(csv)
            list_of_dicts = list(dict_reader)
            return list_of_dicts
    except Exception as e:
        print(e.args)


def read_templates(body_file, subject_file):
    """
    Open email template and return Template object made from its contents.
    """
    try:
        with io.open(body_file, "r", encoding="utf-8") as msg_template:
            msg_template_content = msg_template.read()
        with io.open(subject_file, "r", encoding="utf-8") as subject_template:
            subject_template_content = subject_template.read()
        return Template(msg_template_content), Template(subject_template_content)
    except Exception as e:
        print(e.args)


def setup_smtp(dataset_records, message_template, subject_template):
    # Set up the SMTP server with mailgun settings.
    server = smtplib.SMTP(host=os.environ.get("CKAN_SMTP_SERVER"))

    # Start connection to server and login with credentials.
    server.starttls()
    server.login(os.environ.get("CKAN_SMTP_USER"), os.environ.get("CKAN_SMTP_PASSWORD"))

    # For each record (dataset) in csv, send message.
    for record in dataset_records:
        msg = MIMEMultipart()

        # Add in the actual person name to the message template.
        message = message_template.substitute(PERSON_NAME=record["maintainer_name"])

        # Add in custom subject with dataset name.
        subject = subject_template.substitute(DATASET_NAME=record["title"])

        # Setup the parameters of the message.
        msg["From"] = os.environ.get("CKAN_SMTP_MAIL_FROM")
        msg["To"] = record["maintainer_email"]
        msg["Subject"] = subject

        # Add the message from template to body of email.
        msg.attach(MIMEText(message, "plain"))

        # Send the message via the server set up earlier.
        server.sendmail(msg["From"], msg["To"], msg.as_string())

    server.quit()
    del msg
