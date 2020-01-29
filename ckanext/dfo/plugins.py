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

import logging
logger = logging.getLogger(__name__)


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

    def after_create(self, context, data_dict):
        return data_dict

    def after_update(self, context, data_dict):
        return data_dict

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
    def goc_themes_validator(value, context):
        goc_themes_id = '88f5c7a2-7b25-4ce8-a0c6-081236f5da76'
        logger.info('Check GOC theme keywords: %s' % value)
        logger.info(context)
        result = get_action('datastore_search')(context, {
            'resource_id': goc_themes_id,
            # Default limit is only 100 items
            'limit': 5000})

        goc_themes = []
        records = result.get('records')
        for record in records:
            goc_themes.append(record.get('theme').lower())
        logger.info(goc_themes)
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
