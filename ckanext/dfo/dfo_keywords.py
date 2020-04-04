"""
Logic for getting DFO-specific keywords
"""

import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action

logger = settings.setup_logger(__name__)

"""
from /ckan/plugins/interfaces.py:

By decorating a function with the `ckan.logic.side_effect_free`
decorator, the associated action will be made available by a GET
request (as well as the usual POST request) through the action API.

This is super confusing. The @side_effect_free is not supposed to be used 
in the get_actions() function (which implements plugins.IActions) rather
it needs to be attached to *the function itself* which is referenced by 
get_actions(). Very confusing. 
"""

# Turn off tag name validation:
# In base ckan, /ckan/logic/validators.py, comment this line (460):
# tag_name_validator(tag, context)
@side_effect_free
def find_matching_goc_theme(context, data_dict):
    # Query datastore for matching terms
    logger.debug(data_dict)
    term = data_dict.get('q')

    term_like = " '%s%%' " % term
    sql_p1 = 'SELECT * FROM "%s" WHERE "theme" ILIKE ' % settings.goc_themes_id
    sql_ilike = sql_p1 + term_like
    logger.info(sql_ilike)
    search_qry = {
        'resource_id': settings.goc_themes_id,
        # Default limit is only 100 items
        'limit': 5000,
        'sql': sql_ilike

    }
    result = get_action('datastore_search_sql')(context, search_qry)

    goc_themes = []
    records = result.get('records')
    for record in records:
        goc_themes.append(record.get('theme').lower())
    return goc_themes


def goc_theme_list(context):
    """
    Gets the complete list of GoC themes from datastore in lowercase
    :param context:
    :return:
    """
    # Use resource id for GoC themes:
    # https://www.gis-hub.ca/dataset/goc-themes/resource/88f5c7a2-7b25-4ce8-a0c6-081236f5da76

    result = get_action('datastore_search')(context, {
        'resource_id': settings.goc_themes_id,
        # Default limit is only 100 items
        'limit': 5000})

    goc_themes = []
    records = result.get('records')
    for record in records:
        goc_themes.append(record.get('theme').lower())
    return goc_themes
