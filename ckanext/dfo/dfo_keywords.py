"""
Logic for getting DFO-specific keywords
"""

import dfo_plugin_settings
from ckan.logic import get_action
import ckan.logic as logic
import ckan.model as model

logger = dfo_plugin_settings.setup_logger(__name__)

# Create a dummy Pylons context object
# From /ckan/lib/cli.py line 135
# Does not work, we get: 
# sqlalchemy.exc.UnboundExecutionError: Could not locate a bind configured on mapper Mapper|User|user, SQL expression or this Session
# site_user = logic.get_action('get_site_user')({
#     'model': model,
#     'ignore_auth': True},
#     {}
# )
# context = {
#     'model': model,
#     'session': model.Session,
#     'ignore_auth': True,
#     'user': site_user['name'],
# }


def goc_theme_list(context):
    """
    Gets all GoC themes from datastore in lowercase
    :param context:
    :return:
    """
    # Use resource id for GoC themes:
    # https://www.gis-hub.ca/dataset/goc-themes/resource/88f5c7a2-7b25-4ce8-a0c6-081236f5da76
    goc_themes_id = '88f5c7a2-7b25-4ce8-a0c6-081236f5da76'
    result = get_action('datastore_search')(context, {
        'resource_id': goc_themes_id,
        # Default limit is only 100 items
        'limit': 5000})

    goc_themes = []
    records = result.get('records')
    for record in records:
        goc_themes.append(record.get('theme').lower())
    return goc_themes
