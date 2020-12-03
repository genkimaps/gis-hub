import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action
from ckan.lib import base
import ckan.plugins as p
from plugins import run_command_as
from flask import send_file, jsonify
from subprocess import check_output
import traceback


logger = settings.setup_logger(__name__)


@side_effect_free
def run_hnap(context, data_dict):
    logger.info(data_dict)
    resource_id = data_dict.get('resource_id')
    command_parts = ['/home/dfo/.virtualenvs/hubapi/bin/python',
                     '/home/dfo/hub-geo-api/hnap_export.py',
                     '-r', resource_id]
    hnap_export_cmd = run_command_as(command_parts)
    try:
        hnap_file = check_output(hnap_export_cmd)
    except:
        logger.error(traceback.format_exc())
        return jsonify({'error': traceback.format_exc()})
    logger.info(hnap_file)
    logger.info(type(hnap_file))


# Add to resource_read template:
# <li>{% link_for _('Manage'), named_route='resource.edit', id=pkg.name, resource_id=res.id, class_='btn btn-default', icon='wrench' %}</li>

class HNAPController(base.BaseController):

    @staticmethod
    def get_hnap(dataset_id, resource_id):
        # return flask.send_file(filepath)
        logger.info('HNAP controller: %s %s' % (dataset_id, resource_id))

        return p.toolkit.render('docs/docs.html')
