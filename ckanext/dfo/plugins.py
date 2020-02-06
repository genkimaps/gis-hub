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
from ckan.logic import get_action
from ckan.common import _
import dfo_plugin_settings

import logging
# logger = logging.getLogger(__name__)
logger = dfo_plugin_settings.setup_logger(__name__)

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


class DFOPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IFacets)
    p.implements(p.IPackageController)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IRoutes)
    p.implements(p.IValidators)
    p.implements(p.IResourceController)

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')
        p.toolkit.add_resource('fanstatic', 'dfo')

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
        return data_dict

    def update_facet_titles(self, facet_titles):
        return facet_titles

    def before_view(self, pkg_dict):
        return pkg_dict

    # The next 2 are used by both package and resource
    def after_create(self, context, data_dict):
        logger.info('after_create from resource or dataset')
        return self.object_updated_or_created(context, data_dict)

    def after_update(self, context, data_dict):
        # We need to treat this as if it were after_create.
        logger.info('after_update from resource or dataset')
        # self.ensure_resource_type(context, data_dict)
        # return data_dict
        return self.object_updated_or_created(context, data_dict)

    def after_search(self, search_results, search_params):
        return search_results

    def download_event(self, resource):
        toolkit.add_activity()

    def before_search(self, search_params):
        return search_params

    def get_helpers(self):
        return {
            'get_thumbnail': get_thumbnail,
            'non_empty_fields': non_empty_fields,
            'scheming_field_required': self.field_required_helper,
            'now': datetime.now,
            'utcnow': datetime.utcnow,
            'resource_display_name': self.resource_display_name
        }

    # Additional methods only in IResourceController
    def before_create(self, context, resource):
        logger.info('Going to create resource/package: %s' % resource)

    def before_update(self, context, current, resource):
        pass

    def before_show(self, resource):
        pass

    def before_delete(self, context, resource, resources):
        pass

    # END of additional methods only in IResourceController

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
        return map

    def after_map(self, map):
        return map

    def get_validators(self):
        return {
            'require_when_published': self.required_validator,
            'goc_themes_only': self.goc_themes_validator
        }

    @staticmethod
    def object_updated_or_created(context, data_dict):
        """ This is called whenever an object is updated or created. We only
            care about resources and packages; other types are immediately
            returned.
        """
        obj_name = data_dict.get('name')
        logger.info('%s: after_create/update from resource or dataset' % obj_name)
        obj_type, data_dict = self.detect_object_type(data_dict)
        if obj_type == 'resource':
            # set resource type only if it's a resource
            return self.ensure_resource_type(context, data_dict)
        elif obj_type == 'dataset':
            # check keyword case and duplicates
            return self.kw_case_dups(context, data_dict)
        # If any other object type, just return it
        return data_dict

    @staticmethod
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

    @staticmethod
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
        clean_kw = self.lowerise_and_dedup(dataset.get('keywords'))
        clean_sci_kw = self.lowerise_and_dedup(dataset.get('science_keywords'))
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
        # dataset['keywords'] =
        # dataset['science_keywords'] = lowerise_and_dedup(dataset.get('science_keywords'))
        return dataset

    @staticmethod
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
            kw_clean_str = kw_clean.join(',')
            logger.info('Validated keywords: %s' % kw_clean_str)
            return kw_clean_str
        except (TypeError, AttributeError):
            logger.warning('Bad value in keyword string: %s' % kw_str)
            return kw_str

    @staticmethod
    def ensure_resource_type(context, resource):
        # if data_dict.get('package_id'):
        #     # This is a resource
        #     resource = data_dict
        #     logger.info('after_create for resource: %s' % resource.get('id'))
        # else:
        #     logger.info('after_create for dataset or another object')
        #     return data_dict

        res_id = resource.get('id')
        res_name = resource.get('name')
        res_type = resource.get('resource_type')
        logger.info('Resource: %s %s created' % (res_name, res_id))
        # Try to
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

    @staticmethod
    def goc_themes_validator(value, context):
        # Use resource id for GoC themes:
        # https://www.gis-hub.ca/dataset/goc-themes/resource/88f5c7a2-7b25-4ce8-a0c6-081236f5da76
        goc_themes_id = '88f5c7a2-7b25-4ce8-a0c6-081236f5da76'
        logger.info('Check GOC theme keywords: %s' % value)
        result = get_action('datastore_search')(context, {
            'resource_id': goc_themes_id,
            # Default limit is only 100 items
            'limit': 5000})

        goc_themes = []
        records = result.get('records')
        for record in records:
            goc_themes.append(record.get('theme').lower())
        keywords = value.split(',')
        for kw in keywords:
            if not kw.lower().strip() in goc_themes:
                raise Invalid('Not a valid GoC theme: %s' % kw)
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
