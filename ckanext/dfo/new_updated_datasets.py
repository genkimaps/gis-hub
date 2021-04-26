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

log_dict = {"meta_new": "Preparing metadata from dataset and users to send email...",
            "meta_updated": "Preparing metadata from dataset resources and users to send email...",
            "meta_prepared": "Metadata dictionary prepared for email template...",
            "meta_dict_error": "Error preparing metadata into a dictionary...",
            "email_template_open": "Opening email template files...",
            "email_template_fill": "Loading information into email templates...",
            "email_template_error": "Error opening email templates...",
            "email_template_arg_error": "Invalid template argument...",
            "email_params": "Setting up email connection parameters...",
            "email_send": "Sending email...",
            "email_send_error": "Error sending email...",
            "last_modified_error": "Error getting last modified date...",
            "dataset_new_found": "New dataset found: {}...",
            "dataset_updated_found": "Updated dataset found: {}...",
            "no_followers": "{} has no followers...",
            "all_users_text": "Getting metadata and followers from {} send email..."
            }

smtp_settings = {"server": os.environ.get("CKAN_SMTP_SERVER"),
                 "user": os.environ.get("CKAN_SMTP_USER"),
                 "password": os.environ.get("CKAN_SMTP_PASSWORD"),
                 "mail_from": os.environ.get("CKAN_SMTP_MAIL_FROM")}


class MetaTemplateGroup:
    def __init__(self, dataset, group_data, group_name, group_user_emails, state, change_date, change_desc):
        self.ds_url = "https://www.gis-hub.ca/dataset/" + dataset.get("name")
        self.ds_summary = dataset.get("notes")
        self.ds_title = dataset.get("title")
        self.group_title = group_data.get("title")
        self.group_url = "https://www.gis-hub.ca/group/" + group_name
        self.emails = group_user_emails
        self.state = state
        self.change_date = change_date
        self.change_desc = change_desc


class MetaTemplate:
    def __init__(self, dataset, user_emails, state, change_date, change_desc):
        self.ds_url = "https://www.gis-hub.ca/dataset/" + dataset.get("name")
        self.ds_summary = dataset.get("notes")
        self.ds_title = dataset.get("title")
        self.emails = user_emails
        self.state = state
        self.change_date = change_date
        self.change_desc = change_desc


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
        logger.info(log_dict.get("email_template_open"))
        with io.open(body_file, "r", encoding="utf-8") as msg_template:
            msg_template_content = msg_template.read()
        with io.open(subject_file, "r", encoding="utf-8") as subject_template:
            subject_template_content = subject_template.read()
        return Template(msg_template_content), Template(subject_template_content)
    except Exception as e:
        logger.error(log_dict.get("email_template_error"))
        logger.error(e.args)


def send_email(metadata_dict, message_template, subject_template, template="group"):
    """
    Send email to users if a new dataset is published or updated.
    """
    try:
        if metadata_dict is not None:
            # Set up the SMTP server with mailgun settings.
            logger.info(log_dict.get("email_params"))
            server = smtplib.SMTP(host=smtp_settings.get("server"))

            # Start connection to server and login with credentials.
            server.starttls()
            server.login(smtp_settings.get("user"), smtp_settings.get("password"))

            msg = MIMEMultipart()

            # Add in the actual person name to the message template.
            logger.info(log_dict.get("email_template_fill"))
            if template == "group":
                message = message_template.substitute(DATASET_NAME=metadata_dict.ds_title,
                                                      DATA_URL=metadata_dict.ds_url,
                                                      SUMMARY=metadata_dict.ds_summary,
                                                      GROUP_NAME=metadata_dict.group_title,
                                                      GROUP_URL=metadata_dict.group_url,
                                                      STATE=metadata_dict.state,
                                                      CHANGE_DATE=metadata_dict.change_date,
                                                      CHANGE_DESC=metadata_dict.change_desc)

                # Add in custom subject with dataset name.
                subject = subject_template.substitute(DATASET_NAME=metadata_dict.ds_title,
                                                      GROUP_NAME=metadata_dict.group_title,
                                                      STATE=metadata_dict.state)
            elif template == "datasets":
                message = message_template.substitute(DATASET_NAME=metadata_dict.ds_title,
                                                      DATA_URL=metadata_dict.ds_url,
                                                      SUMMARY=metadata_dict.ds_summary,
                                                      STATE=metadata_dict.state,
                                                      CHANGE_DATE=metadata_dict.change_date,
                                                      CHANGE_DESC=metadata_dict.change_desc)

                # Add in custom subject with dataset name.
                subject = subject_template.substitute(DATASET_NAME=metadata_dict.ds_title,
                                                      STATE=metadata_dict.state)
            else:
                logger.info(log_dict.get("email_template_arg_error"))
            # Setup the parameters of the message.
            msg["From"] = smtp_settings.get("mail_from")
            msg["To"] = ", ".join(metadata_dict.get("emails"))
            msg["Subject"] = subject

            # Add the message from template to body of email.
            msg.attach(MIMEText(message, "plain"))

            # Send the message via the server set up earlier.
            logger.info(log_dict.get("email_send"))
            server.sendmail(msg["From"], metadata_dict.get("emails"), msg.as_string())

            del msg
            server.quit()
    except Exception as e:
        logger.error(log_dict.get("email_send_error"))
        logger.error(e.args)


def latest_modified_date(dataset):
    try:
        # get resources from dataset
        resources = dataset.get("resources")
        if resources is not None:
            # get most recently modified date from list of resources
            max_date = max(
                [dateutil.parser.parse(res.get("last_modified")) for res in resources if
                 res.get("last_modified") is not None])
            return max_date
    except Exception as e:
        logger.error(log_dict.get("last_modified_error"))
        logger.error(e.args)


def new_or_updated_group(dataset, group_name):
    """
    Get all the metadata required to fill template into a dictionary.
    """
    try:
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
        # if dataset was created in the last hour, send email to members of org
        if minutes_diff < 60.0:
            logger.info(log_dict.get("dataset_new_found").format(dataset.get("name")))
            # get group metadata
            logger.info(log_dict.get("meta_new"))
            group_data = ck.get_group(group_name)
            # have to get the user IDs in order to filter user list and get emails
            group_user_ids = [user.get("id") for user in group_data.get("users")]
            # get list of all users information on gis hub
            all_users = ck.get_user_info()
            # now filter the list of all users to get the ones part of the group
            group_user_emails = [u.get("email") for u in all_users if u.get("id") in group_user_ids]
            # get metadata for email
            template_meta = MetaTemplateGroup(dataset,
                                              group_data,
                                              group_name,
                                              group_user_emails,
                                              state="New",
                                              change_date="",
                                              change_desc="")
            logger.info(log_dict.get("meta_prepared"))
            return template_meta
        # if resources were updated in the last hour, AND dataset was not created today, send email to members of group
        elif res_minutes_diff < 60.0 and date_created.date() != today.date():
            logger.info(log_dict.get("dataset_updated_found").format(dataset.get("name")))
            # get group metadata
            logger.info(log_dict.get("meta_updated"))
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
            template_meta = MetaTemplateGroup(dataset=dataset,
                                              group_data=group_data,
                                              group_name=group_name,
                                              group_user_emails=group_user_emails,
                                              state="Updated",
                                              change_date=change_date,
                                              change_desc=change_desc)

            logger.info(log_dict.get("meta_prepared"))
            return template_meta
    except Exception as e:
        logger.error(log_dict.get("meta_dict_error"))
        logger.error(e.args)


def check_updated(dataset):
    try:
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
        # if resources have been updated, process and send email
        if res_minutes_diff < 60.0 and date_created.date() != today.date():
            logger.info(log_dict.get("dataset_updated_found").format(dataset.get("name")))
            # get metadata
            logger.info(log_dict.get("all_users_text").format(dataset))
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
                template_meta = MetaTemplate(dataset=dataset,
                                             user_emails=user_emails,
                                             state="Updated",
                                             change_date=change_date,
                                             change_desc=change_desc)

                logger.info(log_dict.get("meta_prepared"))
                return template_meta
            else:
                logger.info(log_dict.get("no_followers").format(dataset.get("name")))
    except Exception as e:
        logger.error(log_dict.get("meta_dict_error"))
        logger.error(e.args)


def process_group(group_name):
    """
    Get datasets in group, check for newly published ones, send email to members of group if new data exists.
    """
    logger.info("Getting list of datasets in {}".format(group_name))
    datasets_group = ck.list_datasets_in_group(group_name)
    new_updated_group = [new_or_updated_group(dataset, group_name) for dataset in datasets_group]

    if len(new_updated_group) > 0:
        # Load template email body and subject.
        email_template_group = read_templates("templates/emails/new_updated_dataset_group.txt",
                                              "templates/emails/new_updated_dataset_group_subject.txt")
        for data_dict in new_updated_group:
            send_email(data_dict, email_template_group[0], email_template_group[1], template="group")
    else:
        logger.info("No new or updated datasets in {} last 60 minutes.".format(group_name))

    return


def process_updated():
    """
    Check all datasets for updated, email followers if any
    """
    logger.info("Checking all datasets for updates and followers to email...")
    # get all datasets
    all_datasets = ck.list_datasets()
    updated_meta = [check_updated(dataset) for dataset in all_datasets]

    if len(updated_meta) > 0:
        # Load template email body and subject.
        email_template_updated = read_templates("templates/emails/new_updated_dataset.txt",
                                                "templates/emails/new_updated_dataset_subject.txt")

        for data_dict in updated_meta:
            send_email(data_dict, email_template_updated[0], email_template_updated[1], template="datasets")
    else:
        logger.info("No updated datasets in last 60 minutes.")

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
