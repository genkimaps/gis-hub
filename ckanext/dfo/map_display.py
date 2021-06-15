"""
This module does the following:
1. Exposes an endpoint (via map.connect in plugins.py) for the map display URL for a given resource
2. Check user permissions for the resource
3. If user is authorized, proceed with rendering the map display template
4. map display is done with HTML + OpenLayers. Each map tile request is authorized by ckanext-restricted
"""

import dfo_plugin_settings as settings
from ckan.logic import side_effect_free, get_action
from ckan.lib import base
from ckan.common import request
from ckan.common import c
import ckan.lib.helpers as h
import dfo_plugin_settings
from flask import send_file, jsonify, redirect
from subprocess import check_output, Popen
import traceback
import re

render = base.render

logger = settings.setup_logger(__name__)


class MapDisplayController(base.BaseController):

    # Test URL: https://www.gis-hub.ca/dataset/test05/map_display/c70de8dd-1547-496c-b899-e0424cc1c17a

    def extract_geoserver_layer_name(self, spatial_type, map_preview_link):
        """
        Generates the appropriate layer name from parts of the map preview link.
        For a vector layer, the URL looks like:
        /vector/substrate_obs/obs_hg
        /vector/{dataset_name}/{resource_name}
        And the postgis table name is dataset_name_resource_name

        For a raster layer, the URL looks like:
        /raster/env_layers_nsbssb_bpi_broad
        /raster/{layer_name}
        Where the layer_name corresponds to a Geotiff file such as:
        ~/geoserver217/data_dir/data/hubdata/env_layers_nsbssb_bpi_broad/env_layers_nsbssb_bpi_broad.tif

        :param spatial_type: raster or vector
        :param map_preview_link: the full text created by the mapserver layer loading module, which includes
        comments on status, as well as the actual preview URL.
        :return: layer name
        """

        gs_layer_name = None
        if spatial_type == 'vector':
            patt = r'\/vector\/(.+)\/(.+)$'
            m = re.search(patt, map_preview_link)
            try:
                ds_name = m.group(1)
                res_name = m.group(2)
                gs_layer_name = '%s_%s' % (ds_name, res_name)
            except:
                logger.error('Invalid vector preview data: "%s"' % map_preview_link)

        elif spatial_type == 'raster':
            patt = r'\/raster\/(.+)$'
            m = re.search(patt, map_preview_link)
            try:
                gs_layer_name = m.group(1)
            except:
                logger.error('Invalid raster preview data: "%s"' % map_preview_link)

        else:
            logger.error('Invalid spatial type: %s' % spatial_type)

        logger.info('Internal layer name for %s: %s' % (
            spatial_type, gs_layer_name))
        return gs_layer_name

    def preview_error_page(self, errmsg):
        # If an error message is set, show the error page.
        logger.warning(errmsg)
        return render(
            'map_display/resource_map_nopreview.html',
            extra_vars={'errmsg': errmsg})

    def read_bbox_coords(self, bbox):
        """
        Parse the bbox field to get NSEW values in lat-lon
        :param bbox:
        :return: dict of (N, S, E, W) or None
        (N, S, E, W) are returned as strings for now; convert to float in JS frontend
        """
        ll_coord_patt = '([\-]?\d+\.\d+)'
        n_patt = 'North: %s' % ll_coord_patt
        w_patt = 'West: %s' % ll_coord_patt
        s_patt = 'South: %s' % ll_coord_patt
        e_patt = 'East: %s' % ll_coord_patt
        try:
            m = re.search(n_patt, bbox)
            north = m.group(1)

            m = re.search(e_patt, bbox)
            east = m.group(1)

            m = re.search(s_patt, bbox)
            south = m.group(1)

            m = re.search(w_patt, bbox)
            west = m.group(1)

            extent = {'north': north,
                    'east': east,
                    'south': south,
                    'west': west}
            logger.info('Extent: %s' % extent)
            return extent
        except:
            logger.error(traceback.format_exc())
            logger.error('Pattern: %s, bbox %s' % (
                ll_coord_patt, bbox))
            return {}

    def map_display(self, resource_id):
        """
        Get metadata for this resource, pass to resource map template.
        Don't check for user permissions here, not needed.
        :param resource_id:
        :return:
        """

        """ Make a context object.  Without this, we get an error from Flask:
        RuntimeError: Working outside of request context.
        The context object makes use of the global CKAN object 'c' which contains
        session info including the logged-in user.

        request.params.get is only used for URL parameters after the ?
        e.g. for gis-hub.ca/someurl?animal=dog we would use request.params.get('animal')
        But here package_id, resource_id are part of the URL pattern, passed from map.connect in plugins.py
        
        context = {"user": c.user, "auth_user_obj": c.userobj}
        """

        """
        Need to do a few things before rendering the map. 
        1. Get resource metadata, ensure that it is a spatial resource
        2. Is this a raster or a vector layer? Use a different map template for each.
        3. Get the extent of the layer from the bbox in resource metadata 
        (no need to make an extra API call to Geoserver).  
        The last two steps have until now been handled by the Node.js middleware in mapserver.  
        5. Get the Postgis table name / raster layer name, which can be derived from the 
        "map_preview_link" metadata field: https://maps.gis-hub.ca/vector/substrate_obs/obs_wcvi 
        e.g. resource c70de8dd-1547-496c-b899-e0424cc1c17a in substrate-obs dataset has layer name 'substrate_obs_obs_wcvi'
        6. Render the map template. See resource_read.html and resource_map.js for examples of how data 
        is passed to the Javscript template. 
        
        NOTE: we do NOT need to check if user is authorized for this resource. This is handled downstream, 
        in the nginx auth request for each map tile. 
        """

        logger.info('Map display requested by %s: resource: %s' % (
            c.user, resource_id))

        if not c.user:
            # Not logged in, redirect to login page
            import ckan.plugins.toolkit as toolkit
            logger.warning('Not logged in!')
            return toolkit.redirect_to('user.login')

        # Get resource metadata
        import ckan.model as model
        from flask import abort as flask_abort
        resource = model.Resource.get(resource_id)

        if not resource:
            errmsg = 'Resource %s not found! Are you sure that %s is a resource id, ' \
                     'and not the id of some other object? (package, organization)' % (
                resource_id, resource_id)
            return self.preview_error_page(errmsg)

        resource = resource.as_dict()
        layer_name = resource.get('layer_name')

        spatial_type = resource.get('spatial_type')
        if spatial_type not in ['raster', 'vector']:
            errmsg = 'Map display requested for non-spatial resource: %s' % layer_name
            return self.preview_error_page(errmsg)

        map_preview_link = resource.get('map_preview_link')
        if not map_preview_link:
            errmsg = 'No map preview link: user is not authorized, or map preview was not created.'
            return self.preview_error_page(errmsg)

        # The internal layer name used in Geoserver
        gs_layer_name = self.extract_geoserver_layer_name(
            spatial_type, map_preview_link)
        if not gs_layer_name:
            errmsg = 'Cannot find a valid Geoserver layer name'
            return self.preview_error_page(errmsg)

        # Parse layer extent (lat-lon) from bbox field
        bbox = resource.get('bbox')
        extent = self.read_bbox_coords(bbox)
        if not extent:
            errmsg = 'Cannot read extent from bbox field'
            return self.preview_error_page(errmsg)

        logger.info('Map display requested by %s: %s (resource: %s)' % (
            c.user, layer_name, resource_id))

        data = {
            # 'dataset_id': str(dataset_id),
            'resource_id': str(resource_id),
            'spatial_type': str(spatial_type),
            'layer_name': str(layer_name),
            'gs_layer_name': str(gs_layer_name)
        }
        # Add coords to data dict
        data.update(extent)

        logger.info('Show map display with: %s' % data)
        return render(
            'map_display/resource_map_display.html',
            extra_vars={'data': data})
