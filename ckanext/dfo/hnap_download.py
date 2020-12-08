import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action
from ckan.lib import base
from ckan.common import request
import ckan.plugins as p
import dfo_plugin_settings
from flask import send_file, jsonify
from subprocess import check_output
import traceback
import os
import io
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = settings.setup_logger(__name__)


@side_effect_free
def run_hnap(context, data_dict):
    resource_id = data_dict.get('resource_id')

    hnap_file = generate_hnap_file(resource_id)

    # Load template email body and subject.
    email_template_obj = read_templates("templates/emails/hnap_generate.txt.txt",
                                        "templates/emails/hnap_generate_subject.txt.txt")

    # Use data from maintainer_list and email_template_obj to send email to list of users.
    setup_smtp(email_template_obj[0], email_template_obj[1], hnap_file)
    return hnap_file


def generate_hnap_file(resource_id):
    logger.info('Running hub-geo-api for HNAP export of resource: %s' % resource_id)
    command_parts = [dfo_plugin_settings.hubapi_venv,
                     '/home/dfo/hub-geo-api/hnap_export.py',
                     '-r', resource_id]
    hnap_export_cmd = dfo_plugin_settings.run_command_as(command_parts)
    try:
        hnap_file = check_output(hnap_export_cmd)
        # Strip any excess characters such as trailing newline \n
        hnap_file = hnap_file.strip()
    except:
        logger.error(traceback.format_exc())
        return jsonify({'error': traceback.format_exc()})
    logger.info('Created HNAP XML file: %s' % hnap_file)
    return hnap_file
    # return jsonify({'hnap_file': hnap_file})
    # return send_file(hnap_file)


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
    except:
        logger.error(traceback.format_exc())


def setup_smtp(message_template, subject_template, hnap_xml_file):
    """
    Establishes connection with MailGun server. Sends an email with attached xml file to GIS Hub user.
    """
    try:
        # Set up the SMTP server with mailgun settings.
        server = smtplib.SMTP(host=os.environ.get("CKAN_SMTP_SERVER"))

        # Start connection to server and login with credentials.
        server.starttls()
        server.login(os.environ.get("CKAN_SMTP_USER"), os.environ.get("CKAN_SMTP_PASSWORD"))

        # For each record (dataset) in csv, send message.
        msg = MIMEMultipart()

        # Setup the parameters of the message.
        msg["From"] = os.environ.get("CKAN_SMTP_MAIL_FROM")
        msg["To"] = "Cole.Fields@dfo-mpo.gc.ca"
        msg["Subject"] = subject_template

        # Add the message from template to body of email.
        msg.attach(MIMEText(message_template, "plain"))

        xml_file = hnap_xml_file

        # Open xml file in binary mode
        with open(xml_file, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {xml_file}",
        )

        # Add attachment to message and convert message to string
        msg.attach(part)
        text = msg.as_string()

        # Send the message via the server set up earlier.
        server.sendmail(msg["From"], msg["To"], text)

        server.quit()
    except:
        logger.error(traceback.format_exc())
    del msg

# Add to resource_read template:
# <li>{% link_for _('Manage'), named_route='resource.edit', id=pkg.name, resource_id=res.id, class_='btn btn-default', icon='wrench' %}</li>

class HNAPController(base.BaseController):

    def get_hnap(self):
        for k, v in request.params.iteritems():
            logger.info('%s: %s' % (k, v))
        resource_id = request.params.get('resource_id')
        dataset_id = request.params.get('dataset_id')
        logger.info('HNAP controller: %s %s' % (dataset_id, resource_id))
        hnap_file = generate_hnap_file(resource_id)

        """
        This does not work:
        File '/home/tk/venv/local/lib/python2.7/site-packages/flask/globals.py', line 37 in _lookup_req_object
            raise RuntimeError(_request_ctx_err_msg)
        RuntimeError: Working outside of request context.
        """

        # Doesn't work because we don't have a Flask context, probably using pylons
        # return send_file(hnap_file)
        # return p.toolkit.render('docs/docs.html')
        # Added the HNAP export folder to CKAN's extra_public_paths
        # https://docs.ckan.org/en/2.9/maintaining/configuration.html#extra-public-paths
        return p.toolkit.redirect_to('https://www.gis-hub.ca/' + os.path.basename(hnap_file))

        # Test URL:
        # https://www.gis-hub.ca/get_hnap?resource_id=8c074888-cf46-46e8-b082-16aa41916bd0

    # @side_effect_free
    # def get_hnap(self, context, data_dict):

    # @staticmethod
    # def get_hnap(dataset_id, resource_id):
    #     # return flask.send_file(filepath)
    #     logger.info('HNAP controller: %s %s' % (dataset_id, resource_id))
    #
    #     return p.toolkit.render('docs/docs.html')
