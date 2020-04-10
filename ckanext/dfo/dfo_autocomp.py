"""
Logic for custom DFO-specific autocomplete, including:
- keywords (GoC themes from the Thesaurus)
- species codes
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
def search_goc_theme(context, data_dict):
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


"""
Species code autocomplete to match both code and name (latin or common name)
Code, latin name, and common name are concatenated in field 'species_name'
Unlike goc-themes autocomp, we will return both code and display name.
Also want the match to be anywhere in the string, not just at the start, also 
not necessarily at a word break, e.g. we want to match:
fish > hagfish
03A > match at start of string, not just in the middle
so need to use regex ~* 'term' instead of ILIKE '%term%'

The resource ID for the table of species codes: cdc22563-dc61-4abc-9b6d-a863382e4b6c
SELECT * FROM "cdc22563-dc61-4abc-9b6d-a863382e4b6c" WHERE "species_name" ~* '037'
SELECT * FROM "cdc22563-dc61-4abc-9b6d-a863382e4b6c" WHERE "species_name" ~* 'shark'
SELECT * FROM "cdc22563-dc61-4abc-9b6d-a863382e4b6c" WHERE "species_name" ~* 'lepidoch'

A full URL-quoted example:
https://www.gis-hub.ca/api/action/datastore_search_sql?sql=SELECT%20*%20FROM%20%22cdc22563-dc61-4abc-9b6d-a863382e4b6c%22%20WHERE%20%22species_name%22%20~*%20%27fish%27

In plugins.py, this method is registered as an action: ac_species_code
Example URL: https://www.gis-hub.ca/api/action/ac_species_code?q=lepidoch
This can now be used as an API endpoint for Select2.js in our HTML template. 
"""
@side_effect_free
def search_species_code(context, data_dict):
    # Query datastore for matching terms
    logger.debug(data_dict)
    term = data_dict.get('q')
    sql = 'SELECT * FROM "%s" WHERE "species_name"  ~* \'%s\'' % (settings.species_codes_id, term)
    logger.info(sql)
    search_qry = {
        'resource_id': settings.species_codes_id,
        # Default limit is only 100 items
        'limit': 5000,
        'sql': sql

    }
    result = get_action('datastore_search_sql')(context, search_qry)

    sp_codes = []
    records = result.get('records')
    for record in records:
        match = {'code': record.get('code'),
                 'species_name': record.get('species_name')
                 }
        sp_codes.append(match)
    return sp_codes
