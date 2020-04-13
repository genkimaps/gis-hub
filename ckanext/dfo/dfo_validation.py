#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import dfo_plugin_settings
import json
from traceback import format_exc
from ckan.logic import get_action

logger = dfo_plugin_settings.setup_logger(__name__)

CHANGE_DESC_PLACEHOLDER = 'internal update from hub-geo-api'


""" Begin RESOURCE validation """
def validate_resource(context, resource):
    """ Filter chain to validate a resource """
    ensure_resource_type(context, resource)
    save_change_history(context, resource, 'resource')
    return resource


def save_change_history(context, data_dict, type):
    """ Saves change history to the DATASET-LEVEL change_history field,
        regardless of whether the change originated from a resource or
        from the dataset.
    """
    if type=='resource':
        # Get the parent package id and the package metadata
        dataset_id = data_dict.get('package_id')
        ds_metadata = get_action('package_show')(context, {'id': dataset_id})
        title = get_name_or_id(data_dict)
        if not ds_metadata:
            logger.error('Cannot get metadata for parent dataset: %s' % dataset_id)

    else:
        dataset_id = data_dict.get('id')
        title = data_dict.get('title')
        ds_metadata = data_dict
    patch = {'id': dataset_id}

    logger.info('Update change history for %s %s' % (title, type))
    # Get change description from the appropriate field
    change_desc_field = 'change_description_%s' % type
    change_desc = data_dict.get(change_desc_field)
    # Ignore if internal update
    logger.info('%s: %s' % (change_desc_field, change_desc))
    if change_desc == CHANGE_DESC_PLACEHOLDER:
        logger.info('Internal change from API. <<< THIS CHANGE DESCRIPTION WILL BE IGNORED ')
        return
    # Get existing change history from dataset
    change_history = ds_metadata.get('change_history')
    logger.debug('change_history: %s' % change_history)
    if not change_history or change_history == '[]':
        logger.error('Change history is EMPTY but should not be!')
        return
    # Convert change_history to dict
    try:
        if not change_history:
            # Use empty list
            change_history = '[]'
        change_history = json.loads(change_history)
    except:
        logger.error(format_exc())
        return

    # TODO: remove empty change history entries?
    # Add current change history
    if not change_desc:
        logger.warning('No current change description')
        return

    new_history_entry = {'change_date': datetime.now().strftime('%Y-%m-%d'),
                         'change_description': change_desc}

    # Check if this entry already exists in change history
    change_history.append(new_history_entry)
    # put change history back to string for API
    change_history_str = json.dumps(change_history)

    # Patch dataset with the new change history
    patch['change_history'] = change_history_str
    # DON'T DO THIS, we are only using the change_description field at resource level.
    # Ensure that the change_description field is set to the internal
    # placeholder value, to avoid an infinite loop of updates
    # patch[change_desc_field] = CHANGE_DESC_PLACEHOLDER
    logger.debug('Patch change history: %s' % change_history_str)
    result = get_action('package_patch')(context, patch)
    updated_change_history = result.get('change_history')
    logger.info('Updated: %s' % updated_change_history)


def set_resource_display(resource):
    """
    Modify a resource dict before it is displayed to user
    :param resource:
    :return: updated resource
    """
    # Set change_description to empty string, will force user to enter data
    resource['change_description_resource'] = ''
    res_name_or_id = get_name_or_id(resource)
    logger.info('Resource %s: form will have empty change_description' % res_name_or_id)
    return resource


def get_name_or_id(data_dict):
    id = data_dict.get('id')
    name = data_dict.get('name')
    title = data_dict.get('title')
    name_or_id = name
    if not name_or_id:
        name_or_id = title
        if not name_or_id:
            name_or_id = id
    return name_or_id


def ensure_resource_type(context, resource):

    res_id = resource.get('id')
    res_name_or_id = get_name_or_id(resource)
    res_type = resource.get('resource_type')
    logger.info('Resource: %s %s checking resource type' % (res_name_or_id, res_id))
    # Check if resource_type is not already set
    if res_type:
        logger.info('Resource: %s, resource_type already set: %s' % (res_name_or_id, res_type))
        return resource

    # Resource type is not already set. This will be either Upload or Link
    # If url type is upload, it's an upload resource
    patch = {'id': res_id}
    if resource.get('url_type') == 'upload':
        patch['resource_type'] = 'Upload'
    # Otherwise it's a link
    else:
        patch['resource_type'] = 'Link'
        # Also set format to link if URL does not end with .html
        res_url = resource.get('url')
        try:
            if len(res_url) > 0 and not res_url.endswith('.html'):
                patch['format'] = 'link'
        except:
            pass

    # To update resource_type, run the resource_patch action
    result = get_action('resource_patch')(context, patch)


""" Begin DATASET validation """
def validate_dataset(context, dataset):
    """ Filter chain to validate a dataset """
    dataset = kw_case_dups(context, dataset)
    # Disable save_change_history for dataset. Instead use existing dataset-level
    # change history field on the GUI.
    # save_change_history(context, dataset, 'dataset')
    return dataset


def set_dataset_display(dataset):
    """
    Customize how a dataset is displayed in the browser.
    This only affect the display shown to the user (in the dataset page or
    dataset edit page), not the saved metadata.
    :param dataset: dataset dict
    :return: modified dataset dict
    """
    title = dataset.get('title')
    change_history = dataset.get('change_history')
    logger.info('change_history: %s' % change_history)
    logger.info('Last change description: %s' % dataset.get('change_description_dataset'))
    dataset['change_description_dataset'] = ''
    logger.info('Dataset: %s: form will have empty change_description' % title)
    return dataset


def kw_case_dups(context, dataset):
    """
    Check a dataset for keywords--science and goc. We don't validate GoC
    keywords here; that happens downstream. We only make everything lowercase and
    remove duplicates in this function. Patch the package with updated keywords,
    only if changed.
    :param dataset:
    :return: Note that we do NOT return the clean dataset with lowerised,
    no duplicates in keywords and science. Instead we return the original
    dataset object that was passed.
    """
    orig_kw = dataset.get('keywords')
    orig_sci_kw = dataset.get('science_keywords')
    clean_kw = lowerise_and_dedup(dataset.get('keywords'))
    clean_sci_kw = lowerise_and_dedup(dataset.get('science_keywords'))
    # Patch keywords if needed
    patch = {'id': dataset.get('id')}
    fix_keywords = False
    if orig_kw != clean_kw:
        fix_keywords = True
        patch['keywords'] = clean_kw
    if orig_sci_kw != clean_sci_kw:
        fix_keywords = True
        patch['science_keywords'] = clean_sci_kw
    if fix_keywords:
        # Patch the dataset
        logger.info('%s: cleaned keywords: %s %s' % (dataset.get('name'), clean_kw, clean_sci_kw))
        result = get_action('package_patch')(context, patch)
        # logger.info(result)
        # logger.info(dataset)
    else:
        logger.info('%s: Keywords OK.' % dataset.get('name'))
    return dataset


def lowerise_and_dedup(kw_str):
    """
    Lowerise comma-separated keywords and de-duplicate.
    :param kw_str: comma-separated keyword string
    :return: validated keyword string
    """
    try:
        if not kw_str or len(kw_str) == 0:
            return kw_str
        keywords = kw_str.split(',')
        kw_list = []
        for kw in keywords:
            kw_cleaned = kw.strip().lower()
            if kw_cleaned not in kw_list:
                kw_list.append(kw_cleaned)
        kw_clean_str = ','.join(kw_list)
        logger.debug('Validated keywords: %s' % kw_clean_str)
        return kw_clean_str
    except (TypeError, AttributeError):
        logger.warning(format_exc())
        logger.warning('Bad value in keyword string: %s' % kw_str)
        return kw_str
