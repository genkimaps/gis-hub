# import modules
import sys
import json
from string import Template
import io
import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import dateutil.parser
from datetime import datetime, date
# Use sys.append to append path to where ckanapi module lives.
# https://stackoverflow.com/questions/22955684/how-to-import-py-file-from-another-directory
sys.path.append('/home/dfo/hub-geo-api')
import ckanapi as ck
import settings


logger = settings.setup_logger()

#
# # logger setup function
# def logger_setup(output_directory):
#     logging.basicConfig(
#         filename=os.path.join(output_directory, "new-updated-datasets.log"),
#         format="| %(levelname)-7s| %(asctime)s | %(message)s",
#         level="INFO",  # numeric value: 20
#     )
#     logger = logging.getLogger('new_datasets')
#     return logger
#
#
# logger = logger_setup("logs")
#
#
# def read_templates(body_file, subject_file):
#     """
#     Open email message and subject templates and return Template objects made from their contents.
#     """
#     try:
#         with io.open(body_file, "r", encoding="utf-8") as msg_template:
#             msg_template_content = msg_template.read()
#         with io.open(subject_file, "r", encoding="utf-8") as subject_template:
#             subject_template_content = subject_template.read()
#         return Template(msg_template_content), Template(subject_template_content)
#     except Exception as e:
#         print(e.args)
#
#
# def setup_smtp(dataset_records, message_template, subject_template):
#     """
#     Establishes connection with MailGun server. Loops through data in list of dictionaries from
#     SQL database query. For each record, send an email to the data maintainer with details about the
#     dataset they are responsible for.
#     """
#     try:
#         if dataset_records is None:
#             # If dataset records is None, exit program.
#             sys.exit()
#         else:
#             # Set up the SMTP server with mailgun settings.
#             server = smtplib.SMTP(host=os.environ.get("CKAN_SMTP_SERVER"))
#
#             # Start connection to server and login with credentials.
#             server.starttls()
#             server.login(os.environ.get("CKAN_SMTP_USER"), os.environ.get("CKAN_SMTP_PASSWORD"))
#
#             # For each record (dataset) in csv, send message.
#             for record in dataset_records:
#                 msg = MIMEMultipart()
#
#                 # Add in the actual person name to the message template.
#                 message = message_template.substitute(PERSON_NAME=record["maintainer_name"],
#                                                       DATASET_NAME=record["title"],
#                                                       DAYS_SINCE_MODIFIED_MAX=max(record["days_since_modified"]),
#                                                       DATA_URL=record["url"])
#
#                 # Add in custom subject with dataset name.
#                 subject = subject_template.substitute(DATASET_NAME=record["title"])
#
#                 # Setup the parameters of the message.
#                 msg["From"] = os.environ.get("CKAN_SMTP_MAIL_FROM")
#                 msg["To"] = record["maintainer_email"]
#                 msg["Subject"] = subject
#
#                 # Add the message from template to body of email.
#                 msg.attach(MIMEText(message, "plain"))
#
#                 # Send the message via the server set up earlier.
#                 server.sendmail(msg["From"], msg["To"], msg.as_string())
#
#             server.quit()
#     except Exception as e:
#         print(e.args, e.message)
#     del msg
#
#
# def get_metadata_created(dataset):
#     """
#     Get dates for metadata created.
#     :return:
#     """
#     iso_date = dataset.get('metadata_created')
#
#
#


def process(group_name):
    logger.info("Getting list of datasets in {}".format(group_name))
    datasets_group = ck.list_datasets_in_group(group_name)
    return datasets_group


def main():
    # CLI arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("group_id", type=str, help="Group name or ID to query and retrieve datasets.")
    args = parser.parse_args()

    group_datasets = process(args.group_id)
    with open("/tmp/new-test.json", "w") as outfile:
        json.dump(group_datasets[0], outfile)
    # Load template email body and subject.
    # email_template_obj = read_templates("templates/emails/new_updated_dataset.txt",
    #                                     "templates/emails/new_updated_dataset_subject.txt")
    # # Use data from maintainer_list and email_template_obj to send email to list of users.
    # setup_smtp(maintainer_list, email_template_obj[0], email_template_obj[1])


if __name__ == "__main__":
    main()
