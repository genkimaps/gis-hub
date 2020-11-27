import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action
from ckan.lib import base
import flask

import ckan.plugins as p

logger = settings.setup_logger(__name__)


# @side_effect_free
# def run_hnap(context, data_dict):
#     pass


# Add to resource_read template:
# <li>{% link_for _('Manage'), named_route='resource.edit', id=pkg.name, resource_id=res.id, class_='btn btn-default', icon='wrench' %}</li>

class HNAPController(base.BaseController):
    def get_hnap(self, dataset_id, resource_id):
        # return flask.send_file(filepath)
        logger.info('HNAP controller: %s %s' % (id, resource_id))

        return p.toolkit.render('docs/docs.html')
