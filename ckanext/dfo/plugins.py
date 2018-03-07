#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit


class DFOPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IFacets)
    p.implements(p.IPackageController)
    p.implements(p.ITemplateHelpers)

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')

    def dataset_facets(self, facets_dict, package_type):
        return facets_dict

    def group_facets(self, facets_dict, organization_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        return facets_dict

    def before_index(self, data_dict):
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

    def before_search(self, search_params):
        return search_params

    def get_helpers(self):
        return {
            'get_thumbnail': get_thumbnail
        }


def get_thumbnail(package_id):
    package = toolkit.get_action('package_show')(data_dict={'id': package_id})

    for resource in package['resources']:
        if resource['name'].lower() == 'thumbnail':
            return resource['url']