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
from datetime import datetime
import dateutil.parser
# Use sys.append to append path to where ckanapi module lives.
# https://stackoverflow.com/questions/22955684/how-to-import-py-file-from-another-directory
sys.path.append("/home/dfo/hub-geo-api")
import ckanapi as ck
import settings

# set up logger
logger = settings.setup_logger()


def read_templates(body_file, subject_file):
    """
    Open email message and subject templates and return Template objects made from their contents.
    """
    try:
        with io.open(body_file, "r", encoding="utf-8") as msg_template:
            msg_template_content = msg_template.read()
        with io.open(subject_file, "r", encoding="utf-8") as subject_template:
            subject_template_content = subject_template.read()
        return Template(msg_template_content), Template(subject_template_content)
    except Exception as e:
        print(e.args)


def send_email(metadata_dict, message_template, subject_template):
    """
    TODO
    """
    try:
        if metadata_dict is None:
            # If dataset records is None, exit program.
            sys.exit()
        else:
            # Set up the SMTP server with mailgun settings.
            server = smtplib.SMTP(host=os.environ.get("CKAN_SMTP_SERVER"))

            # Start connection to server and login with credentials.
            server.starttls()
            server.login(os.environ.get("CKAN_SMTP_USER"), os.environ.get("CKAN_SMTP_PASSWORD"))

            msg = MIMEMultipart()

            # Add in the actual person name to the message template.
            message = message_template.substitute(DATASET_NAME=metadata_dict.get("title"),
                                                  DATA_URL=metadata_dict.get("url"),
                                                  SUMMARY=metadata_dict.get("summary"))

            # Add in custom subject with dataset name.
            subject = subject_template.substitute(DATASET_NAME=metadata_dict.get("title"))

            # Setup the parameters of the message.
            msg["From"] = os.environ.get("CKAN_SMTP_MAIL_FROM")
            msg["To"] = "Cole.Fields@dfo-mpo.gc.ca"
            msg["Subject"] = subject

            # Add the message from template to body of email.
            msg.attach(MIMEText(message, "plain"))

            # Send the message via the server set up earlier.
            server.sendmail(msg["From"], msg["To"], msg.as_string())

            server.quit()
    except Exception as e:
        print(e.args, e.message)
    del msg


def get_metadata(dataset):
    """
    Get dates for metadata created.
    :return:
    """
    iso_date = dateutil.parser.parse(dataset.get("metadata_created"))
    today = datetime.today().date()
    if iso_date.date() < today:
        # get metadata for email
        template_meta = {"url": "https://www.gis-hub.ca/dataset/" + dataset.get("name"),
                         "summary": dataset.get("notes"),
                         "title": dataset.get("title")}
        return template_meta


def process(group_name):
    logger.info("Getting list of datasets in {}".format(group_name))
    datasets_group = ck.list_datasets_in_group(group_name)
    dataset_dicts = [get_metadata(dataset) for dataset in datasets_group]
    # Load template email body and subject.
    email_template_obj = read_templates("templates/emails/new_updated_dataset.txt",
                                        "templates/emails/new_updated_dataset_subject.txt")
    for data_dict in dataset_dicts:
        send_email(data_dict, email_template_obj[0], email_template_obj[1])

    return


def main():
    # CLI arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("group_id", type=str, help="Group name or ID to query and retrieve datasets.")
    args = parser.parse_args()

    process(args.group_id)
    # Load template email body and subject.
    # email_template_obj = read_templates("templates/emails/new_updated_dataset.txt",
    #                                     "templates/emails/new_updated_dataset_subject.txt")
    # # Use data from maintainer_list and email_template_obj to send email to list of users.
    # setup_smtp(maintainer_list, email_template_obj[0], email_template_obj[1])


if __name__ == "__main__":
    main()
