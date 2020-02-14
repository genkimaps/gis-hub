#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import dfo_plugin_settings
from traceback import format_exc
from ckan.logic import get_action

logger = dfo_plugin_settings.setup_logger(__name__)


def validate_resource(context, resource):
    """ Filter chain to validate a resource """
    resource = ensure_resource_type(context, resource)
    return resource


def ensure_resource_type(context, resource):

    res_id = resource.get('id')
    res_name = resource.get('name')
    res_type = resource.get('resource_type')
    logger.info('Resource: %s %s created' % (res_name, res_id))
    # Check if resource_type is not already set
    if res_type:
        logger.info('Resource: %s, type already set: %s' % (res_name, res_type))
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
    return resource


def validate_dataset(context, dataset):
    """ Filter chain to validate a dataset """
    dataset = kw_case_dups(context, dataset)
    return dataset


def kw_case_dups(context, dataset):
    """
    Check a dataset for keywords--science and goc. We don't validate GoC
    keywords here; that happens downstream. We only make everything lowercase and
    remove duplicates in this function. Patch the package with updated keywords,
    only if changed.
    :param dataset:
    :return: clean dataset with lowerised, no duplicates in keywords and science
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
        logger.info(result)
        logger.info(dataset)
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
