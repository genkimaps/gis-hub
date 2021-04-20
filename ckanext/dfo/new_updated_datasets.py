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


# logger setup function
def logger_setup(output_directory):
    logging.basicConfig(
        filename=os.path.join(output_directory, "spill-response-emails.log"),
        format="| %(levelname)-7s| %(asctime)s | %(message)s",
        level="INFO",  # numeric value: 20
    )
    logger = logging.getLogger('spill_response')
    return logger


# instantiate logger
logger = logger_setup("logs")


def read_templates(body_file, subject_file):
    """
    Open email message and subject templates and return Template objects made from their contents.
    """
    try:
        logger.info("Opening email template files...")
        with io.open(body_file, "r", encoding="utf-8") as msg_template:
            msg_template_content = msg_template.read()
        with io.open(subject_file, "r", encoding="utf-8") as subject_template:
            subject_template_content = subject_template.read()
        return Template(msg_template_content), Template(subject_template_content)
    except Exception as e:
        logger.error("Error opening email templates...")
        logger.error(e.args)


def send_email(metadata_dict, message_template, subject_template):
    """
    Send email to users if a new dataset is published.
    """
    try:
        if metadata_dict is None:
            # If dataset records is None, exit program.
            logger.warning("Metadata dictionary is empty, program is exiting.")
            sys.exit()
        else:
            # Set up the SMTP server with mailgun settings.
            logger.info("Setting up email connection parameters...")
            server = smtplib.SMTP(host=os.environ.get("CKAN_SMTP_SERVER"))

            # Start connection to server and login with credentials.
            server.starttls()
            server.login(os.environ.get("CKAN_SMTP_USER"), os.environ.get("CKAN_SMTP_PASSWORD"))

            msg = MIMEMultipart()

            # Add in the actual person name to the message template.
            logger.info("Loading information into email templates...")
            message = message_template.substitute(DATASET_NAME=metadata_dict.get("ds_title"),
                                                  DATA_URL=metadata_dict.get("ds_url"),
                                                  SUMMARY=metadata_dict.get("ds_summary"),
                                                  GROUP_NAME=metadata_dict.get("group_title"))

            # Add in custom subject with dataset name.
            subject = subject_template.substitute(DATASET_NAME=metadata_dict.get("ds_title"),
                                                  GROUP_NAME=metadata_dict.get("group_title"))

            # Setup the parameters of the message.
            msg["From"] = os.environ.get("CKAN_SMTP_MAIL_FROM")
            msg["To"] = ", ".join(metadata_dict.get("group_emails"))
            msg["Subject"] = subject

            # Add the message from template to body of email.
            msg.attach(MIMEText(message, "plain"))

            # Send the message via the server set up earlier.
            logger.info("Sending email...")
            server.sendmail(msg["From"], metadata_dict.get("group_emails"), msg.as_string())

            server.quit()
    except Exception as e:
        logger.error("Error loading email settings and sending email...")
        logger.error(e.args, e.message)
    del msg


def get_metadata(dataset, group_name):
    """
    Get all the metadata required to fill template into a dictionary.
    """
    try:
        iso_date = dateutil.parser.parse(dataset.get("metadata_created"))
        # https://docs.ckan.org/en/ckan-2.7.3/maintaining/configuration.html#ckan-display-timezone
        # time comparisons should be UTC time as that is the default
        today = datetime.utcnow().date()
        logger.info("Checking publication dates of datasets for new records...")
        if iso_date.date() == today:
            logger.info("New dataset found...")
            # get group metadata
            logger.info("Getting all the metadata from dataset and users to send email...")
            group_data = ck.get_group(group_name)
            # have to get the user IDs in order to filter user list and get emails
            group_user_ids = [user.get("id") for user in group_data.get("users")]
            # get list of all users information on gis hub
            all_users = ck.get_user_info()
            # now filter the list of all users to get the ones part of the group
            group_user_emails = [u.get("email") for u in all_users if u.get("id") in group_user_ids]
            # get metadata for email
            template_meta = {"ds_url": "https://www.gis-hub.ca/dataset/" + dataset.get("name"),
                             "ds_summary": dataset.get("notes"),
                             "ds_title": dataset.get("title"),
                             "group_title": group_data.get("title"),
                             "group_url": "https://www.gis-hub.ca/group/" + group_name,
                             "group_emails": group_user_emails}
            logger.info("Metadata dictionary prepared for email template...")
            return template_meta
        else:
            logger.info("Dataset was published {}...".format(iso_date))
    except Exception as e:
        logger.error("Error preparing metadata into a dictionary...")
        logger.error(e.args, e.message)


def process(group_name):
    logger.info("Getting list of datasets in {}".format(group_name))
    datasets_group = ck.list_datasets_in_group(group_name)
    dataset_dicts = [get_metadata(dataset, group_name) for dataset in datasets_group]

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


if __name__ == "__main__":
    main()
