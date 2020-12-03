import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action
from ckan.lib import base
import ckan.plugins as p
import dfo_plugin_settings
from flask import send_file, jsonify
from subprocess import check_output
import traceback


logger = settings.setup_logger(__name__)


@side_effect_free
def run_hnap(context, data_dict):
    resource_id = data_dict.get('resource_id')
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
    logger.info('Downloading %s' % hnap_file)
    return hnap_file
    # return jsonify({'hnap_file': hnap_file})
    # return send_file(hnap_file)


# Add to resource_read template:
# <li>{% link_for _('Manage'), named_route='resource.edit', id=pkg.name, resource_id=res.id, class_='btn btn-default', icon='wrench' %}</li>

class HNAPController(base.BaseController):

    @staticmethod
    def get_hnap(dataset_id, resource_id):
        # return flask.send_file(filepath)
        logger.info('HNAP controller: %s %s' % (dataset_id, resource_id))

        return p.toolkit.render('docs/docs.html')
