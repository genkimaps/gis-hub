# import modules
import sys
from string import Template
import io
import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import dateutil.parser
import json

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
        if metadata_dict is not None:
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
                                                  GROUP_NAME=metadata_dict.get("group_title"),
                                                  GROUP_URL=metadata_dict.get("group_url"),
                                                  STATE=metadata_dict.get("state"),
                                                  CHANGE_DATE=metadata_dict.get("change_date"),
                                                  CHANGE_DESC=metadata_dict.get("change_desc"))

            # Add in custom subject with dataset name.
            subject = subject_template.substitute(DATASET_NAME=metadata_dict.get("ds_title"),
                                                  GROUP_NAME=metadata_dict.get("group_title"),
                                                  STATE=metadata_dict.get("state"))

            # Setup the parameters of the message.
            msg["From"] = os.environ.get("CKAN_SMTP_MAIL_FROM")
            msg["To"] = ", ".join(metadata_dict.get("group_emails"))
            msg["Subject"] = subject

            # Add the message from template to body of email.
            msg.attach(MIMEText(message, "plain"))

            # Send the message via the server set up earlier.
            logger.info("Sending email...")
            server.sendmail(msg["From"], metadata_dict.get("group_emails"), msg.as_string())

            del msg
            server.quit()
    except Exception as e:
        logger.error("Error loading email settings and sending email...")
        logger.error(e.args)


def latest_modified_date(dataset):
    try:
        # get resources from dataset
        resources = dataset.get("resources")
        if resources is not None:
            # get most recently modified date from list of resources
            max_date = max(
                [dateutil.parser.parse(res.get("last_modified")) for res in resources])
            return max_date
    except Exception as e:
        logger.error("Error getting last modified date...")
        logger.error(e.args)


def new_or_updated_group(dataset, group_name):
    """
    Get all the metadata required to fill template into a dictionary.
    """
    try:
        logger.info("Processing {}".format(dataset.get("name")))
        date_created = dateutil.parser.parse(dataset.get("metadata_created"))
        # https://docs.ckan.org/en/ckan-2.7.3/maintaining/configuration.html#ckan-display-timezone
        # todays datetime
        today = datetime.today()
        date_diff = today - date_created
        minutes_diff = date_diff.total_seconds() / 60
        # get date of most recent modified metadata from dataset
        res_last_modified_date = latest_modified_date(dataset)
        res_date_diff = today - res_last_modified_date
        res_minutes_diff = res_date_diff.total_seconds() / 60
        logger.info("Checking publication dates of datasets for new records...")
        # if dataset was created in the last hour, send email to members of org
        if minutes_diff < 60.0:
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
                             "group_emails": group_user_emails,
                             "state": "New",
                             "change_date": "",
                             "change_desc": ""
                             }
            logger.info("Metadata dictionary prepared for email template...")
            return template_meta
        # if resources were updated in the last hour, AND dataset was not created today, send email to members of org
        elif res_minutes_diff < 60.0 and date_created.date() != today.date():
            logger.info("Updated dataset found...")
            # get group metadata
            logger.info("Getting all the metadata from dataset and users to send email...")
            group_data = ck.get_group(group_name)
            # have to get the user IDs in order to filter user list and get emails
            group_user_ids = [user.get("id") for user in group_data.get("users")]
            # get list of all users information on gis hub
            all_users = ck.get_user_info()
            # now filter the list of all users to get the ones part of the group
            group_user_emails = [u.get("email") for u in all_users if u.get("id") in group_user_ids]
            # change history text
            change_string = dataset.get("change_history")
            change_list = json.loads(change_string)
            # get latest change history entry
            # leave as empty strings so if no change information, the text is blank when the template is filled.
            change_date = ""
            change_desc = ""
            if len(change_list) > 0:
                change_date = "Change Date: {}".format(change_list[-1].get('change_date'))
                change_desc = "Description: {}".format(change_list[-1].get('change_description'))

            # get metadata for email
            template_meta = {"ds_url": "https://www.gis-hub.ca/dataset/" + dataset.get("name"),
                             "ds_summary": dataset.get("notes"),
                             "ds_title": dataset.get("title"),
                             "group_title": group_data.get("title"),
                             "group_url": "https://www.gis-hub.ca/group/" + group_name,
                             "group_emails": group_user_emails,
                             "state": "Updated",
                             "change_date": change_date,
                             "change_desc": change_desc}

            logger.info("Metadata dictionary prepared for email template...")
            return template_meta
        else:
            logger.info("{} was published {}...".format(dataset.get("name"), date_created))
    except Exception as e:
        logger.error("Error preparing metadata into a dictionary...")
        logger.error(e.args)


def check_updated(dataset):
    try:
        logger.info("Processing {}".format(dataset.get("name")))
        date_created = dateutil.parser.parse(dataset.get("metadata_created"))
        # https://docs.ckan.org/en/ckan-2.7.3/maintaining/configuration.html#ckan-display-timezone
        # todays datetime
        today = datetime.today()
        date_diff = today - date_created
        minutes_diff = date_diff.total_seconds() / 60
        # get date of most recent modified metadata from dataset
        res_last_modified_date = latest_modified_date(dataset)
        res_date_diff = today - res_last_modified_date
        res_minutes_diff = res_date_diff.total_seconds() / 60
        logger.info("Checking publication dates of datasets for updated records...")

        if res_minutes_diff < 60.0 and date_created.date() != today.date():
            logger.info("Updated dataset found...")
            # get metadata
            logger.info("Getting all the metadata from dataset and users to send email...")
            followers_list = ck.get_dataset_followers(dataset.get("id"))
            # check if there are any followers
            if len(followers_list) > 0:
                # have to get the user IDs in order to filter user list and get emails
                follower_ids = [follower.get("id") for follower in followers_list]
                # get list of all users information on gis hub
                all_users = ck.get_user_info()
                # now filter the list of all users to get the ones part of the group
                user_emails = [u.get("email") for u in all_users if u.get("id") in follower_ids]
                # change history text
                change_string = dataset.get("change_history")
                change_list = json.loads(change_string)
                # get latest change history entry
                # leave as empty strings so if no change information, the text is blank when the template is filled.
                change_date = ""
                change_desc = ""
                if len(change_list) > 0:
                    change_date = "Change Date: {}".format(change_list[-1].get('change_date'))
                    change_desc = "Description: {}".format(change_list[-1].get('change_description'))

                # get metadata for email
                template_meta = {"ds_url": "https://www.gis-hub.ca/dataset/" + dataset.get("name"),
                                 "ds_summary": dataset.get("notes"),
                                 "ds_title": dataset.get("title"),
                                 "emails": user_emails,
                                 "state": "Updated",
                                 "change_date": change_date,
                                 "change_desc": change_desc}

                logger.info("Metadata dictionary prepared for email template...")
                return template_meta
            else:
                logger.info("{} has no followers...".format(dataset.get("name")))
        else:
            logger.info(
                "Most recently modified resource date from {} was: {}".format(dataset.get("name"), res_last_modified_date))
    except Exception as e:
        logger.error("Error preparing metadata into a dictionary...")
        logger.error(e.args)


def process_group(group_name):
    """
    Get datasets in group, check for newly published ones, send email to members of group if new data exists.
    """
    logger.info("Getting list of datasets in {}".format(group_name))
    datasets_group = ck.list_datasets_in_group(group_name)
    new_updated_group = [new_or_updated_group(dataset, group_name) for dataset in datasets_group]

    # Load template email body and subject.
    email_template_group = read_templates("templates/emails/new_updated_dataset_group.txt",
                                          "templates/emails/new_updated_dataset_group_subject.txt")
    for data_dict in new_updated_group:
        send_email(data_dict, email_template_group[0], email_template_group[1])

    return


def process_updated():
    """
    Check all datasets for updated, email followers if any
    """
    logger.info("Checking all datasets for updates and followers to email...")
    # get all datasets
    all_datasets = ck.list_datasets()
    updated_meta = [check_updated(dataset) for dataset in all_datasets]

    # Load template email body and subject.
    email_template_updated = read_templates("templates/emails/new_updated_dataset.txt",
                                            "templates/emails/new_updated_dataset_group.txt")

    for data_dict in updated_meta:
        send_email(data_dict, email_template_updated[0], email_template_updated[1])

    return


def main():
    # CLI arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("group_id", type=str, help="Group name or ID to query and retrieve datasets.")
    args = parser.parse_args()

    # check for updated datasets and followers
    process_updated()

    # check for new and/or updated datasets and send emails
    process_group(args.group_id)


if __name__ == "__main__":
    main()
