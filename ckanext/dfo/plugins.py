#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
from ckan.lib import base
from ckan.common import request, g
from ckanext.scheming import helpers as scheming_helpers
from ckantoolkit import get_validator
from ckan.plugins.toolkit import Invalid
from ckan.common import _
from ckan.logic import get_action
import dfo_plugin_settings
import dfo_validation
import dfo_autocomp
import hnap_download
import subprocess
import traceback
import json

logger = dfo_plugin_settings.setup_logger(__name__)
logger.info('This is the logger for ckanext-dfo')


""" Functions for DFO-specific validation """
def non_empty_fields(field_list, pkg_dict, exclude):
    r = []
    for field in field_list:
        if field['field_name'] in exclude:
            continue

        if field.get('display_snippet', False) is None:
            continue

        if pkg_dict.get(field['field_name']):
            r.append(field)
    return r


def run_command_as(command_parts):
    """
    We need to run external commands that communicate with the hub-geo-api component
    as user dfo with --login to get enviro vars and permissions.
    This prevents various exceptions, including:
    - botocore.exceptions.NoCredentialsError: Unable to locate credentials
    - no write permission to folders within /home/dfo/hub-geo-api
    :param command_parts: original command parts for the 'subprocess' call
    :return: command with dfo login prepended
    """
    if not type(command_parts) is list:
        logger.error('command_parts must be a list of command strings')
        return
    return ['sudo', '-u', 'dfo', '--login'] + command_parts


def object_updated_or_created(context, data_dict):
    """ This is called AFTER an object is updated or created. We only
        care about resources and packages; other types are immediately
        returned.
    """
    obj_title = data_dict.get('title')
    logger.debug('%s: after_create/update from resource or dataset' % obj_title)
    obj_type, data_dict = detect_object_type(data_dict)
    if obj_type == 'resource':
        # If the object is a resource, we don't have to worry about backup, because
        # package_update will be triggered after the resource is updated.
        logger.info('Resource was updated: %s ' % obj_title)
        change_desc = data_dict.get('change_description_resource')
        logger.debug('Resource: %s Change Description: %s' % (
            obj_title, change_desc))
        return dfo_validation.validate_resource(context, data_dict)

    elif obj_type == 'dataset':
        ds_name = data_dict.get('name')
        logger.info('Dataset was updated: %s ' % ds_name)

        # Done: ensure download placeholder is in position 0
        resources = data_dict.get('resources')
        download_position = None
        if type(resources) is list:
            logger.info('Checking contents of %s resources' % len(resources))
            for i, res in enumerate(resources):
                # Check for download_resource
                # The 'position' property is not set, use the list index
                url_type = res.get('url_type')
                if str(url_type) == 'upload' and i > 0:
                    logger.warning('Download resource in wrong position! %s' % i)
                    logger.info('url type: "%s", index: %s' % (str(url_type), i))
                    # Set download resource position
                    download_position = i
                res_title = res.get('title')
                change_desc = res.get('change_description_resource')
                logger.info('Dataset: %s, Resource: %s, Change Description: "%s"' % (
                    obj_title, res_title, change_desc))

            # Fix position if needed
            if download_position is not None:
                # new_resources = []
                download_resource = resources.pop(download_position)
                # download_resource in first position, append other resources
                new_resources = [download_resource] + resources
                logger.info('Updating resource order...')
                for i, res in enumerate(new_resources):
                    res_title = res.get('title')
                    url_type = res.get('url_type')
                    logger.debug('%s: type: "%s", index: %s' % (res_title, url_type, i))

                # Update package with new resource order
                resource_ids = [x['id'] for x in new_resources]
                data = {'id': ds_name, 'order': resource_ids}
                result = get_action('package_resource_reorder')(context, data)

        elif resources is None:
            logger.info('Only the dataset was updated, no resources to check')
        else:
            # logger.info('Resources list is: %s' % (str(type(resources))))
            logger.warning('Dataset %s: Resources list in unexpected format: %s' % (
                ds_name, str(type(resources))))

        # TODO: check if dataset has changed before backup
        logger.debug('Backup to cloud command:')
        # Trigger external call to hub-geo-api to upload metadata to S3.
        # Must do this because hub-geo-api is Python3, can't mix with Python2 CKAN.
        # cmd = ['sudo', '-u', 'dfo', '--login',
        backup_cmd = run_command_as([dfo_plugin_settings.hubapi_venv,
               dfo_plugin_settings.hubapi_backup_script,
               ds_name])

        logger.debug(backup_cmd)

        try:
            subprocess.Popen(backup_cmd)
            logger.info('Backup command was started.')
        except:
            logger.error(traceback.format_exc())
            logger.info('Backup command failed')

        return dfo_validation.validate_dataset(context, data_dict)

    # If any other object type, just return it
    return data_dict


def detect_object_type(data_dict):
    """
    Check if a data_dict is a resource, package, or other
    :param data_dict:
    :return: object type, data_dict
    """
    if data_dict.get('type') == 'dataset':
        return 'dataset', data_dict
    if data_dict.get('package_id'):
        return 'resource', data_dict
    else:
        return 'other', data_dict


class DFOPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IFacets)
    p.implements(p.IPackageController)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IRoutes)
    p.implements(p.IValidators)
    p.implements(p.IResourceController)
    
    # Added for custom autocomplete
    p.implements(p.IActions)
    
    # Implement function in IActions for custom autocomplete
    # DO NOT USE @side_effect_free here! Causes CKAN 2.7.x to crash on startup, 
    # when loading plugins (but does not crash CKAN 2.8)
    # @side_effect_free
    def get_actions(self):
        return {'ac_goc_themes': dfo_autocomp.search_goc_theme,
                'ac_species_code': dfo_autocomp.search_species_code,
                'ac_contacts': dfo_autocomp.search_contacts,
                'hnap_export': hnap_download.run_hnap
                }

    # IConfigurer
    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')
        p.toolkit.add_resource('fanstatic', 'dfo')

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        if package_type in ('dataset', None):
            facets_dict.pop('license_id', None)
            facets_dict.pop('tags', None)
            facets_dict.pop('res_format', None)

            facets_dict['res_extras_data_format'] = p.toolkit._('Formats')
            facets_dict['extras_science_keywords'] = p.toolkit._('Keywords')
            facets_dict['extras_theme'] = p.toolkit._('Themes')

        return facets_dict

    def group_facets(self, facets_dict, organization_type, package_type):
        return self.dataset_facets(facets_dict, package_type)

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        return self.dataset_facets(facets_dict, package_type)

    def before_index(self, data_dict):
        data_dict['extras_science_keywords'] = data_dict.get(
            'extras_science_keywords',
            ''
        ).split(',')

        schema = scheming_helpers.scheming_get_dataset_schema('dataset')

        theme = data_dict.get('extras_theme')
        if theme:
            theme_field = scheming_helpers.scheming_field_by_name(
                schema['dataset_fields'],
                'theme'
            )

            data_dict['extras_theme'] = scheming_helpers.scheming_choices_label(
                scheming_helpers.scheming_field_choices(theme_field),
                theme
            )

        return data_dict

    # We don't use all of these methods, but must have them anyway
    # Listed in the same order as in the CKAN docs for IPackageController
    # https://docs.ckan.org/en/2.8/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IPackageController

    # These are all called *twice* once each for Pylons and Flask, super annoying
    # Next 6 are only for IPackageController
    def read(self, entity):
        pass

    def create(self, entity):
        pass

    def edit(self, entity):
        pass

    def authz_add_role(self, object_role):
        pass

    def authz_remove_role(self, object_role):
        pass

    def delete(self, entity):
        pass

    def after_delete(self, context, data_dict):
        return data_dict

    def after_show(self, context, data_dict):
        """
            Modify the dataset (package) dict after everything else, but just
            prior to sending it to the template for display in the web browser
            For DATASET only, not resource
            :param pkg_dict: dataset dict
            :return: modified dataset dict
        """
        title = dfo_validation.get_name_or_id(data_dict)
        logger.debug('%s: after_show triggered' % title)
        # return dfo_validation.set_dataset_display(data_dict)
        return data_dict

    def update_facet_titles(self, facet_titles):
        return facet_titles

    def before_view(self, pkg_dict):
        """
        I thought I could use this to Modify the dataset (package) dict before
        showing in the web browser, but it does not seem to return anything.
        Use after_show() instead, very confusing.
        """
        pkg_dict = toolkit.get_action('package_show')({}, {
            'include_tracking': True,
            'id': pkg_dict['id']
        })
        return pkg_dict

    # The next two are used by both package and resource
    def after_create(self, context, data_dict):
        logger.debug('after_create from resource or dataset')
        return object_updated_or_created(context, data_dict)

    def after_update(self, context, data_dict):
        # We need to treat this as if it were after_create.
        package_id = data_dict.get('package_id')
        obj_type = 'resource'
        if not package_id:
            obj_type = 'dataset'

        logger.info('"after_update" from %s' % obj_type)
        return object_updated_or_created(context, data_dict)

    def after_search(self, search_results, search_params):
        return search_results

    def download_event(self, resource):
        toolkit.add_activity()

    def before_search(self, search_params):
        return search_params

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_thumbnail': get_thumbnail,
            'non_empty_fields': non_empty_fields,
            'scheming_field_required': self.field_required_helper,
            'now': datetime.now,
            'utcnow': datetime.utcnow,
            'resource_display_name': self.resource_display_name,
            'load_json': self.load_json
        }

    # Additional methods only in IResourceController
    def before_create(self, context, resource):
        logger.debug('before_create: Going to create resource/package: %s' % resource)

    def before_update(self, context, current, resource):
        res_title = resource.get('title')
        disclaimer = resource.get('disclaimer')
        logger.info('before_update: Going to update resource: %s' % res_title)
        logger.debug('%s: Changed: %s' % (res_title, disclaimer))
        pass

    def before_show(self, resource):
        """
        Modify the resource dict before showing in the web browser
        For RESOURCE only, not dataset (package)
        :param resource:
        :return: updated resource
        """
        title = dfo_validation.get_name_or_id(resource)
        logger.debug('%s: before_show triggered' % title)
        # return dfo_validation.set_resource_display(resource)
        return resource

    def before_delete(self, context, resource, resources):
        pass

    # END of additional methods only in IResourceController

    # IRoutes
    def before_map(self, map):
        map.connect(
            '/advanced_search',
            controller='ckanext.dfo.plugins:AdvancedSearch',
            action='search'
        )
        map.connect(
            '/docs',
            controller='ckanext.dfo.plugins:DocsController',
            action='docs'
        )
        map.connect(
            '/dataset/{dataset_id}/resource/get_hnap',
            controller='ckanext.dfo.hnap_download:HNAPController',
            action='get_hnap'
        )
        return map

    def after_map(self, map):
        return map

    # IValidators
    def get_validators(self):
        return {
            'require_when_published': self.required_validator,
            'goc_themes_only': self.goc_themes_validator
        }

    @staticmethod
    def goc_themes_validator(value, context):
        # Validate keywords against a list of GOC themes
        logger.debug('Validating "%s" against GOC themes' % value)
        goc_themes = dfo_autocomp.goc_theme_list(context)
        
        keywords = value.split(',')
        for kw in keywords:
            if not kw.lower().strip() in goc_themes:
                invalid_msg = 'Not a valid GoC theme: %s' % kw
                logger.warning(invalid_msg)
                raise Invalid(invalid_msg)
        return value


    @staticmethod
    def required_validator(key, flattened_data, errors, context):
        """
        A custom required validator that prevents publishing if a required
        field is not provided.
        """
        is_private = flattened_data[('private',)]
        if not is_private:
            return get_validator('not_empty')(
                key,
                flattened_data,
                errors,
                context
            )

        return get_validator('ignore_missing')(
            key,
            flattened_data,
            errors,
            context
        )

    @staticmethod
    def field_required_helper(field):
        """
        Return field['required'] or guess based on validators if not present.
        """
        if 'required' in field:
            return field['required']

        validators = field.get('validators', '').split()

        # The standard CKAN "required" validator.
        if 'not_empty' in validators:
            return True

        # Our custom DFO validator to only require a field on publishing.
        if 'require_when_published' in validators:
            return True
    
    @staticmethod
    def resource_display_name(resource_dict):
        # Use title then name
        title = resource_dict.get('title')
        if not title:
            name = resource_dict.get('name')
            if name:
                title = name
        if not title:
            return _("Unnamed resource")
        else:
            return _(title)

    @staticmethod
    def load_json(obj, **kw):
        return json.loads(obj, **kw)


def get_thumbnail(package_id):
    package = toolkit.get_action('package_show')(data_dict={'id': package_id})

    for resource in package.get('resources', []):
        name = resource.get('name')
        if name and name.lower() == 'thumbnail':
            return resource['url']


class DocsController(base.BaseController):
    def docs(self):
        return p.toolkit.render('docs/docs.html')


class AdvancedSearch(base.BaseController):
    @staticmethod
    def _to_dt(v):
        return '{v}T00:00:00Z'.format(v=v)

    def search(self):
        schema = scheming_helpers.scheming_get_dataset_schema('dataset')
        if request.method == 'POST':
            args = []
            for k, v in request.params.iteritems():
                if not v.strip():
                    continue

                if k == 'range_picker':
                    start, end = v.split(' - ')
                    args.extend(
                        u'{f}:[{start} TO {end}]'.format(
                            start=self._to_dt(start.strip()),
                            end=self._to_dt(end.strip()),
                            f=f
                        ) for f in (u'start_date', u'end_date')
                    )
                elif k.endswith('_date'):
                    args.append(u'{k}:[{v} TO {v}]'.format(
                        k=k,
                        v=self._to_dt(v)
                    ))
                else:
                    args.append(u'{k}:"{v}"'.format(k=k, v=v))

            h.redirect_to(
                controller='package',
                action='search',
                q=u' AND '.join(args)
            )

        return base.render(
            'advanced_search.html',
            extra_vars={
                'schema': schema
            }
        )
