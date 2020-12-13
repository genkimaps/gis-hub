import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action
from ckan.lib import base
from ckan.common import request
import ckan.plugins as p
import dfo_plugin_settings
from flask import send_file, jsonify
from subprocess import check_output, Popen
import traceback
import os


logger = settings.setup_logger(__name__)


@side_effect_free
def run_hnap(context, data_dict):
    username = context.get('user')
    # Get the email address for current user
    result = get_action('user_show')(context, {'id': username})
    email = result.get('email')
    if not email:
        err_msg = 'No email address for user: %s' % username
        logger.error(err_msg)
        return err_msg
    resource_id = data_dict.get('resource_id')
    return generate_hnap_file(resource_id, email=email)


def generate_hnap_file(resource_id, email=None):
    logger.info('Running hub-geo-api for HNAP export of resource: %s' % resource_id)
    command_parts = [dfo_plugin_settings.hubapi_venv,
                     '/home/dfo/hub-geo-api/hnap_export.py',
                     '-r', resource_id]
    if email:
        command_parts += ['-e', email]
        logger.info('Email results to: %s' % email)
    hnap_export_cmd = dfo_plugin_settings.run_command_as(command_parts)
    try:
        if not email:
            # Send command to hub-geo-api, wait for output
            hnap_file = check_output(hnap_export_cmd)
            # Strip any excess characters such as trailing newline \n
            hnap_file = hnap_file.strip()
            user_msg = 'Created HNAP XML file: %s' % hnap_file
        else:
            # Use Popen, do not wait for command to finish
            Popen(hnap_export_cmd)
            user_msg = 'HNAP export will be sent to: %s' % email
    except:
        logger.error(traceback.format_exc())
        return jsonify({'error': traceback.format_exc()})
    logger.info(user_msg)
    return user_msg
    # return jsonify({'hnap_file': hnap_file})
    # return send_file(hnap_file)


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
